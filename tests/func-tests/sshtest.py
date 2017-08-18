import logging
import os
import subprocess

import pytest

import filetest

logger = logging.getLogger(__name__)


class SSHKeys(object):

    def __init__(self, ssh_key_file=None, ssh_pub_file=None):
        """
        :param ssh_key_file: the file path to the private SSH key.
        :param ssh_pub_file: the file path to the public SSH key.
        """
        self.ssh_key_file = ssh_key_file
        self.ssh_pub_file = ssh_pub_file

    def __repr__(self):
        return '<{}.{} {}>'.format(self.__class__.__module__, self.__class__.__name__, self.__dict__)


def gen_ssh_keys(ssh_key_dir):
    ssh_key_file = os.path.join(ssh_key_dir, 'id_rsa')
    ssh_pub_file = os.path.join(ssh_key_dir, 'id_rsa.pub')
    filetest.create_dir(ssh_key_dir)
    subprocess.check_call(['ssh-keygen', '-N', "", '-f', ssh_key_file], stdout=open(os.devnull, 'wb'))
    logger.info('Generated SSH keys "%s".', ssh_key_file)
    return SSHKeys(ssh_key_file=ssh_key_file, ssh_pub_file=ssh_pub_file)


@pytest.fixture(scope='function')
def ssh_keys(function_test_dir):
    return gen_ssh_keys(os.path.join(function_test_dir, 'ssh_keys'))
