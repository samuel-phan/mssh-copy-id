import datetime
import logging
import os

import pytest


def fmt_ctn_log(ctn_name, msg):
    """
    Format container log entry.
    """
    return '[{}] {}'.format(ctn_name, msg)


@pytest.fixture(scope='session', autouse=True)
def session_init_log(session_test_dir):
    log_file = os.path.join(session_test_dir, 'session.log')

    root_logger = logging.getLogger()
    fh = logging.FileHandler(log_file)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s'))
    root_logger.addHandler(fh)


@pytest.fixture(scope='function', autouse=True)
def function_init_log(request, function_test_dir):
    start_dt = datetime.datetime.now()
    log_file = os.path.join(function_test_dir, 'log')

    root_logger = logging.getLogger()
    fh = logging.FileHandler(log_file)
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] %(message)s'))
    root_logger.addHandler(fh)
    logger = logging.getLogger(request.module.__name__)
    logger.info('Start test function "%s".', request.function.__name__)

    yield

    logger.info('Ended test function "%s". (elapsed: %s)',
                request.function.__name__, datetime.datetime.now() - start_dt)
    root_logger.removeHandler(fh)
