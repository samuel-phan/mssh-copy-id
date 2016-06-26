from __future__ import print_function

import argparse
import datetime
import getpass
import logging
import os
import socket
import subprocess
import sys

import paramiko

from msshcopyid._version import __version__, __version_info__


DEFAULT_SSH_DIR = os.path.join(os.path.expanduser("~"), '.ssh')

DEFAULT_KNOWN_HOSTS = os.path.join(DEFAULT_SSH_DIR, 'known_hosts')
DEFAULT_SSH_CONFIG = os.path.join(DEFAULT_SSH_DIR, 'config')
DEFAULT_SSH_DSA = os.path.join(DEFAULT_SSH_DIR, 'id_dsa')
DEFAULT_SSH_RSA = os.path.join(DEFAULT_SSH_DIR, 'id_rsa')
DEFAULT_SSH_PORT = 22


logger = logging.getLogger(__name__)


def main():
    start_dt = datetime.datetime.now()
    mc = Main()
    mc.main()
    logger.debug('Elapsed time: %s', datetime.datetime.now() - start_dt)


class Main(object):

    def __init__(self):
        self.args = None
        self.hosts = None

        self.priv_key = None
        self.pub_key = None
        self.pub_key_content = None

    def main(self):
        self.init()

        # Check dry run
        if self.args.dry:
            logger.info('Dry run: nothing will be changed.')

        # Check the action to perform
        if self.args.add or self.args.remove:
            # Action on the known_hosts file

            # Check that known_hosts file exists
            if not os.path.exists(self.args.known_hosts):
                with open(self.args.known_hosts, 'w'):
                    pass

            if self.args.add:
                self.add_to_known_hosts(self.hosts, known_hosts=self.args.known_hosts, dry=self.args.dry)
            else:
                self.remove_from_known_hosts(self.hosts, known_hosts=self.args.known_hosts, dry=self.args.dry)

        else:
            # Copy the SSH keys to the hosts

            # Read the public key
            if not os.path.exists(self.pub_key):
                logger.error(format_error('The SSH public key [%s] does not exist.'), self.pub_key)
                sys.exit(1)
            with open(self.pub_key) as fh:
                self.pub_key_content = fh.read().strip()

            if self.args.clear:
                # Clear the hosts from the known_hosts file
                self.remove_from_known_hosts(self.hosts, known_hosts=self.args.known_hosts, dry=self.args.dry)

            self.run_copy_ssh_keys(self.hosts, known_hosts=self.args.known_hosts, dry=self.args.dry)

    def init(self):
        # Parse input arguments
        self.args = self.parse_args(sys.argv)

        # Init logging
        sh = logging.StreamHandler()
        logger.addHandler(sh)
        if self.args.verbose:
            sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.setLevel(logging.DEBUG)
        else:
            sh.setFormatter(logging.Formatter('%(message)s'))
            logger.setLevel(logging.INFO)

        # Check SSH key argument
        if not self.args.identity:
            if os.path.exists(DEFAULT_SSH_RSA):
                self.args.identity = DEFAULT_SSH_RSA
            elif os.path.exists(DEFAULT_SSH_DSA):
                self.args.identity = DEFAULT_SSH_DSA
            else:
                logger.error(format_error('Cannot find any SSH keys in %s and %s.'), DEFAULT_SSH_RSA, DEFAULT_SSH_DSA)
                sys.exit(1)
            logger.debug('Found SSH key: %s', self.args.identity)

        self.priv_key = self.args.identity
        self.pub_key = '{0}.pub'.format(self.args.identity)

        # Load ~/.ssh/config if it exists
        config = load_config()

        # Parse the hosts to extract the username if given
        self.hosts = self.parse_hosts(self.args.hosts, config)  # list of Host objects

    def parse_args(self, argv):
        parser = argparse.ArgumentParser(description='Copy SSH keys to multiple servers.')
        parser.add_argument('hosts', metavar='host', nargs='+',
                            help='the remote hosts to copy the keys to.  Syntax: [user@]hostname')
        parser.add_argument('-a', '--add', action='store_true',
                            help='don\'t copy the SSH keys, but instead, add the hosts to the "known_hosts" file')
        parser.add_argument('-A', '--no-add-host', action='store_true',
                            help='don\'t add automatically new hosts into "known_hosts" file')
        parser.add_argument('-C', '--clear', action='store_true',
                            help='clear the hosts from the "known_hosts" file before copying the SSH keys')
        parser.add_argument('-i', '--identity', help='the SSH identity file. Default: {0} or {1}'
                                                     .format(DEFAULT_SSH_RSA, DEFAULT_SSH_DSA))
        parser.add_argument('-k', '--known-hosts', default=DEFAULT_KNOWN_HOSTS,
                            help='the known_hosts file to use. Default: {0}'.format(DEFAULT_KNOWN_HOSTS))
        parser.add_argument('-n', '--dry', action='store_true', help='do a dry run. Do not change anything')
        parser.add_argument('-p', '--port', type=int, help='the SSH port for the remote hosts')
        parser.add_argument('-P', '--password',
                            help='the password to log into the remote hosts.  It is NOT SECURED to set the password '
                                 'that way, since it stays in the bash history.  Password can also be sent on the '
                                 'STDIN.')
        parser.add_argument('-R', '--remove', action='store_true',
                            help='don\'t copy the SSH keys, but instead, remove the hosts from the "known_hosts" file')
        parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode.')
        parser.add_argument('--version', action='version', version=__version__)
        return parser.parse_args(argv[1:])

    def parse_hosts(self, hosts, config):
        host_list = []  # list of Host objects
        current_user = getpass.getuser()
        for host in hosts:
            d = config.lookup(host)

            # hostname & user
            if '@' in host:
                user, hostname = host.split('@', 1)
            else:
                hostname = host
                user = d.get('user', current_user)

            # port
            port = self.args.port or d.get('port', DEFAULT_SSH_PORT)

            host_list.append(Host(hostname=hostname, port=port, user=user))

        return host_list

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

    def run_copy_ssh_keys(self, hosts, known_hosts=DEFAULT_KNOWN_HOSTS, dry=False):
        """
        Copy the SSH keys to the given hosts.

        :param hosts: the list of `Host` objects to copy the SSH keys to.
        :param known_hosts: the `known_hosts` file to store the SSH public keys.
        :param dry: perform a dry run.
        """
        for host in hosts:
            logger.info('[%s] Copy the SSH public key [%s]...', host.hostname, self.pub_key)
            if not dry:
                self.copy_ssh_keys(host, hosts, known_hosts=known_hosts)

    def copy_ssh_keys(self, host, hosts, known_hosts=DEFAULT_KNOWN_HOSTS):
        """
        Copy the SSH keys to the given host.

        :param host: the `Host` object to copy the SSH keys to.
        :param hosts: the list of `Host` objects (used to update the password if needed).
        :param known_hosts: the `known_hosts` file to store the SSH public keys.
        """
        with paramiko.SSHClient() as client:
            if not self.args.no_add_host:
                client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
            client.load_host_keys(filename=known_hosts)
            try:
                try:
                    client.connect(host.hostname, port=host.port, username=host.user, password=host.password,
                                   key_filename=self.priv_key)
                except paramiko.ssh_exception.AuthenticationException:
                    if host.password:
                        # A password was given, and it is wrong
                        raise
                    else:
                        # Ask for password & update the password for all the hosts
                        if not self.args.password:
                            self.args.password = get_password()
                        for h in hosts:
                            h.password = self.args.password

                        # Try to connect again
                        client.connect(host.hostname, port=host.port, username=host.user, password=host.password,
                                       key_filename=self.priv_key)

                if client.get_transport().is_active():
                    cmd = (r'''mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
k='{0}' && if ! grep -qFx "$k" ~/.ssh/authorized_keys; then echo "$k" >> ~/.ssh/authorized_keys; fi'''
                           .format(self.pub_key_content))
                    logger.debug('Run on [%s]: %s', host.hostname, cmd)
                    client.exec_command(cmd)

            except (paramiko.ssh_exception.SSHException, socket.error) as ex:
                logger.error(format_error(format_exception(ex)))


def load_config(config=DEFAULT_SSH_CONFIG):
    config_obj = paramiko.config.SSHConfig()
    if os.path.isfile(config):
        with open(config) as fh:
            config_obj.parse(fh)
        logger.debug('Loaded SSH configuration from [%s]', config)
    return config_obj


def get_password():
    if not sys.stdin.isatty():
        password = sys.stdin.readline().strip()
    else:
        password = getpass.getpass('Enter the password: ')
    return password


def format_error(msg):
    return 'Error: {0}'.format(msg)


def format_exception(ex):
    return '{0}: {1}'.format(type(ex).__name__, ex)


class Host(object):

    def __init__(self, hostname=None, port=DEFAULT_SSH_PORT, user=None, password=None):
        self.hostname = hostname
        self.port = port
        self.user = user
        self.password = password

    def __repr__(self):
        return '<{0} {1}>'.format(type(self).__name__, self.__dict__)
