def to_aws_params(**raw_params):
    params = dict()
    for name, value in raw_params.items():
        if value is not None:
            params[name] = value
    return params
