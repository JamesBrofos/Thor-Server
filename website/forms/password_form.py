from flask_wtf import FlaskForm
from wtforms.fields import PasswordField, SubmitField
from wtforms.validators import Required, Length, EqualTo

class PasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[
        Required(message="You must enter a password."),
        Length(min=8, message="Your password must be at least 8 characters long")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        Required(message="You must confirm your password"),
        EqualTo("password", message="Passwords do not match")
    ])
    submit = SubmitField("Submit")
