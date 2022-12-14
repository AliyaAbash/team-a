from concurrent.futures.thread import _worker
import os
from turtle import title
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, g, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.functions import user 
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import backref, declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from flask_login import login_user, login_required, logout_user, current_user
from forms import LoginForm, RegisterForm, WorksForm
from flask import jsonify
from io import BytesIO
from flask_login import LoginManager


app = Flask(__name__, template_folder='template') 

app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:71336@localhost/py'
app.config['SECRET_KEY'] = 'pysqlflask1111'
db=SQLAlchemy(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return Users.query.filter_by(alternative_id=user_id).first()
@app.before_request
def before_request():
    g.user = current_user

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname= db.Column(db.String(15), unique=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(256), unique=True)
    user_works=db.relationship('Works', backref='users', lazy='dynamic')
    
class Works(db.Model):
    works_id = db.Column(db.Integer, primary_key=True)
    project = db.Column(db.String(50), unique=True)
    skill = db.Column(db.String(50), unique=True)
    users_id = db.Column(db.Integer, db.ForeignKey("users.id"))

class Books(db.Model):
    __tablename__='books'
    books_id = db.Column(db.Integer, primary_key=True)
    bookk = db.Column(db.String(250), unique=True)
    username = db.Column(db.String(15), unique=True)
 
    def __init__(self,bookk,username):
       self.bookk=bookk
       self.username=username     

@app.route("/")
def home_page():
    return render_template("index.html")

@app.route('/login/', methods = ['GET', 'POST'])
def login():

    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate:
        user = Users.query.filter_by(email = form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                flash('You have successfully logged in.', "success")            
                session['logged_in'] = True
                session['id'] = user.id
                session['email'] = user.email 
                session['username'] = user.username
                session['fullname'] = user.fullname
                return redirect(url_for('home_page'))

            else:
                flash('Username or Password Incorrect', "Danger")
                return redirect(url_for('login'))

    return render_template('login.html', form = form)


@app.route('/register/', methods = ['GET', 'POST'])
def register():
    
    form = RegisterForm(request.form) 
    if request.method == 'POST' and form.validate():   
         hashed_password = generate_password_hash(form.password.data, method='sha256')
         new_user = Users( fullname = form.fullname.data, username = form.username.data, email = form.email.data, password = hashed_password)
    
         db.session.add(new_user)    
         db.session.commit()
    
         flash('You have successfully registered', 'success')   
         return redirect(url_for('login'))
    
    else:
        return render_template('register.html', form = form)


@app.route('/logout/')
def logout():  
    session['logged_in'] = False
    return redirect(url_for('home_page'))

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/works/', methods=['POST', 'GET'])
def works():
    form = WorksForm(request.form) 
    if request.method == 'POST' and form.validate():
            work=Works(project=form.project.data, skill=form.skill.data)
            db.session.add(work)
            db.session.commit()
    
            flash('successfully ')   
            return redirect(url_for('home_page'))            
    else:         
        return render_template('works.html', form = form)    


@app.route('/session', methods=['POST', 'GET'])
def session_list():
    return render_template('session_list.html', items=Works.query.all())

@app.route('/upload', methods=['POST', 'GET'])
def upload():
        file = request.files['inputFile']
        username = request.form['username']
        filename = secure_filename(file.filename)
        if file and allowed_file(file.filename):
         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
   
         newFile = Books(bookk=file.filename, username=username)
         db.session.add(newFile)
         db.session.commit()
         flash('File successfully uploaded ' + file.filename + ' to the database!')
         return redirect(url_for('home_page'))
        else:
         flash('Invalid Uplaod only pdf') 
        return render_template('home.html')

@app.route('/very_fine_pdf/')
def library():
    return render_template('/very_fine_pdf.html')  

@app.route('/very_fine_pdf/<file_name>')
def out_file(file_name):
     #?????????????? ???????? ?? ??????????, ?????????????????? ?? ?????????? ???????? file_name
    return send_from_directory('static/uploads', file_name)

@app.route('/crud')
def crud():
   userlist=Users.query.all()
   return render_template("crud.html",userlist=userlist)

@app.route('/insert',methods=['GET','POST'])
def insert(): 
    if request.method=='POST':
        email=request.form.get('email')
        username=request.form.get('username')
        fullname=request.form.get('fullname')
        password=request.form.get('password')
        check_username=Users.query.filter_by(username=username).first()
        check_email=Users.query.filter_by(email=email).first()
        if check_username:
            flash('username already Used ',category='error') 
        elif check_email:
            flash('Email already Used ',category='error') 
        elif len(email)<7:
            flash('_> Email > 7 charac',category='error')
        elif len(username)<3:
            flash('_> Username > 3 charac',category='error')
        else:
            new_user=Users(email=email,username=username,fullname=fullname,password=password,id=None)
            db.session.add(new_user)
            db.session.commit()
            flash('User: "'+username+'" Created',category='success')
            return redirect(url_for("crud"))
    return render_template("insert.html") 

@app.route('/update/<int:id>',methods=['GET','POST'])
def update(id):
    updd= Users.query.get_or_404(id)
    if request.method=='POST':
        email=request.form.get('email')
        username=request.form.get('username')      
        if updd.email==request.form.get('email'):
            flash('Email already Used ',category='error') 
        elif len(email)<7:
            flash('_> Email > 47charac',category='error')
        elif len(username)<3:
            flash('_> Username > 3 charac',category='error')
        else:
            updd.email=request.form.get('email')
            updd.username=request.form.get('username')
            db.session.commit()
            flash('User: "'+updd.username+'" Updated',category='success')
            ##login_user(user,remember=True)
            ## userResult=db.session.query(User)
            return redirect(url_for("crud"))
    return render_template("update.html",user=updd) 

@app.route('/delete/<int:id>',methods=['GET','POST'])
def delete_user(id):
        de = Users.query.get_or_404(id)
        username = de.username
        if de:
            db.session.delete(de)
            db.session.commit()
            flash('User: "'+username+'" deleted',category='warning')
            return redirect(url_for("crud"))


if __name__ == '__main__':
    app.run(port=8000,debug=True)








