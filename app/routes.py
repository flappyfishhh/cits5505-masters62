import os
import csv
from datetime import datetime, timezone, timedelta
now = datetime.now(timezone.utc)
from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, current_app, send_from_directory, jsonify, abort
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


# ================================
# # Solar Panel Suitability Classification Helper
# ================================

def suitability_grade(avg_exposure):
    """
    Classifies solar suitability based on average daily solar exposure.
    Parameters:
        avg_exposure (float): Average daily solar exposure in MJ/m².
    Returns:
        tuple: (grade, message)
    """
    if avg_exposure < 3.99:
        return (
            "Not Suitable",
            f"Average Solar Exposure value is less than 3.99 MJ/m²/day. Current value: {avg_exposure:.2f} MJ/m²/day."
        )
    elif avg_exposure <= 4.0:
        return (
            "Off-grid",
            f"Average Solar Exposure value is between 4 and 5 MJ/m²/day. Current value: {avg_exposure:.2f} MJ/m²/day."
        )
    elif avg_exposure < 20.0:
        return (
            "Grid-tied Residential",
            f"Average Solar Exposure value is between 4.01 and less than 20.0 MJ/m²/day. Current value: {avg_exposure:.2f} MJ/m²/day."
        )
    else:
        return (
            "High Performance Zone",
            f"Average Solar Exposure value is greater than or equal to 20.0 MJ/m²/day. Current value: {avg_exposure:.2f} MJ/m²/day."
        )

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
        user.last_login_time = datetime.now(timezone.utc)
        db.session.commit()
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
    now = datetime.now(timezone(timedelta(hours=8)))
    if current_user.last_login_time:
        last_login = current_user.last_login_time + timedelta(hours=8)
        formatted_last_login = last_login.strftime('%Y-%m-%d %H:%M:%S')
    else:
        formatted_last_login = "-"
    return render_template('dashboard.html', recent_uploads=recent_uploads, now=now, last_login=formatted_last_login)

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
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
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

    owner = db.session.get(User, f.user_id)
    return render_template('view_file.html', file=f, headers=headers, rows=rows, owner=owner, shared_users=f.share_with if f.visibility == 'shared' else [])

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
        perth_tz = timezone(timedelta(hours=8))
        ts = datetime.now(perth_tz).strftime('%Y%m%d%H%M%S')  
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

    form.share_with.data = '' if file.visibility != 'public' else ''
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
# Rendering visualisation page
# ================================
@main.route('/visualisation')
@login_required
def visualisation():
    private_files = (
        FileUpload.query
        .filter_by(user_id=current_user.id)
        .order_by(FileUpload.uploaded_at.desc())
        .all()
    )
    current_app.logger.info(f"Private files: {private_files}")

    shared_files = (
        FileUpload.query
        .join(FileShare, FileShare.file_id == FileUpload.id)
        .filter(FileShare.user_id == current_user.id, FileUpload.visibility == 'shared')
        .order_by(FileUpload.uploaded_at.desc())
        .all()
    )
    current_app.logger.info(f"Shared files: {shared_files}")

    public_files = (
        FileUpload.query
        .filter_by(visibility='public')
        .order_by(FileUpload.uploaded_at.desc())
        .all()
    )
    current_app.logger.info(f"Public files: {public_files}")

    # Combine all files and remove duplicates based on file ID
    all_files = private_files + shared_files + public_files
    unique_files = {file.id: file for file in all_files}.values()  # Use a dictionary to ensure uniqueness by file ID

    return render_template('visualisation.html', uploaded_files=unique_files)

# ================================
# Get file data for visualisation
# ================================
@main.route('/get-file-data/<int:file_id>', methods=['GET'])
@login_required
def get_file_data(file_id):
    current_app.logger.info(f"Fetching file with ID {file_id} for user {current_user.id}")

    # Query the file metadata
    file_record = (
        FileUpload.query
        .filter(
            (FileUpload.id == file_id) & (
                (FileUpload.user_id == current_user.id) |
                (FileUpload.visibility == 'public') |
                (
                    (FileUpload.visibility == 'shared') &
                    (FileShare.user_id == current_user.id)
                )
            )
        )
        .join(FileShare, isouter=True)
        .first()
    )

    if not file_record:
        current_app.logger.error(f"File with ID {file_id} not found or access denied for user {current_user.id}")
        abort(404, description="File not found or access denied.")

    current_app.logger.info(f"File metadata: {file_record}")

    # Query the rows of data
    rows = Upload.query.filter_by(file_id=file_id).order_by(Upload.row_number).all()

    if not rows:
        current_app.logger.error(f"No data found for file ID {file_id}")
        abort(404, description="No data found for the selected file.")

    current_app.logger.info(f"Number of rows found: {len(rows)}")

    # Prepare the data
    data = []
    for row in rows:
        date = f"{row.data['Year']}-{row.data['Month'].zfill(2)}-{row.data['Day'].zfill(2)}"
        data.append({
            "date": date,
            "solar_exposure": float(row.data['Daily global solar exposure (MJ/m*m)']) if row.data.get('Daily global solar exposure (MJ/m*m)') else None
        })

    current_app.logger.info(f"Prepared data: {data}")

    return jsonify({"filename": file_record.filename, "data": data})
	
# ================================
# Solar Data Analysis (Trend + Anomalies)
# ================================
@main.route('/solar_analysis/<int:file_id>', methods=['GET'])
@login_required
def solar_analysis(file_id):
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go

    file = FileUpload.query.get_or_404(file_id)

    if file.visibility == 'private' and file.user_id != current_user.id:
        abort(403)

    if file.visibility == 'shared' and (current_user != file.user and current_user not in file.share_with):
        abort(403)

    if file.visibility == 'public':
        pass

    uploads = Upload.query.filter_by(file_id=file.id).order_by(Upload.row_number).all()
    if not uploads:
        flash('No data available for analysis.', 'warning')
        return redirect(url_for('main.dashboard'))

    df = pd.DataFrame([row.data for row in uploads])
    df.columns = [col.strip() for col in df.columns]

    required_cols = {'Year', 'Month', 'Day', 'Daily global solar exposure (MJ/m*m)'}
    if not required_cols.issubset(df.columns):
        flash('Dataset must contain Year, Month, Day, and Daily global solar exposure (MJ/m*m)', 'danger')
        return redirect(url_for('main.dashboard'))

    df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']], errors='coerce')
    df['Daily global solar exposure (MJ/m*m)'] = pd.to_numeric(
        df['Daily global solar exposure (MJ/m*m)'], errors='coerce'
    )
    df.dropna(subset=['Date', 'Daily global solar exposure (MJ/m*m)'], inplace=True)

    # Apply date filter if provided
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if start_date:
        df = df[df["Date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["Date"] <= pd.to_datetime(end_date)]

    monthly_avg = df.groupby(df['Date'].dt.to_period('M'))['Daily global solar exposure (MJ/m*m)'].mean()
    monthly_avg.index = monthly_avg.index.to_timestamp()

    seasonal_patterns = df.groupby(df['Date'].dt.month_name())['Daily global solar exposure (MJ/m*m)'].mean().round(2).to_dict()

    Q1 = monthly_avg.quantile(0.25)
    Q3 = monthly_avg.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    anomalies = monthly_avg[(monthly_avg < lower_bound) | (monthly_avg > upper_bound)].round(2).to_dict()

    overall_avg = df['Daily global solar exposure (MJ/m*m)'].mean()
    grade, suitability_message = suitability_grade(overall_avg)

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

    return render_template('analysis.html',
                           seasonal_patterns=seasonal_patterns,
                           anomalies=anomalies,
                           trend_plot=trend_plot,
                           suitability_message=suitability_message,
                           suitability_grade=grade,
                           file_id=file_id)

# ================================
# Bushfire Alert Analysis
# ================================
@main.route('/bushfire_alert/<int:file_id>')
@login_required
def bushfire_alert(file_id):
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    from sklearn.linear_model import LogisticRegression, LinearRegression

    file = FileUpload.query.get_or_404(file_id)
    
    if file.visibility == 'private' and file.user_id != current_user.id:
        abort(403)

    if file.visibility == 'shared' and (current_user != file.user and current_user not in file.share_with):
        abort(403)

    if file.visibility == 'public':
        pass

    uploads = Upload.query.filter_by(file_id=file.id).order_by(Upload.row_number).all()
    if not uploads:
        flash('No data available to analyze bushfire alerts.', 'warning')
        return redirect(url_for('main.index'))

    df = pd.DataFrame([row.data for row in uploads])
    df.columns = [col.strip() for col in df.columns]

    required_cols = {'Year', 'Month', 'Day', 'Daily global solar exposure (MJ/m*m)'}
    if not required_cols.issubset(df.columns):
        flash('Dataset must contain Year, Month, Day, and Daily global solar exposure (MJ/m*m)', 'danger')
        return redirect(url_for('main.index'))

    df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']], errors='coerce')
    df['Exposure'] = pd.to_numeric(df['Daily global solar exposure (MJ/m*m)'], errors='coerce')
    df = df.dropna(subset=['Date', 'Exposure']).sort_values(by='Date')
    df['Month'] = df['Date'].dt.month
    df['Year'] = df['Date'].dt.year

    #  Bushfire streak detection
    df['HighRisk'] = ((df['Exposure'] >= 30) & (df['Month'].isin([11, 12, 1, 2]))).astype(int)
    df['StreakGroup'] = (df['HighRisk'] != df['HighRisk'].shift()).cumsum()

    high_risk_df = df[df['HighRisk'] == 1]
    streaks = high_risk_df.groupby('StreakGroup').agg({
        'Date': ['min', 'max', 'count']
    }).reset_index()
    streaks.columns = ['StreakID', 'StartDate', 'EndDate', 'Days']
    alerts = streaks[streaks['Days'] >= 3].sort_values(by='StartDate', ascending=False)
    total_alerts = len(alerts)

    #  Pagination for alert streaks
    page = int(request.args.get('page', 1))
    per_page = 10
    total_pages = (len(alerts) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    alerts_paginated = alerts.iloc[start:end]

    #  Forecast: Monthly risk using LogisticRegression
    monthly = df.groupby(df['Date'].dt.to_period('M')).agg({
        'Exposure': 'mean',
        'HighRisk': 'max'
    }).reset_index()
    monthly['Date'] = monthly['Date'].dt.to_timestamp()
    monthly['TimeIndex'] = np.arange(len(monthly))

    X = monthly[['TimeIndex']]
    y = monthly['HighRisk']

    if y.nunique() < 2:
        forecast_plot = "<p class='text-sm text-red-600'> Forecast unavailable: Not enough variation in bushfire data (only one class detected).</p>"
    else:
        model = LogisticRegression()
        model.fit(X, y)

        future_index = np.arange(X['TimeIndex'].max() + 1, X['TimeIndex'].max() + 7).reshape(-1, 1)
        future_index_df = pd.DataFrame(future_index, columns=['TimeIndex'])
        future_probs = model.predict_proba(future_index_df)[:, 1]
        future_dates = pd.date_range(monthly['Date'].max() + pd.offsets.MonthBegin(1), periods=6, freq='MS')
        future_df = pd.DataFrame({'Date': future_dates, 'PredictedRisk': future_probs})

        #  Color coding
        def risk_color(prob):
            if prob >= 0.75:
                return 'red'
            elif prob >= 0.5:
                return 'orange'
            else:
                return 'green'

        future_df['Color'] = future_df['PredictedRisk'].apply(risk_color)

        #  Forecast Plot
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=future_df['Date'].dt.strftime('%b %Y'),
            y=future_df['PredictedRisk'],
            marker_color=future_df['Color'],
            text=(future_df['PredictedRisk'] * 100).round(1).astype(str) + '%',
            textposition='outside',
            name='Predicted Risk'
        ))

        fig.add_trace(go.Scatter(
            x=future_df['Date'].dt.strftime('%b %Y'),
            y=[0.75] * len(future_df),
            mode='lines',
            line=dict(dash='dash', color='black'),
            name='High Risk Threshold (75%)'
        ))

        fig.update_layout(
            title="6-Month Bushfire Risk Forecast",
            xaxis_title="Month",
            yaxis_title="Risk Probability",
            yaxis=dict(range=[0, 1]),
            height=500
        )

        forecast_plot = fig.to_html(full_html=False)

    #  7-day prediction using LinearRegression
    df_sorted = df.reset_index(drop=True)
    df_sorted['DayIndex'] = np.arange(len(df_sorted))
    X_lin = df_sorted[['DayIndex']]
    y_lin = df_sorted['Exposure']
    lin_model = LinearRegression()
    lin_model.fit(X_lin, y_lin)

    future_index = np.arange(X_lin['DayIndex'].max() + 1, X_lin['DayIndex'].max() + 8).reshape(-1, 1)
    future_index_df = pd.DataFrame(future_index, columns=['DayIndex'])  # fixes warning
    future_dates = pd.date_range(start=df_sorted['Date'].max() + pd.Timedelta(days=1), periods=7)
    predicted_exposure = lin_model.predict(future_index_df)

    seven_day_df = pd.DataFrame({
        'Date': future_dates,
        'PredictedExposure': predicted_exposure
    })
    seven_day_df['Month'] = seven_day_df['Date'].dt.month
    seven_day_df['Risk'] = (seven_day_df['PredictedExposure'] >= 30) & (seven_day_df['Month'].isin([11, 12, 1, 2]))
    alert_days = seven_day_df[seven_day_df['Risk'] == True][['Date', 'PredictedExposure']]


   

    return render_template(
        'bushfire_alert.html',
        alerts=alerts_paginated,
        total_alerts=total_alerts,
        current_page=page,
        total_pages=total_pages,
        file_id=file_id,
        forecast_plot=forecast_plot,
        seven_day_alerts=alert_days
    )

# ================================
# BushfireAlert_PDF Export
# ================================
from flask import render_template, make_response, abort, flash, redirect, url_for
from flask_login import login_required, current_user
import pandas as pd
from datetime import datetime
import io
from xhtml2pdf import pisa

@main.route('/export_bushfire_pdf/<int:file_id>')
@login_required
def export_bushfire_pdf(file_id):
    file = FileUpload.query.get_or_404(file_id)

    if file.user_id != current_user.id and current_user not in file.share_with:
        abort(403)

    uploads = Upload.query.filter_by(file_id=file.id).order_by(Upload.row_number).all()
    if not uploads:
        flash('No data available to export.', 'warning')
        return redirect(url_for('main.index'))

    df = pd.DataFrame([row.data for row in uploads])
    df.columns = [col.strip() for col in df.columns]
    df['Date'] = pd.to_datetime(df[['Year', 'Month', 'Day']], errors='coerce')
    df['Exposure'] = pd.to_numeric(df['Daily global solar exposure (MJ/m*m)'], errors='coerce')
    df.dropna(subset=['Date', 'Exposure'], inplace=True)
    df.sort_values(by='Date', inplace=True)
    df['Month'] = df['Date'].dt.month
    df['HighRisk'] = ((df['Exposure'] >= 30) & (df['Month'].isin([11, 12, 1, 2]))).astype(int)
    df['StreakGroup'] = (df['HighRisk'] != df['HighRisk'].shift()).cumsum()

    high_risk_df = df[df['HighRisk'] == 1]
    streaks = high_risk_df.groupby('StreakGroup').agg({
        'Date': ['min', 'max', 'count']
    }).reset_index()
    streaks.columns = ['StreakID', 'StartDate', 'EndDate', 'Days']
    alerts = streaks[streaks['Days'] >= 3].sort_values(by='StartDate', ascending=False)

    # 7-Day forecast summary
    today = df['Date'].max()
    next_7 = df[(df['Date'] > today) & (df['Date'] <= today + pd.Timedelta(days=7))]

    seven_day_alert = False
    if not next_7.empty:
        seven_day_alert = any(next_7['Exposure'] >= 30)

     # 7-Day forecast summary
    today = df['Date'].max()
    next_7 = df[(df['Date'] > today) & (df['Date'] <= today + pd.Timedelta(days=7))]

    seven_day_alert = not next_7.empty and any(next_7['Exposure'] >= 30)

    html = render_template('bushfire_report.html',
                           alerts=alerts,
                           file=file,
                           chart_src=None,
                           now=datetime.now(),
                           seven_day_alert=seven_day_alert)

    pdf = io.BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)

    response = make_response(pdf.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=bushfire_alert_report.pdf'
    return response
