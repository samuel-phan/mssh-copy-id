import logging
import os
import subprocess

import filetest

logger = logging.getLogger(__name__)


def gen_ssh_keys(ssh_key_dir):
    ssh_key_file = os.path.join(ssh_key_dir, 'id_rsa')
    ssh_pub_file = os.path.join(ssh_key_dir, 'id_rsa.pub')
    filetest.create_dir(ssh_key_dir)
    subprocess.check_call(['ssh-keygen', '-N', "", '-f', ssh_key_file], stdout=open(os.devnull, 'wb'))
    logger.info('Generated SSH keys "{}".'.format(ssh_key_file))
    return ssh_key_file, ssh_pub_file
