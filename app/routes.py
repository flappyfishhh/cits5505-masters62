import os
import csv
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, send_from_directory, jsonify
)
from flask_login import (
    current_user, login_user, logout_user, login_required
)
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from app import db
from app.models import User, FileUpload, Upload, FileShare
from app.forms import (
    RegistrationForm, LoginForm, UploadForm,
    ForgotPasswordForm, ResetPasswordForm,
    UpdateEmailForm, ChangePasswordForm, UpdateFileForm
)
import pandas as pd
import plotly.graph_objs as go
from flask import session 

# ================================
# Upload Blueprint
# ================================
main = Blueprint('main', __name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')

# Create the uploads directory if it doesn't exist
def ensure_upload_folder():
    folder = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder

# ================================
# Intro Page (Public Landing)
# ================================
@main.route('/')
def intro():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('intro.html')


# ================================
# User Registration
# ================================
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

# ================================
# User Login
# ================================
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

# ================================
# Dashboard - central hub for users to access key features
# ================================
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

# ================================
# User Logout
# ================================
@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.intro'))

# ================================
# Password Reset (Step 1)
# ================================
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

# ================================
# Password Reset (Step 2)
# ================================
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



# ================================
# Index - Shows files by access level
# ================================
@main.route('/index')
@login_required
def index():
    # Own files (all visibilities)
    own_files = FileUpload.query.filter_by(user_id=current_user.id).order_by(FileUpload.uploaded_at.desc()).all()
    
    # Public files (visible to all users)
    public_files = FileUpload.query.filter_by(visibility='public').order_by(FileUpload.uploaded_at.desc()).all()
    
    # Shared files (shared explicitly with current user)
    shared_files = FileUpload.query.join(FileShare, FileShare.file_id == FileUpload.id)\
        .filter(FileShare.user_id == current_user.id, FileUpload.visibility == 'shared')\
        .order_by(FileUpload.uploaded_at.desc()).all()

    return render_template('index.html', own_files=own_files, public_files=public_files, shared_files=shared_files)

# ================================
# View uploaded file's data
# ================================
@main.route('/files/<int:file_id>')
@login_required
def view_file(file_id):
    f = FileUpload.query.filter_by(id=file_id).first_or_404()

    # ===== Permission check =====
    if f.visibility == 'private' and f.user_id != current_user.id:
        flash('Private file, you do not have permission')
        return redirect(url_for('main.index'))
    elif f.visibility == 'shared':
        if current_user != f.user and current_user not in f.share_with:
            flash('Shared file, you are not authorized')
            return redirect(url_for('main.index'))

    # ===== Load file data =====
    uploads = Upload.query.filter_by(file_id=file_id).order_by(Upload.row_number).all()
    headers = list(uploads[0].data.keys()) if uploads else []
    rows = [list(u.data.values()) for u in uploads] if uploads else []

    return render_template('view_file.html', file=f, headers=headers, rows=rows, owner=User.query.get(f.user_id), shared_users=f.share_with if f.visibility == 'shared' else [])

# ================================
# Delete uploaded file (only by owner)
# ================================
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

# ================================
# Serve uploaded file for download
# ================================
@main.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(os.path.join(current_app.root_path, UPLOAD_FOLDER), filename, as_attachment=True)

# ================================
# File Upload
# ================================
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

        # Save file upload metadata
        record = FileUpload(
            user_id=current_user.id,
            filename=orig,
            filepath=path,
            city=form.city.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            visibility='private'
        )
        db.session.add(record)
        db.session.flush()

        # Save CSV row-by-row
        with open(os.path.join(current_app.root_path, path), newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for idx, row in enumerate(reader, start=1):
                db.session.add(Upload(file_id=record.id, row_number=idx, data=row))

        db.session.commit()
        flash(f'File "{orig}" uploaded with {idx} rows.')
        return redirect(url_for('main.index'))
    return render_template('upload.html', form=form)

# ================================
# Update file visibility/sharing
# ================================
@main.route('/files/<int:file_id>/update', methods=['GET', 'POST'])
@login_required
def update_file(file_id):
    file = FileUpload.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    form = UpdateFileForm(obj=file)
    current_shared_emails = [user.email for user in file.share_with] if file.visibility != 'public' else []

    if request.method == 'POST':
        if form.validate_on_submit():
            file.visibility = form.visibility.data

            if form.visibility.data == 'shared':
                if isinstance(form.share_with.data, str):
                    submitted_emails = [e.strip() for e in form.share_with.data.split(',') if e.strip() and e.strip() != current_user.email]
                elif isinstance(form.share_with.data, list):
                    submitted_emails = [e.strip() for e in form.share_with.data if e.strip() and e.strip() != current_user.email]
                else:
                    submitted_emails = []

                all_emails = list(set(current_shared_emails + submitted_emails))

                FileShare.query.filter_by(file_id=file.id).delete()
                for email in all_emails:
                    user = User.query.filter_by(email=email).first()
                    if user and user.id != current_user.id:
                        db.session.add(FileShare(file_id=file.id, user_id=user.id))

            db.session.commit()

            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': True, 'message': 'Permissions updated successfully', 'shared_emails': all_emails if form.visibility.data == 'shared' else []})

            flash('Permissions updated successfully', 'success')
            return redirect(url_for('main.index', file_id=file.id))

        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'message': 'Validation failed', 'errors': form.errors}), 400

    form.share_with.data = ', '.join(current_shared_emails) if file.visibility != 'public' else ''
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'shared_emails': current_shared_emails, 'visibility': file.visibility})

    return render_template('update_file.html', form=form, file=file, current_shared_emails=current_shared_emails)

# ================================
# Remove a specific user from file sharing list
# ================================
@main.route('/files/<int:file_id>/remove_share', methods=['GET'])
@login_required
def remove_share(file_id):
    email = request.args.get('email')
    file = FileUpload.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    user = User.query.filter_by(email=email).first()
    if user:
        share_record = FileShare.query.filter_by(file_id=file.id, user_id=user.id).first()
        if share_record:
            db.session.delete(share_record)
            db.session.commit()
            flash(f'File no longer shared with {email}.')
        else:
            flash(f'{email} is not on the share list.')
    return redirect(url_for('main.update_file', file_id=file.id))

# ================================
# User profile: change email or password
# ================================
@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    email_form = UpdateEmailForm(obj=current_user)
    pw_form = ChangePasswordForm()

    # Update email if submitted and valid
    if email_form.submit_email.data and email_form.validate_on_submit():
        current_user.email = email_form.email.data
        db.session.commit()
        flash('Email updated successfully!')
        return redirect(url_for('main.profile'))

    # Update password using either current password or security answer
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


# ================================
# Solar Data Upload (NEW)
# ================================
@main.route('/solar_upload', methods=['GET', 'POST'])
@login_required
def solar_upload():
    ensure_upload_folder()
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)
            file.save(save_path)
            flash('Solar data file uploaded successfully!', 'success')
            # Store filename in session or db if needed later
            session['solar_file'] = filename
            return redirect(url_for('main.solar_visualize'))
        else:
            flash('Invalid file type. Please upload a CSV file.', 'danger')
    return render_template('solar_upload.html')  # you need to rename your index.html as solar_upload.html


# ================================
# Solar Data Visualization
# ================================
@main.route('/solar_visualize', methods=['GET', 'POST'])
@login_required
def solar_visualize():
    filename = session.get('solar_file')
    if not filename:
        flash('No solar data file uploaded.', 'danger')
        return redirect(url_for('main.solar_upload'))

    filepath = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        flash('Solar data file not found.', 'danger')
        return redirect(url_for('main.solar_upload'))

    df = pd.read_csv(filepath)
    columns = df.columns.tolist()
    chart = None

    if request.method == 'POST':
        x_axis = request.form['x_axis']
        y_axis = request.form['y_axis']
        chart_type = request.form['chart_type']
        data = df[[x_axis, y_axis]].dropna().to_dict(orient='list')
        chart = {'x': data[x_axis], 'y': data[y_axis], 'type': chart_type}

    return render_template('visualize.html', columns=columns, chart=chart)


# ================================
# Solar Data Analysis (Trend + Anomalies)
# ================================
@main.route('/solar_analysis')
@login_required
def solar_analysis():
    filename = session.get('solar_file')
    if not filename:
        flash('No solar data file uploaded.', 'danger')
        return redirect(url_for('main.solar_upload'))

    filepath = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        flash('Solar data file not found.', 'danger')
        return redirect(url_for('main.solar_upload'))

    df = pd.read_csv(filepath)
    trend_plot = None

    if {'Year', 'Month', 'Day', 'Daily global solar exposure (MJ/m*m)'}.issubset(df.columns):
        df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
        monthly_avg = df.groupby(df['Date'].dt.to_period('M'))['Daily global solar exposure (MJ/m*m)'].mean()
        monthly_avg.index = monthly_avg.index.to_timestamp()

        # Seasonal Patterns
        monthly_seasonal = df.groupby(df['Month'])['Daily global solar exposure (MJ/m*m)'].mean().round(2).to_dict()

        # Anomaly Detection
        Q1 = monthly_avg.quantile(0.25)
        Q3 = monthly_avg.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        anomalies = monthly_avg[(monthly_avg < lower_bound) | (monthly_avg > upper_bound)].round(2).to_dict()

        # Trend Plot
        trend_fig = go.Figure()
        trend_fig.add_trace(go.Scatter(
            x=monthly_avg.index,
            y=monthly_avg.values,
            mode='lines+markers',
            name='Monthly Avg Solar Exposure'
        ))
        trend_fig.update_layout(
            title='Monthly Average Solar Exposure Over Time',
            xaxis_title='Date',
            yaxis_title='Daily Global Solar Exposure (MJ/m²)',
            height=500
        )
        trend_plot = trend_fig.to_html(full_html=False)

        return render_template('analysis.html', seasonal_patterns=monthly_seasonal, anomalies=anomalies, trend_plot=trend_plot)

    return render_template('analysis.html', seasonal_patterns=None, anomalies=None, trend_plot=None)

@main.route('/files/<int:file_id>/visualize', methods=['GET', 'POST'])
@login_required
def visualize_file(file_id):
    f = FileUpload.query.filter_by(id=file_id).first_or_404()

    # Permission check
    if f.visibility == 'private' and f.user_id != current_user.id:
        flash('Private file, you do not have permission')
        return redirect(url_for('main.index'))
    elif f.visibility == 'shared':
        if current_user != f.user and current_user not in f.share_with:
            flash('Shared file, you are not authorized')
            return redirect(url_for('main.index'))

    # Load file data
    filepath = os.path.join(current_app.root_path, f.filepath)
    if not os.path.exists(filepath):
        flash('File not found.', 'danger')
        return redirect(url_for('main.index'))

    df = pd.read_csv(filepath)
    columns = df.columns.tolist()
    chart = None

    if request.method == 'POST':
        x_axis = request.form['x_axis']
        y_axis = request.form['y_axis']
        chart_type = request.form['chart_type']
        data = df[[x_axis, y_axis]].dropna().to_dict(orient='list')
        chart = {'x': data[x_axis], 'y': data[y_axis], 'type': chart_type}

    return render_template('visualize.html', columns=columns, chart=chart)