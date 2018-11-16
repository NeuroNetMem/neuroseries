from .interval_set import *
from .time_series import *
from . import tests


def get_test_data_dir():
    import os
    path = os.path.join(os.path.dirname(__file__), os.pardir)
    return os.path.join(path, 'test_data')