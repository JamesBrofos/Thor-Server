from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField, PasswordField, BooleanField
from wtforms.validators import Required, Email, ValidationError
from .validators import Exists, Active, CorrectPassword
from ..models import User


class LoginForm(FlaskForm):
    username = TextField("Username", validators=[
        Required(),
        Exists(User, User.username, message="Username does not exist."),
        Active(),
    ])
    password = PasswordField("Password", validators=[
        Required(), CorrectPassword()
    ])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Submit")
