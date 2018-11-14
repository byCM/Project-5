from flask import (Flask, g, render_template, flash, redirect, url_for, abort)
from flask.ext.bcrypt import check_password_hash
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user

import forms 
import models

DEBUG = True
PORT = 8000
HOST = '0.0.0.0'

app = Flask(__name__)
app.secret_key = 'sasdhfkjsdfkjshdkjf.sdf.sdf.sdf'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None    


@app.before_request
def before_request():
    """connect to the database before each requeest."""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user
    
    
@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response


@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("You are now registered!", "success")
        models.User.create_user(
            username=form.username.data,
            email=form.username.data,
            password=form.password.data,
        )
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password doesn't match!", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("You've been logged in!", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email or password doesn't match!", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You've been logged out", "success")
    return redirect(url_for('index'))


@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.create_entry(
            title=form.title.data,
            date=form.date.data,
            time_spent=form.time_spent.data,
            learning=form.learning.data,
            resources=form.resources.data,
            user=g.user._get_current_object(),
        )
        flash("New journal entry has been added!", "success")
        return redirect(url_for('index'))
    return render_template("post.html", form=form)
     

@app.route('/')
@login_required
def index():  
    stream = models.Post.select().limit(100)
    return render_template('entries.html', stream=stream, total=stream.count())
  

@app.route('/entries')
@app.route('/entries/<username>')
@login_required
def stream(username=None):
    template = 'entries.html'
    if username and username != current_user.username:
        user = models.User.select().where(models.User.username**username).get()
        stream = user.posts.limit(100)
    else:
        stream = current_user.get_stream()
        user = current_user
    if username:
        template = 'user_stream.html'
    return render_template(template, stream=stream, user=user)
  

@app.route('/entries/edit/<postid>', methods=['GET', 'POST'])
@login_required
def edit(postid=None):
    entry = models.Post.get(models.Post.id == postid)
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.update(
            title=form.title.data.strip(),
            date=form.date.data,
            time_spent=form.time_spent.data,
            learning=form.learning.data.strip(),
            resources=form.resources.data.strip(),
            ).where(models.Post.id == postid).execute()
        flash("Entry saved!", 'success')
        return redirect(url_for('index'))
    form.title.data = entry.title
    form.date.data = entry.date
    form.time_spent.data = entry.time_spent
    form.learning.data = entry.learning
    form.resources.data = entry.resources
    return render_template('edit.html', form=form)
  

@app.route('/entries/delete/<postid>', methods=['GET', 'POST'])
@login_required
def delete(postid=None):
    models.Post.get(models.Post.id == postid).delete_instance()
    flash("Entry has been deleted", "success")
    return redirect(url_for('index'))


@app.route('/detail/<postid>', methods=['GET', 'POST'])
@login_required
def detail(postid=None):
    try:
        post = models.Post.select().where(models.Post.id == postid).get()
    except models.DoesNotExist:
        abort(404)
    return render_template('detail.html', post=post)
    

@app.errorhandler(404)
def error_page(error):
    return render_template('404.html', error=error), 404


if __name__ == '__main__':
    models.initialize()
    try:       
        models.User.create_user(
            username='buggy',
            email='buggy@gmail.com',
            password='password',
            admin=True
        )
    except ValueError:
        pass
    
    app.run(debug=DEBUG, host=HOST, port=PORT, use_reloader=False)
