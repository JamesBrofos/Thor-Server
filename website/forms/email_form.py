from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField
from wtforms.validators import Required, Email

class EmailForm(FlaskForm):
    email = TextField("Email", validators=[
        Required(message="You must enter an email."),
        Email()
    ])
    submit = SubmitField("Submit")
