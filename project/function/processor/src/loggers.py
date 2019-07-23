import logging
from logging.config import dictConfig

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
