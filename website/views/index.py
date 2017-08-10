from flask import Blueprint, render_template
from flask_login import current_user

from ..models import Experiment


index = Blueprint("index", __name__)
# Define the number of experiments that will appear on a page.
EXPERIMENTS_PER_PAGE = 10


@index.route("/")
@index.route("/<int:page>")
def page(page=1):
    try:
        experiments = current_user.experiments.order_by(
            Experiment.date.desc()
            ).paginate(
                page, EXPERIMENTS_PER_PAGE, False
                )
    except AttributeError:
        experiments = None

    return render_template("index.jinja2", experiments=experiments)
