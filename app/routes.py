import os
import csv
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, send_from_directory
)
from flask_login import (
    current_user, login_user, logout_user, login_required
)
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from app import db
from app.models import User, FileUpload, Upload
from app.forms import (
    RegistrationForm, LoginForm, UploadForm,
    ForgotPasswordForm, ResetPasswordForm,
    UpdateEmailForm, ChangePasswordForm
)

main = Blueprint('main', __name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')

def ensure_upload_folder():
    folder = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


@main.route('/')
def intro():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('intro.html')

@main.route('/dashboard')
@login_required
def dashboard():
    # Example: Fetch recent uploads and other relevant data
    recent_uploads = (
        FileUpload.query
        .filter_by(user_id=current_user.id)
        .order_by(FileUpload.uploaded_at.desc())
        .limit(5)
        .all()
    )
    return render_template('dashboard.html', recent_uploads=recent_uploads)

@main.route('/index')
@login_required
def index():
    files = (
        FileUpload.query
        .filter_by(user_id=current_user.id)
        .order_by(FileUpload.uploaded_at.desc())
        .all()
    )
    return render_template('index.html', files=files)



@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        user.set_security_answer(form.security_answer.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
    return render_template('login.html', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.intro'))

@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('No account found with that email.')
        else:
            return redirect(url_for('main.reset_password', user_id=user.id))
    return render_template('forgot_password.html', form=form)

@main.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if not user.check_security_answer(form.security_answer.data):
            flash('Security answer is incorrect.')
        else:
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been reset. Please log in.')
            return redirect(url_for('main.login'))
    return render_template('reset_password.html', form=form)


@main.route('/files/<int:file_id>')
@login_required
def view_file(file_id):
    f = FileUpload.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    uploads = (
        Upload.query
        .filter_by(file_id=file_id)
        .order_by(Upload.row_number)
        .all()
    )
    if uploads:
        headers = list(uploads[0].data.keys())
        rows = [list(u.data.values()) for u in uploads]
    else:
        headers, rows = [], []
    return render_template('view_file.html', file=f, headers=headers, rows=rows)

@main.route('/files/<int:file_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_file(file_id):
    f = FileUpload.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    try:
        os.remove(os.path.join(current_app.root_path, f.filepath))
    except OSError:
        pass
    db.session.delete(f)
    db.session.commit()
    flash(f'File "{f.filename}" has been deleted.')
    return redirect(url_for('main.index'))

@main.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(
        os.path.join(current_app.root_path, UPLOAD_FOLDER),
        filename, as_attachment=True
    )

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        ensure_upload_folder()
        f = form.csv_file.data
        orig = secure_filename(f.filename)
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        saved = f"{current_user.id}_{ts}_{orig}"
        path = os.path.join(UPLOAD_FOLDER, saved)
        f.save(os.path.join(current_app.root_path, path))

        record = FileUpload(
            user_id=current_user.id,
            filename=orig,
            filepath=path,
            city=form.city.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data
        )
        db.session.add(record)
        db.session.flush()

        full = os.path.join(current_app.root_path, path)
        with open(full, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for idx, row in enumerate(reader, start=1):
                upload_row = Upload(
                    file_id=record.id,
                    row_number=idx,
                    data=row
                )
                db.session.add(upload_row)

        db.session.commit()
        flash(f'File "{orig}" uploaded for {form.city.data} ({form.latitude.data}, {form.longitude.data}) with {idx} rows.')
        return redirect(url_for('main.index'))
    return render_template('upload.html', form=form)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    email_form = UpdateEmailForm(obj=current_user)
    pw_form = ChangePasswordForm()
    # Update email
    if email_form.submit_email.data and email_form.validate_on_submit():
        current_user.email = email_form.email.data
        db.session.commit()
        flash('Email updated successfully!')
        return redirect(url_for('main.profile'))
    # Change password by current password or security answer
    if pw_form.submit_password.data and pw_form.validate_on_submit():
        ok = False
        if pw_form.current_password.data and current_user.check_password(pw_form.current_password.data):
            ok = True
        elif pw_form.security_answer.data and current_user.check_security_answer(pw_form.security_answer.data):
            ok = True
        if not ok:
            flash('Current password or security answer is incorrect.')
        else:
            current_user.set_password(pw_form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!')
        return redirect(url_for('main.profile'))
    return render_template('profile.html', email_form=email_form, pw_form=pw_form)
