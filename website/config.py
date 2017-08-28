SQLALCHEMY_DATABASE_URI = "postgresql://thor_server:thor@localhost:5432/thor"
SQLALCHEMY_TRACK_MODIFICATIONS = True

SECRET_KEY = "THIS IS A SECRET KEY - SEE README TO SET YOUR OWN"

MAIL_PREFIX = "[Thor]"
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = "this.is.a.gmail.account@gmail.com"
MAIL_PASSWORD = "this.is.a.password"
