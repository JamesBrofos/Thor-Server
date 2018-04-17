from thor.space import Space


def create_space(model_dims):
    """This function creates a Thor Space object by providing a set of dimensions
    to the initialization method of the Space object.
    """
    return Space([d.to_thor_dimension() for d in model_dims])
