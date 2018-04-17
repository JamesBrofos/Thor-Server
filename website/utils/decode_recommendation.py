import numpy as np
import json


def decode_recommendation(observations, dims):
    """This function converts a list of Observation objects defined by the database
    to both a numpy array representing a design matrix and a vector of targets.
    These represent settings of machine learning hyperparameters and their
    associated performance.
    """
    # Initialize a design matrix in addition to a vector of targets. These are
    # initialized to zero.
    n_observations, n_dims = len(observations), len(dims)
    X = np.zeros((n_observations, n_dims))
    y = np.zeros((n_observations, ))
    # Convert each of the observations to a vector representation and an
    # associated performance.
    for i, obs in enumerate(observations):
        o = json.loads(obs.configuration)
        X[i] = np.array([o[dim.name] for dim in dims])
        y[i] = obs.target

    return X, y
