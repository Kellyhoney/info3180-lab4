from werkzeug.security import check_password_hash
import os
from app import app, db, login_manager
from flask import render_template, request, redirect, url_for, flash, session, abort, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from app.models import UserProfile
from app.forms import LoginForm, UploadForm

###
# Routing for your application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')

@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html', name="Mary Jane")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = UserProfile.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for("upload"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash("File uploaded successfully.", "success")
        return redirect(url_for("files"))
    return render_template("upload.html", form=form)

def get_uploaded_images():
    """
    Return a list of image filenames (jpg, jpeg, png) from UPLOAD_FOLDER.
    Skips .gitkeep or non-image extensions.
    """
    upload_folder = app.config['UPLOAD_FOLDER']
    images = []
    for f in os.listdir(upload_folder):
        full_path = os.path.join(upload_folder, f)
        if os.path.isfile(full_path) and f.lower().endswith(('.jpg', '.jpeg', '.png')):
            images.append(f)
    return images

@app.route('/files')
@login_required
def files():
    images = get_uploaded_images()
    return render_template('files.html', images=images)

@app.route('/upload/<filename>')
@login_required
def get_image(filename):
    """
    Serve an uploaded file from UPLOAD_FOLDER.
    Example URL: /upload/f-635b8680.jpg
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(UserProfile).filter_by(id=user_id)).scalar()

# Flash errors from the form if validation fails
def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in the {getattr(form, field).label.text} field - {error}", "danger")

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)

@app.after_request
def add_header(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
