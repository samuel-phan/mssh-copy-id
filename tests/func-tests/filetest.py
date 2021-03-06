import os

import pytest

import constantstest


@pytest.fixture(scope='session')
def session_test_dir():
    return create_dir(os.path.join(constantstest.TEST_RUN_DIR))


@pytest.fixture(scope='module')
def module_test_dir(request):
    return create_dir(os.path.join(constantstest.TEST_RUN_DIR, request.module.__name__))


@pytest.fixture(scope='class')
def class_test_dir(request, module_test_dir):
    return create_dir(os.path.join(module_test_dir, request.cls.__name__))


@pytest.fixture(scope='function')
def function_test_dir(request, class_test_dir):
    return create_dir(os.path.join(class_test_dir, request.function.__name__))


def create_dir(directory, mode=0777):
    """
    Ensure that the given directory is created with all intermediate directories.

    :param directory: the directory to create.
    :param mode: the directory mode. Default: 0777 (octal).
    """
    if not os.path.exists(directory):
        os.makedirs(directory, mode=mode)

    return directory
