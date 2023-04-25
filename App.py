from flask import Flask, render_template,flash,redirect,url_for,request,session,logging,g
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from data import Articles
from functools import wraps

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'unl0ckme'
app.config['MYSQL_DB'] = 'blogverse'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)
app.secret_key = 'gadgetfreak'


Articles = Articles()
@app.route('/')
def home() :
    return render_template('home.html')
@app.route('/about')
def about() :
    return render_template('about.html')
@app.route('/articles')
def articles() :
    cur = mysql.connection.cursor()
    results = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if results > 0:
        return render_template('articles.html',articles = articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html',msg=msg)
    cur.close()
@app.route('/article/<string:id>/')
def article(id) :
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id=%s",[id])
    article = cur.fetchone()
    return render_template('article.html', article=article)
class RegisterForm(Form) :
    name = StringField('Name', [validators.Length(min = 1, max = 50)])
    username = StringField('Username',[validators.length(min = 4, max = 15)])
    email = StringField('Email',[validators.length(min = 6, max = 20)])
    password = PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm', message = 'Passwords do not match')])
    confirm = PasswordField('Confirm Password')
@app.route('/register',methods = ['GET','POST'])
def register() :
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate() :
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)", (name,email,username,password))
        mysql.connection.commit()
        cur.close()
        flash ('You are now registered','success')
        redirect(url_for('register'))
    return render_template('register.html', form = form)
@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST' :
        username = request.form['username']
        password_c = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0 :
            data = cur.fetchone()
            password = data['password']
            if sha256_crypt.verify(password_c,password) :
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else :
                error = 'Wrong Credentials'
                return render_template('login.html',error = error)
            cur.close()
        else :
            error = 'Username not found'
            return render_template('login.html',error = error)


    return render_template('login.html')
def is_logged_in(f):
    @wraps(f)
    def login_check(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else :
            flash('Unauthorized Access','danger')
            return redirect(url_for('login'))        
    return login_check
@app.route('/logout')
@is_logged_in
def logout() :
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))
@app.route('/dashboard')
@is_logged_in
def dashboard() :
    cur = mysql.connection.cursor()
    results = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if results > 0:
        return render_template('dashboard.html',articles = articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html',msg=msg)
    cur.close()
class ArticleForm(Form) :
    title = StringField('title', [validators.Length(min = 1, max = 200)])
    body = TextAreaField('body',[validators.length(min = 100)])
@app.route('/add_article',methods = ['GET','POST'])
@is_logged_in
def add_article() :
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate() :
        title = form.title.data
        body = form.body.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title,body,author) VALUES (%s,%s,%s)",(title,body,session['username']))
        mysql.connection.commit()
        cur.close()
        flash('Article Created','success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)
@app.route('/edit_article/<string:id>', methods = ['GET','POST'])
@is_logged_in
def edit_article(id) :
    
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id= %s",[id])
    article = cur.fetchone()
    form = ArticleForm(request.form)
    form.title.data == article['title']
    form.body.data == article['body']
    if request.method == 'POST' and form.validate() :
        title = request.form['title']
        body = request.form['body']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id= %s",(title,body,id))
        mysql.connection.commit()
        cur.close()
        flash('Article Created','success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form=form)
@app.route('/delete_article/<string:id>',methods=['POST'])
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id=%s",[id])
    mysql.connection.commit()
    cur.close()
    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))
if __name__ == '__main__' :
    
    app.run(debug = True)