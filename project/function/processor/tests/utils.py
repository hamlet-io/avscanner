import os
import json


def get_test_data_text(name):
    with open(os.path.join('tests/data', name)) as f:
        return f.read()


def get_test_data_file_text(name):
    return get_test_data_text(os.path.join('files', name))


def get_test_data_event_text(name):
    return get_test_data_text(os.path.join('events', name))


def get_test_data_event(name):
    return json.loads(get_test_data_event_text(name))
