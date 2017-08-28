import numpy as np
import datetime as dt
from sqlalchemy.ext.hybrid import hybrid_property
from .observation import Observation
from .dimension import Dimension
from .. import db


class Experiment(db.Model):
    """Experiment Class"""
    __tablename__ = "experiments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(80))
    date = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, server_default="FALSE", default=False,
                             nullable=False)
    acq_func = db.relationship(
        "AcquisitionFunction",
        uselist=False,
        backref="experiments",
        cascade="all, delete-orphan"
    )
    dimensions = db.relationship(
        "Dimension",
        lazy="dynamic",
        backref="experiments",
        cascade="all, delete-orphan"
    )
    observations = db.relationship(
        "Observation",
        lazy="dynamic",
        backref="experiments",
        cascade="all, delete-orphan"
    )

    def __init__(self, name, date):
        self.name = name
        self.date = date
        self.is_published = False

    def to_dict(self):
        dims = [d.to_dict() for d in self.dimensions.all()]
        return {
            "name": self.name,
            "date": self.date,
            "dimensions": dims,
            "id": self.id,
            "is_published": self.is_published
        }

    @classmethod
    def from_json(cls, json):
        date = dt.datetime.today()
        name = json["name"]
        dims = json["dimensions"]
        e = cls(name, date)
        # Handle the case of multiple dimensions or a single dimension supplied
        # as a dictionary.
        if isinstance(dims, list):
            for d in dims:
                e.dimensions.append(Dimension.from_json(d))
        else:
            e.dimensions.append(Dimension.from_json(dims))

        return e

    @hybrid_property
    def percent_improvement(self):
        first = self.observations.order_by("date").first()
        best = self.maximal_observation
        return np.abs((best.target - first.target) / first.target) * 100.

    @hybrid_property
    def maximal_observation(self):
        return self.observations.filter_by(
            pending=False
        ).order_by(Observation.target.desc()).first()

    @hybrid_property
    def area_over_curve(self):
        best = self.maximal_observation.target
        series = np.maximum.accumulate(
            [o.target for o in self.observations.filter_by(
                pending=False
            ).order_by("date").all()]
        )
        return np.mean(best - series)
