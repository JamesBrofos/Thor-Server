from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from ... import db

api = Blueprint("api", __name__)


@api.route("/api/<string:tab>/")
@login_required
def page(tab="introduction"):
    return render_template("api.jinja2", tab=tab)


@api.route("/api/delete/<int:experiment_id>/", methods=["POST"])
@login_required
def delete_experiment(experiment_id):
    # Query for the corresponding experiment to delete.
    exp = current_user.experiments.filter_by(id=experiment_id).first()
    if exp:
        db.session.delete(exp)
        db.session.commit()
        flash("Deleted experiment.", "success")
    else:
        db.session.rollback()
        flash("Unable to delete experiment.", "warning")
    return redirect(url_for("index.page"))


@api.route("/api/publish/<int:experiment_id>/", methods=["POST"])
@login_required
def publish_experiment(experiment_id):
    # Query for the corresponding experiment to publish.
    exp = current_user.experiments.filter_by(id=experiment_id).first()
    if exp:
        exp.is_published = True
        db.session.commit()
        flash("Published experiment.", "success")
    else:
        db.session.rollback()
        flash("Unable to publish experiment.", "warning")
    return redirect(url_for("experiment.admin_page",
                            experiment_id=experiment_id, tab='admin'))


@api.route("/api/unpublish/<int:experiment_id>/", methods=["POST"])
@login_required
def unpublish_experiment(experiment_id):
    # Query for the corresponding experiment to unpublish.
    exp = current_user.experiments.filter_by(id=experiment_id).first()
    if exp:
        exp.is_published = False
        db.session.commit()
        flash("Unpublished experiment.", "success")
    else:
        db.session.rollback()
        flash("Unable to unpublish experiment.", "warning")
    return redirect(url_for("experiment.admin_page",
                            experiment_id=experiment_id, tab='admin'))
