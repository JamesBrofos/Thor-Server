# Thor Server

This module implements the functionality of the Thor Server, a web service for performing Bayesian optimization. This site is responsible for presenting a visual overview of a user's machine learning and parameter tuning experiments and for providing references to tutorials and software downloads of client-side applications.

## Installation

In order to install and operate the Thor Server, please follow these steps:

1. Ensure that you have installed the requirements for Thor and Thor-Server by executing `pip install -r requirements.txt`.
2. Create a user named `thor_server` and a database named `thor` in your Postgres database.
3. Execute the following block of code to set up the Thor database:
```shell
python db.py db init
python db.py db migrate
python db.py db upgrade head
```
4. To run the Thor Server on your computer's localhost, simply run `make` from the root directory of this repository. For development, run `make dev` to enable automatic application reloads whenever code changes as well as verbose (debug) logging.

## Documentation

Documentation for using Thor's API clients, which exist presently for Python, MATLAB, and R, will be hosted online as well as made available as inline comments in the client source code.

Documentation for Python and MATLAB will be hosted on a corresponding site on [Read the Docs](https://readthedocs.org/). Documentation for R will be provided through CRAN or through the R client's dedicated page on GitHub.

## Email Notifications

For deployment it can be useful to have an email account setup to dispense messages. This can be accomplished by nagivating to the file `./website/__init__.py` and modifying the application attributes
```python
app.config["MAIL_USERNAME"] = "this.is.a.gmail.account@gmail.com"
app.config["MAIL_PASSWORD"] = "this.is.a.password"
```
Enter the gmail address and the password you want to use.
