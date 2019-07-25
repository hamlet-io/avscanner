from __init__ import handler
from s3client import client


handler(
    {
        'user': 'testuser',
        'file': {
            'name': 'test.json'
        }
    },
    {}
)
