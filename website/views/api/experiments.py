import datetime as dt
from flask import Blueprint
from flask import request, jsonify
from flask_api import status
from ...utils import require_apikey
from ...models import Experiment, AcquisitionFunction, Observation
from ... import db


experiments = Blueprint("experiments", __name__)


@experiments.route("/api/submit_observation/", methods=["POST"])
@require_apikey
def submit_observation(user):
    # Get the corresponding experiment.
    exp_id = request.json["experiment_id"]
    exp = user.experiments.filter_by(id=exp_id).first()

    if exp:
        print("Submitted new observation and target")
        config = request.json["configuration"]
        target = request.json["target"]
        obs = Observation(str(config), dt.datetime.today())
        obs.target = target
        obs.pending = False
        exp.observations.append(obs)
        db.session.commit()
        return jsonify({"id": obs.id, "submitted": True})
    else:
        err = {
            "error": "Experiment with identifier {} does not exist.".format(
                exp_id
            )
        }
        return err


@experiments.route("/api/create_experiment/", methods=["POST"])
@require_apikey
def create_experiment(user):
    # Extract name and creation parameters.
    name = request.json["name"]
    overwrite = request.json.get("overwrite", False)
    maximize = request.json.get("maximize", True)
    # Check if the experiment already exists.
    exists = db.session.query(
        user.experiments.filter(Experiment.name==name).exists()
    ).scalar() > 0

    if exists and not overwrite:
        err = {"error": "Experiment named '{}' already exists.".format(name)}
        print(err)
        return (jsonify(err), status.HTTP_400_BAD_REQUEST)
    else:
        if exists:
            # If we need to overwrite an existing experiment.
            exp = user.experiments.filter_by(name=name).first()
            db.session.delete(exp)

        # Create an experiment for this user.
        exp = Experiment.from_json(request.json)
        exp.acq_func = AcquisitionFunction.from_json(request.json)
        user.experiments.append(exp)
        # Commit changes.
        db.session.commit()

        return jsonify(exp.to_dict())


@experiments.route("/api/experiment_for_name/", methods=["POST"])
@require_apikey
def experiment_for_name(user):
    # Extract name.
    name = request.json["name"]
    # Get experiments for user.
    experiment = user.experiments.filter(Experiment.name==name).first()
    if experiment:
        return jsonify(experiment.to_dict())
    else:
        err = {"error": "Experiment named '{}' does not exist.".format(name)}
        print(err)
        return (jsonify(err), status.HTTP_400_BAD_REQUEST)


@experiments.route("/api/best_configuration/", methods=["POST"])
@require_apikey
def best_configuration(user):
    # Extract experiment identifier.
    exp_id = request.json["experiment_id"]
    experiment = user.experiments.filter(Experiment.id==exp_id).first()
    if experiment:
        return jsonify(experiment.maximal_observation.to_dict())
    else:
        err = {
            "error": "Experiment with identifier {} does not exist.".format(
                exp_id
            )
        }
        print(err)
        return (jsonify(err), status.HTTP_400_BAD_REQUEST)
