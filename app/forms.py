from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')
    ])
    password2 = PasswordField('Repeat Password', validators=[DataRequired()])
    security_answer = StringField('What is your pet name?', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Please use a different email address.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Registered Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Next')

class ResetPasswordForm(FlaskForm):
    security_answer = StringField('What is your pet name?', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('new_password2', message='Passwords must match')
    ])
    new_password2 = PasswordField('Repeat New Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class UpdateEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Email()])
    submit_email = SubmitField('Update Email')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('This email is already in use.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[Optional()])
    security_answer = StringField('What is your pet name?', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('new_password2', message='Passwords must match')
    ])
    new_password2 = PasswordField('Repeat New Password', validators=[DataRequired()])
    submit_password = SubmitField('Change Password')
