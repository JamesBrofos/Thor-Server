# Thor Server

This module implements the functionality of the Thor Server, a web service for performing Bayesian optimization. This site is responsible for presenting a visual overview of a user's machine learning and parameter tuning experiments and for providing references to tutorials and software downloads of client-side applications.

## Installation

In order to install and operate the Thor Server, please follow these steps:

1. Ensure that you have installed the requirements for Thor and Thor-Server by executing `pip install -r requirements.txt`.
2. Create a local directory `instance` and a config file `local_config.py` in that directory to hold configuration variables specific to your configuration, e.g.:
 * `SQLALCHEMY_DATABASE_URI` - defaults to user `thor_server` and db `thor`
 * `SECRET_KEY` - for sessions; see [How to generate good secret keys](http://flask.pocoo.org/docs/0.12/quickstart/#sessions), under "Sessions"
 * `MAIL_*` - as appropriate
3. Create a user and database to match your `SQLALCHEMY_DATABASE_URI`.
4. Execute the following block of code to set up the Thor database:
```shell
python db.py db init
python db.py db migrate
python db.py db upgrade head
```
5. To run the Thor Server on your computer's localhost, simply run `make` from the root directory of this repository. For development, run `make dev` to enable automatic application reloads whenever code changes as well as verbose (debug) logging.

## Updates / schema migrations

Thor Server uses [alembic](http://alembic.zzzcomputing.com/en/latest/index.html) for database schema migrations via [flask-migrate](https://flask-migrate.readthedocs.io/en/latest/).  Migration support and versioning scripts are stored under `migrations/`. When new
schema migrations are added, update an existing database using the `upgrade` command:

```shell
python db.py db upgrade head
```

It is probably best to test this first and to ensure backups are up to date
before applying to production instances.

During development, after you change the models/schema, start a new migration
script using `migrate`:

```shell
python db.py db migrate
```

Alembic will attempt to auto-generate the script for you, but note that its [ability to detect changes is limited](http://alembic.zzzcomputing.com/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect), and the generated script should be thought of as a starting point for your review. Be sure to examine the generated migration script before applying and committing.

To add a description to the migration name to help the versioning script stand out a little more, use `-m`:

```shell
python db.py db migrate -m "add is_published column"
```

When a new migration script is complete, upgrade schemas using `upgrade` as described above.


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
