import os
import logging
from logging.config import dictConfig
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration


SENTRY_DSN = os.environ.get('SENTRY_DSN', default=None)


if SENTRY_DSN:  # pragma: no cover
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[AwsLambdaIntegration()]
    )


LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s[%(name)s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    '': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

dictConfig(LOGGING)

root = logging.getLogger()
