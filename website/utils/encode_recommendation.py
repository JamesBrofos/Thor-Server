import json


def encode_recommendation(rec, dims):
    """This function encodes a representation and associated list of dimensions
    into a JSON dictionary. This dictionary contains keys giving the name of
    the associated hyperparameter and the suggested value of that dimension of
    the hyperparameter set.
    """
    return json.dumps({
        d.name: int(v) if d.dim_type == "integer" else v for v, d in zip(rec, dims)
    })
