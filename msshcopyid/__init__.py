from __future__ import unicode_literals

import logging
import os
import subprocess
import sys

import paramiko

from msshcopyid._version import __version__, __version_info__
from msshcopyid.constants import DEFAULT_KNOWN_HOSTS
from msshcopyid.constants import DEFAULT_SSH_PORT

from msshcopyid.log import format_error
from msshcopyid.log import format_exception
from msshcopyid import utils

logger = logging.getLogger(__name__)


class SSHCopyId(object):
    def __init__(self, priv_key=None, pub_key=None, ssh_config=None, default_password=None):
        self.priv_key = priv_key
        self.pub_key = None
        self.set_pub_key(pub_key)
        self.pub_key_content = None
        self.ssh_config = ssh_config

        self.default_password = default_password

    def set_pub_key(self, pub_key):
        if pub_key:
            self.pub_key = pub_key
        elif self.priv_key:
            self.pub_key = '{0}.pub'.format(self.priv_key)
        else:
            self.pub_key = None

    def read_pub_key(self):
        if not os.path.exists(self.pub_key):
            logger.error(format_error('The SSH public key [%s] does not exist.'), self.pub_key)
            sys.exit(1)
        with open(self.pub_key) as fh:
            self.pub_key_content = fh.read().strip()

    def add_to_known_hosts(self, hosts, known_hosts=DEFAULT_KNOWN_HOSTS, dry=False):
        """
        Add the remote host SSH public key to the `known_hosts` file.

        :param hosts: the list of the remote `Host` objects.
        :param known_hosts: the `known_hosts` file to store the SSH public keys.
        :param dry: perform a dry run.
        """
        to_add = []
        with open(known_hosts) as fh:
            known_hosts_set = set(line.strip() for line in fh.readlines())

        cmd = ['ssh-keyscan'] + [host.hostname for host in hosts]
        logger.debug('Call: %s',  ' '.join(cmd))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        for line in stdout.splitlines():
            line = line.strip()
            logger.info('[%s] Add the remote host SSH public key to [%s]...', line.split(' ', 1)[0], known_hosts)
            if line not in known_hosts_set:
                known_hosts_set.add(line)
                to_add.append('{0}\n'.format(line))

        if not dry:
            with open(known_hosts, 'a') as fh:
                fh.writelines(to_add)

    def remove_from_known_hosts(self, hosts, known_hosts=DEFAULT_KNOWN_HOSTS, dry=False):
        """
        Remove the remote host SSH public key to the `known_hosts` file.

        :param hosts: the list of the remote `Host` objects.
        :param known_hosts: the `known_hosts` file to store the SSH public keys.
        :param dry: perform a dry run.
        """
        for host in hosts:
            logger.info('[%s] Removing the remote host SSH public key from [%s]...', host.hostname, known_hosts)
            cmd = ['ssh-keygen', '-f', known_hosts, '-R', host.hostname]
            logger.debug('Call: %s', ' '.join(cmd))
            if not dry:
                try:
                    subprocess.check_call(cmd)
                except subprocess.CalledProcessError as ex:
                    logger.error(format_error(format_exception(ex)))

    # TODO: change no_add_host to add_host
    def copy_ssh_keys_to_host(self, host, password=None, no_add_host=False, known_hosts=DEFAULT_KNOWN_HOSTS):
        """
        Copy the SSH keys to the given host.

        :param host: the `Host` object to copy the SSH keys to.
        :param password: the SSH password for the given host.
        :param no_add_host: if the host is not in the known_hosts file, write an error instead of adding it to the
                            known_hosts.
        :param known_hosts: the `known_hosts` file to store the SSH public keys.
        :raise paramiko.ssh_exception.AuthenticationException: if SSH authentication error.
        :raise paramiko.ssh_exception.SSHException: generic SSH error.
        :raise socket.error: if error at the socket level.
        """
        client = None
        try:
            client = paramiko.SSHClient()
            if not no_add_host:
                client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
            if os.path.isfile(known_hosts):
                client.load_host_keys(filename=known_hosts)

            client.connect(host.hostname, port=host.port, username=host.user, password=password,
                           key_filename=self.priv_key)

            cmd = (r'''mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
k='{0}' && if ! grep -qFx "$k" ~/.ssh/authorized_keys; then echo "$k" >> ~/.ssh/authorized_keys; fi'''
                   .format(self.pub_key_content))
            logger.debug('Run on [%s]: %s', host.hostname, cmd)
            client.exec_command(cmd.encode('utf-8'))
        finally:
            if client:
                client.close()


class Host(object):

    def __init__(self, hostname=None, port=DEFAULT_SSH_PORT, user=None, password=None):
        self.hostname = hostname
        self.port = port
        self.user = user
        self.password = password

    def __repr__(self):
        return '<{0} {1}>'.format(type(self).__name__, self.__dict__)
