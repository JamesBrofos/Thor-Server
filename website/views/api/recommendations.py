import datetime as dt
import numpy as np
import sobol_seq
from flask import Blueprint, request, jsonify
from flask_api import status
from thor.optimization import BayesianOptimization
from sif.models import GaussianProcess
from ...models import Experiment, Observation
from ... import db
from ...utils import (
    require_apikey,
    encode_recommendation,
    decode_recommendation,
    create_space
)


recommendations = Blueprint("recommendations", __name__)


@recommendations.route("/api/create_recommendation/", methods=["POST"])
@require_apikey
def create_recommendation(user):
    # Extract parameters.
    experiment_id = request.json["experiment_id"]
    date = dt.datetime.today()
    description = request.json.get("description", "")
    # Get the experiment corresponding to this observation.
    exp = Experiment.query.filter_by(id=experiment_id).first()
    dims = exp.dimensions.all()
    n_dims = len(dims)
    space = create_space(dims)

    # Probability of selecting a random configuration.
    if request.json.get("rand_prob", None):
        rand_prob = request.json["rand_prob"]
    else:
        rand_prob = 0.
    # Number of model estimation iterations to perform. Note that the meaning of
    # this parameter changes when switching from a Gaussian process to a
    # Bayesian neural network.
    if request.json.get("n_model_iters", None):
        n_model_iters = request.json["n_model_iters"]
    else:
        n_model_iters = 10
    # Number of randomly positioned observations to create.
    n_random = 1 * n_dims

    # Either use Bayesian optimization or generate a random point depending on
    # the number of observations collected so far. Note that an input parameter
    # can be provided to determine the chance of selecting a configuration at
    # random. Setting this parameter to one is equivalent to assuming a policy
    # of pure exploration.
    n_observed = exp.observations.filter_by(pending=False).count()
    n_obs = exp.observations.count()
    sobol_rec = space.invert(sobol_seq.i4_sobol(n_dims, n_obs+1)[0]).ravel()
    rec = encode_recommendation(sobol_rec, dims)

    # If the number of observations exceeds the number of initialization
    # observations and we're not random sampling.
    if n_observed >= n_random and np.random.uniform() > rand_prob:
        # Get pending and non-pending observations.
        observed = exp.observations.filter(Observation.pending==False).all()
        pending = exp.observations.filter(Observation.pending==True).all()
        X, y = decode_recommendation(observed, dims)
        X_pending = (
            decode_recommendation(pending, dims)[0]
            if len(pending) > 0 else None
        )
        # Create a recommendation with Bayesian optimization.
        try:
            bo = BayesianOptimization(exp, space)
            c = bo.recommend(X, y, X_pending, GaussianProcess, n_model_iters)
            rec = encode_recommendation(c, dims)
        except Exception as err:
            print(
                "Bayesian optimization error: {}. "
                "The recommendation is: {}.".format(err, rec)
            )

    # Submit recommendation to user and store in the Thor database. It is
    # created initially without a response and is marked as pending.
    obs = Observation(str(rec), date, description)
    exp.observations.append(obs)
    # Commit changes.
    db.session.commit()

    return jsonify(obs.to_dict())

@recommendations.route("/api/submit_recommendation/", methods=["POST"])
@require_apikey
def submit_recommendation(user):
    # Extract recommendation identifier and observed value.
    identifier = request.json["recommendation_id"]
    value = request.json["value"]
    # Update observation.
    obs = Observation.query.filter_by(id=identifier).first()

    if obs is not None:
        e = Experiment.query.filter_by(id=obs.experiment_id).first()
        if e.user_id == user.id:
            obs.target = value
            obs.pending = False
            # Commit changes.
            db.session.commit()

            return jsonify({"id": identifier, "submitted": True})
    else:
        err = {"error": "Observation does not exist."}
        print(err)
        return (jsonify(err), status.HTTP_400_BAD_REQUEST)

@recommendations.route("/api/pending_recommendations/", methods=["POST"])
@require_apikey
def pending_recommendations(user):
    # Extract experiment.
    experiment_id = request.json["experiment_id"]
    exp = user.experiments.filter(Experiment.id==experiment_id).first()

    if exp:
        pending_obs = exp.observations.filter(Observation.pending==True).all()
        return jsonify([o.to_dict() for o in pending_obs])
    else:
        err = {
            "error": "Experiment with identifier {} does not exist.".format(
                experiment_id
            )
        }
        print(err)
        return (jsonify(err), status.HTTP_400_BAD_REQUEST)
