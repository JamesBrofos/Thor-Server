from flask import Blueprint, render_template, redirect, flash, request, url_for
from flask_login import login_user, logout_user, login_required
from ..utils import require_unauthed, ts, send_email
from ..forms import LoginForm, EmailForm, PasswordForm
from ..models import User
from .. import db


login = Blueprint("login", __name__)

@login.route("/login/", methods=["GET", "POST"])
@require_unauthed
def login_page():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data
        ).first()
        login_user(user, form.remember_me.data)
        flash("Logged in successfully!", "success")
        next = request.args.get("next")

        return redirect(next or url_for("index.page"))

    return render_template("login.jinja2", form=form)

@login.route("/logout/")
@login_required
def logout_page():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("index.page"))

@login.route('/reset/', methods=["GET", "POST"])
@require_unauthed
def reset():
    form = EmailForm()
    if form.validate_on_submit():
        # Send an email to the user requesting to change the account's password.
        user = User.query.filter_by(email=form.email.data).first_or_404()
        subject = "Password reset requested"

        # Here we use the URLSafeTimedSerializer we created.
        token = ts.dumps(user.email, salt="recover-key")
        recover_url = url_for("login.reset_with_token", token=token, _external=True)
        html = render_template("email/recover.jinja2", recover_url=recover_url)
        send_email(user.email, subject, html)

        flash("Sent password reset request to {}".format(form.email.data),
              "success")

        return redirect(url_for("index.page"))

    return render_template("reset.jinja2", form=form)

@login.route('/reset/<token>', methods=["GET", "POST"])
@require_unauthed
def reset_with_token(token):
    try:
        email = ts.loads(token, salt="recover-key", max_age=86400)
    except:
        abort(404)

    form = PasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()
        user.password = form.password.data
        db.session.commit()

        flash("Successfully reset password!", "success")
        return redirect(url_for("login.login_page"))

    return render_template("reset_with_token.jinja2", form=form, token=token)
