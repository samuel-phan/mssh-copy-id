import logging
import os

import pytest

import filetest


class BaseTestClass(object):

    @pytest.fixture(scope='function', autouse=True)
    def init_logger(self, request, function_test_dir):
        log_file = os.path.join(function_test_dir, 'log')
        filetest.create_dir(function_test_dir)

        root_logger = logging.getLogger()
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))
        root_logger.addHandler(fh)
        self.logger = logging.getLogger(request.module.__name__)
