import os

import pytest

import constantstest


def create_dir(directory, mode=0777):
    """
    Ensure that the given directory is created with all intermediate directories.

    :param directory: the directory to create.
    :param mode: the directory mode. Default: 0777 (octal).
    """
    if not os.path.exists(directory):
        os.makedirs(directory, mode=mode)

    return directory


@pytest.fixture(scope='module')
def module_test_dir(request):
    return os.path.join(constantstest.TEST_RUN_DIR, request.module.__name__)


@pytest.fixture(scope='class')
def class_test_dir(request, module_test_dir):
    return os.path.join(module_test_dir, request.cls.__name__)


@pytest.fixture(scope='function')
def function_test_dir(request, class_test_dir):
    return os.path.join(class_test_dir, request.function.__name__)
