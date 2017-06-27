import json
from sqlalchemy.ext.hybrid import hybrid_property
from .. import db


class Observation(db.Model):
    """Observation Class"""
    __tablename__ = "observations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    experiment_id = db.Column(db.Integer, db.ForeignKey("experiments.id"))
    configuration = db.Column(db.Text)
    target = db.Column(db.Float, default=None)
    pending = db.Column(db.Boolean, default=True)
    date = db.Column(db.DateTime)

    def __init__(self, configuration, date):
        self.configuration = configuration
        self.date = date

    @hybrid_property
    def config(self):
        return json.loads(self.configuration)

    def to_dict(self):
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "config": self.configuration,
            "target": self.target,
            "pending": self.pending
        }
