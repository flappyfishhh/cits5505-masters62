from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from app.models import User
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
# =============================
# User Registration Form
# =============================
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')
    ])
    password2 = PasswordField('Repeat Password', validators=[DataRequired()])
    security_answer = StringField('What was the name of your first pet?', validators=[DataRequired()])
    submit = SubmitField('Register')

    # Check if username is already taken
    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Please use a different username.')

    # Check if email is already registered
    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Please use a different email address.')

# =============================
# User Login Form
# =============================
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

# =============================
# File Upload Form
# =============================
class UploadForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()])
    latitude = FloatField('Latitude', validators=[DataRequired()])
    longitude = FloatField('Longitude', validators=[DataRequired()])
    csv_file = FileField('CSV File', validators=[
        FileRequired(message='CSV file is required'),
        FileAllowed(['csv'], 'Only CSV files are allowed')
    ])

    # Visibility: who can access this file
    visibility = SelectField('Visibility', choices=[
        ('private', 'Private'), 
        ('public', 'Public'), 
        ('shared', 'Shared')
    ], default='private')

    # Comma-separated email list for sharing (only applies if visibility = shared)
    share_with = StringField('Share With (Emails)', validators=[Optional()])

    submit = SubmitField('Upload')

# =============================
# Forgot Password Form
# =============================
class ForgotPasswordForm(FlaskForm):
    email = StringField('Registered Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Next')

# =============================
# Reset Password Form
# =============================
class ResetPasswordForm(FlaskForm):
    security_answer = StringField('What was the name of your first pet?', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('new_password2', message='Passwords must match')
    ])
    new_password2 = PasswordField('Repeat New Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

# =============================
# Update Email Form
# =============================
class UpdateEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Email()])
    submit_email = SubmitField('Update Email')

    # Prevent changing to an email already in use
    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('This email is already in use.')

# =============================
# Change Password Form
# =============================
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[Optional()])
    security_answer = StringField('What was the name of your first pet?', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('new_password2', message='Passwords must match')
    ])
    new_password2 = PasswordField('Repeat New Password', validators=[DataRequired()])
    submit_password = SubmitField('Change Password')

# =============================
# Update File Visibility & Sharing Form
# =============================
class UpdateFileForm(FlaskForm):
    visibility = SelectField('Visibility', choices=[
        ('private', 'Private'), 
        ('public', 'Public'), 
        ('shared', 'Shared')
    ], default='private')
    share_with = StringField('Share With (Emails)', validators=[Optional()])
    submit = SubmitField('Update Permissions')

    # Custom validator: validate shared emails if visibility is set to 'shared'
    def validate_share_with(self, field):
        if self.visibility.data == 'shared' and field.data:
            emails = [e.strip() for e in field.data.split(',') if e.strip()]
            for email in emails:
                if email == current_user.email:
                    raise ValidationError("You cannot share with your own account")
                if not User.query.filter_by(email=email).first():
                    raise ValidationError(f"User with email {email} not found")


# =============================
# Empty form, just for CSRF protection.
# =============================
class VisualizationForm(FlaskForm):
    x_axis = SelectField("X Axis", choices=[])  # choices will be set dynamically in the route
    y_axis = SelectField("Y Axis", choices=[])
    submit = SubmitField("Generate Chart")