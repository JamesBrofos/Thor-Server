import datetime as dt
import numpy as np
import sobol_seq
import traceback
import logging
from flask import Blueprint, request, jsonify
from flask_api import status
from scipy.spatial.distance import cdist
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
    # Get the experiment corresponding to this observation.
    exp = Experiment.query.filter_by(id=experiment_id).first()
    dims = exp.dimensions.all()
    n_dims = len(dims)
    space = create_space(dims)

    # Which acquisition function would you like to use?
    acq_func = request.json.get("acq_func", "expected_improvement")
    # Description of this observation or experiment.
    description = request.json.get("description", "")
    # Probability of selecting a random configuration.
    rand_prob = request.json.get("rand_prob", 0.)
    # Number of model samples to draw from the Bayesian posterior.
    n_models = request.json.get("n_models", 5)
    # Number of randomly positioned observations to create.
    n_random = 1 * n_dims

    # We'll include an indicator for whether or not to return a recommendation
    # for each computed model or to return a single recommendation for an
    # integrated acquisition function.
    integrate_acq = request.json.get("integrate_acq", True)

    # Either use Bayesian optimization or generate a random point depending on
    # the number of observations collected so far. Note that an input parameter
    # can be provided to determine the chance of selecting a configuration at
    # random. Setting this parameter to one is equivalent to assuming a policy
    # of pure exploration.
    n_observed = exp.observations.filter_by(pending=False).count()
    n_obs = exp.observations.count()
    if integrate_acq:
        rec = space.invert(sobol_seq.i4_sobol(n_dims, n_obs+1)[0].ravel())
    else:
        rec = space.invert([sobol_seq.i4_sobol(n_dims, n_obs+1+i)[0] for i in range(n_models)])

    # If the number of observations exceeds the number of initialization
    # observations and we're not random sampling.
    if n_observed >= n_random and np.random.uniform() > rand_prob:
        # Create a flag that is true when the Bayesian optimization algorithm
        # fails due to numerical instability.
        optimization_failed = False
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
            bo_rec = BayesianOptimization(exp, space).recommend(
                X,
                y,
                X_pending,
                GaussianProcess,
                n_models,
                acq_func,
                integrate_acq
            )
            bo_rec_inv = space.invert(bo_rec)
        except Exception as err:
            optimization_failed = True
            logging.error(traceback.format_exc())

        # There are several failure modes that we are considering here. First,
        # there is a case where the chosen point is too close to any other point
        # we've previously evaluated (up to machine precision). Second, there is
        # an unusual case where the recommendation from the Bayesian
        # optimization procedure contains NaNs. Additionally, if the Bayesian
        # optimization algorithm failed due to numerical instability, this is
        # the third failure mode.
        X_orig = space.invert(X)
        if optimization_failed:
            print("Optimization failed. Using Sobol recommendation: {}.".format(rec))
            description += " Sobol"
        elif (
                (cdist(np.atleast_2d(bo_rec_inv), X_orig) < 1e-10).any() or
                np.isnan(bo_rec_inv).any()
        ):
            print(
                "Invalid recommendation recommendation: {}. "
                "Using Sobol recommendation: {}.".format(bo_rec_inv, rec)
            )
            description += " Sobol"
        else:
            rec = bo_rec_inv
    else:
        description += " Sobol"

    # Submit recommendation to user and store in the Thor database. It is
    # created initially without a response and is marked as pending.
    O = []
    for r in np.atleast_2d(rec):
        obs = Observation(
            str(encode_recommendation(r, dims)),
            dt.datetime.today(),
            description
        )
        exp.observations.append(obs)
        O.append(obs)
    # Commit changes.
    db.session.commit()

    return jsonify([o.to_dict() for o in O])

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
