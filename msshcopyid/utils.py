import getpass
import logging
import os
import sys

import paramiko

from msshcopyid.constants import DEFAULT_SSH_CONFIG, DEFAULT_SSH_PORT
import msshcopyid

logger = logging.getLogger(__name__)


def get_password(from_stdin_only=False):
    """
    Get a password either from STDIN or by prompting the user.

    :return: the password.
    """
    if not sys.stdin.isatty():
        password = sys.stdin.readline().strip()
    elif not from_stdin_only:
        password = getpass.getpass('Enter the password: ')
    else:
        password = None

    return password


def load_ssh_config(config=DEFAULT_SSH_CONFIG):
    ssh_config = paramiko.config.SSHConfig()
    if os.path.isfile(config):
        with open(config) as fh:
            ssh_config.parse(fh)
        logger.debug('Loaded SSH configuration from [%s]', config)
    else:
        logger.debug('SSH config file "{0}" not found.'.format(config))

    return ssh_config


def parse_hosts(hosts, ssh_port=None, ssh_config=None):
    """
    Parse a list of hosts (string) and return a list of `msshcopyid.Host` objects.

    The information about the host are taken in this order of priority:

    - host:
        - from the host (string) itself.
    - user:
        - from the host (string) itself.
        - from the `paramiko.config.SSHConfig` object.
        - current logged user.
    - port:
        - from the function argument `port`.
        - from the `paramiko.config.SSHConfig` object.
        - default SSH port: 22

    :param hosts: list of hosts (string). Eg: ['server1', 'user1@server2']
    :param ssh_config: a `paramiko.config.SSHConfig` object.
    :return: a list of `msshcopyid.Host` objects.
    """
    host_list = []  # list of Host objects
    current_user = getpass.getuser()
    for host in hosts:
        # host_info = {'hostname': 'server1', 'hashknownhosts': 'no', 'user': 'user1'}
        if ssh_config is not None:
            host_info = ssh_config.lookup(host)
        else:
            host_info = {}

        # hostname & user
        if '@' in host:
            user, hostname = host.split('@', 1)
        else:
            hostname = host
            user = host_info.get('user', current_user)

        # port
        port = ssh_port or host_info.get('port', DEFAULT_SSH_PORT)

        host_list.append(msshcopyid.Host(hostname=hostname, port=port, user=user))

    return host_list
