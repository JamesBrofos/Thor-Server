import pandas as pd
import numpy as np
from flask import (
    Blueprint,
    render_template,
    abort, request,
    make_response,
    url_for,
    redirect
)
from flask_login import login_required, current_user
from flask_api import status
# Bokeh imports.
from bokeh.embed import components
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import HoverTool
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8
# Thor Server imports.
from ..models import Experiment, Observation
from ..utils import decode_recommendation
from .. import db

experiment = Blueprint("experiment", __name__)
js_resources = INLINE.render_js()
css_resources = INLINE.render_css()


@experiment.route(
    "/experiment/<int:experiment_id>/analysis/delete_pending/",
    methods=["POST"]
)
@login_required
def delete_pending(experiment_id):
    # Query for the corresponding experiment.
    exp = Experiment.query.filter_by(
        id=experiment_id, user_id=current_user.id
    ).first_or_404()
    pending = exp.observations.filter(Observation.pending==True).all()
    for obs in pending:
        db.session.delete(obs)
    db.session.commit()

    return redirect(url_for("experiment.analysis_page",
                            experiment_id=experiment_id))


@experiment.route("/experiment/<int:experiment_id>/history/download/")
@login_required
def download_history(experiment_id):
    # Query for the corresponding experiment.
    experiment = Experiment.query.filter_by(id=experiment_id).filter(
        (Experiment.user_id==current_user.id) | (Experiment.is_published==True)
    ).first_or_404()
    # Parse the observations into a pandas dataframe.
    dims = experiment.dimensions.all()
    # obs = experiment.observations.filter(Observation.pending==False).all()
    obs = experiment.observations.order_by("id").all()
    X, y = decode_recommendation(obs, dims)
    D = pd.DataFrame(X, columns=[d.name for d in dims])
    D["target"] = y
    D["obs_id"] = [o.id for o in obs]
    D["date"] = [pd.datetime.strftime(o.date, '%Y-%m-%d %H:%M:%S')
                 for o in obs]
    D["description"] = [o.description or "" for o in obs]
    D.set_index('obs_id', inplace=True)
    # Make a comma-separated variables file.
    resp = make_response(D.to_csv())
    resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
    resp.headers["Content-Type"] = "text/csv"

    return resp


@experiment.route("/experiment/<int:experiment_id>/history/")
@login_required
def history_page(experiment_id):
    # Query for the corresponding experiment.
    experiment = Experiment.query.filter_by(id=experiment_id).filter(
        (Experiment.user_id==current_user.id) | (Experiment.is_published==True)
    ).first_or_404()

    return render_template(
            "experiment.jinja2",
            tab="history",
            experiment=experiment
        )


@experiment.route("/experiment/<int:experiment_id>/analysis/")
@login_required
def analysis_page(experiment_id):
    # Query for the corresponding experiment.
    experiment = Experiment.query.filter_by(id=experiment_id).filter(
        (Experiment.user_id==current_user.id) | (Experiment.is_published==True)
    ).first()
    # Grab the inputs arguments from the URL.
    args = request.args
    # Variable selector for analysis.
    selected_dim = int(args.get("variable", 0))

    if experiment:
        dims = experiment.dimensions.all()
        if experiment.observations.filter_by(pending=False).count() > 1:
            obs = experiment.observations.filter_by(
                pending=False
            ).order_by("date").all()
            # Extract best observation so far.
            X, y = decode_recommendation(obs, dims)
            sd = dims[selected_dim]
            # Construct tooltips on hover.
            D = {d.name.replace(" ", "_"): X[:, i] for i, d in enumerate(dims)}
            D["objective"] = y
            source = ColumnDataSource(data=D)
            hover = HoverTool(
                tooltips=[("Objective", "@objective")] +
                [(d.name, "@{}".format(d.name.replace(" ", "_"))) for d in dims],
                names=["evals"]
            )
            # Visualize.
            fig = figure(
                title="Metric vs. Variable Scatter",
                tools=["pan", "box_zoom", "reset", hover],
                plot_height=225,
                sizing_mode='scale_width',
                x_axis_label="Variable",
                x_axis_type="log" if sd.dim_type == "logarithmic" else "linear"
            )
            fig.circle(sd.name.replace(" ", "_"), "objective", source=source, name="evals")
            fig.toolbar.logo = None
            script, div = components(fig)
        else:
            script, div = "", ""

        return encode_utf8(
            render_template(
                "experiment.jinja2",
                tab="analysis",
                selected_dim=selected_dim,
                experiment=experiment,
                plot_script=script,
                plot_div=div,
                js_resources=js_resources,
                css_resources=css_resources,
            )
        )
    else:
        abort(404)


@experiment.route("/experiment/<int:experiment_id>/")
@login_required
def overview_page(experiment_id):
    # Query for the corresponding experiment.
    experiment = Experiment.query.filter_by(id=experiment_id).filter(
        (Experiment.user_id==current_user.id) | (Experiment.is_published==True)
    ).first_or_404()

    dims = experiment.dimensions.all()
    if experiment.observations.filter_by(pending=False).count() > 1:
        obs = experiment.observations.filter_by(
            pending=False
        ).order_by("date").all()
        # Decode the observations into a design matrix and a vector of targets.
        X, y = decode_recommendation(obs, dims)
        cummax = np.maximum.accumulate(y)
        r = np.arange(1, cummax.shape[0] + 1, step=1)
        # Construct tooltips on hover.
        D = {d.name.replace(" ", "_"): X[:, i] for i, d in enumerate(dims)}
        D["objective"] = y
        D["r"] = r
        source = ColumnDataSource(data=D)
        hover = HoverTool(
            tooltips=[("Objective", "@objective")] + [(d.name, "@{}".format(d.name.replace(" ", "_"))) for d in dims],
            names=["evals"]
        )

        # Visualize the performance of the algorithm so far. This involves
        # showing a cumulative best line alongside dots indicating the
        # evaluation of the objective at each iteration. The plot is
        # accompanied by tools for banning, zooming, tooltips on hover, and
        # reseting the figure.
        fig = figure(
            title="Metric Improvement",
            tools=["pan", "box_zoom", "reset", hover],
            plot_height=225,
            sizing_mode='scale_width',
            x_axis_label="Number of Observations",
        )
        fig.line(r, cummax, line_width=2)
        fig.circle("r", "objective", source=source, name="evals")
        fig.toolbar.logo = None
        script, div = components(fig)
    else:
        script, div = "", ""

    return encode_utf8(
        render_template(
            "experiment.jinja2",
            tab="overview",
            experiment=experiment,
            plot_script=script,
            plot_div=div,
            js_resources=js_resources,
            css_resources=css_resources,
        )
    )


@experiment.route("/experiment/<int:experiment_id>/admin/")
@login_required
def admin_page(experiment_id):
    # Query for the corresponding experiment.
    experiment = Experiment.query.filter_by(
        id=experiment_id, user_id=current_user.id
    ).first_or_404()

    return render_template(
            "experiment.jinja2",
            tab="admin",
            experiment=experiment
        )


@experiment.errorhandler(404)
def page_not_found(e):
    return render_template("404.jinja2"), status.HTTP_404_NOT_FOUND
