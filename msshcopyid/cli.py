from __future__ import unicode_literals

import argparse
import datetime
import logging
import os
import socket
import sys
import traceback

import paramiko

import msshcopyid
from msshcopyid.constants import DEFAULT_KNOWN_HOSTS
from msshcopyid.constants import DEFAULT_SSH_DSA
from msshcopyid.constants import DEFAULT_SSH_RSA
from msshcopyid.log import format_exception, format_error
from msshcopyid import utils

logger = logging.getLogger(__name__)


def main():
    start_dt = datetime.datetime.now()
    mc = Main()
    mc.init()
    mc.run()
    logger.debug('Elapsed time: %s', datetime.datetime.now() - start_dt)


class Main(object):

    def __init__(self):
        self.args = None
        self.hosts = None
        self.ssh_config = None

        self.sshcopyid = None

    def init(self, argv=sys.argv):
        # Parse input arguments
        parser = self.get_parser()
        self.args = parser.parse_args(argv[1:])

        # Init logging
        self.init_log(self.args.verbose)

        # Check input arguments
        self.check_ssh_key_exists()
        self.check_add_remove_options_exclusion()

        # Get the password
        default_password = self.args.password or utils.get_password(from_stdin_only=True)

        # Load ~/.ssh/config if it exists
        self.ssh_config = utils.load_ssh_config()

        # Init `SSHCopyId` object
        self.sshcopyid = msshcopyid.SSHCopyId(priv_key=self.args.identity, ssh_config=self.ssh_config,
                                              default_password=default_password)

        # Parse the hosts to extract the username if given
        self.hosts = utils.parse_hosts(self.args.hosts, ssh_port=self.args.port, ssh_config=self.ssh_config)

    def init_log(self, verbose):
        root_logger = logging.getLogger()
        sh = logging.StreamHandler()
        root_logger.addHandler(sh)
        if verbose:
            sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s"))
            root_logger.setLevel(logging.DEBUG)
        else:
            sh.setFormatter(logging.Formatter('%(message)s'))
            root_logger.setLevel(logging.INFO)
            paramiko_logger = logging.getLogger('paramiko')
            paramiko_logger.setLevel(logging.ERROR)

    def check_ssh_key_exists(self):
        error_msg = None

        if not self.args.identity:
            if os.path.exists(DEFAULT_SSH_RSA):
                self.args.identity = DEFAULT_SSH_RSA
            elif os.path.exists(DEFAULT_SSH_DSA):
                self.args.identity = DEFAULT_SSH_DSA
            else:
                error_msg = 'Cannot find any SSH keys "{0}" and "{1}".'.format(DEFAULT_SSH_RSA, DEFAULT_SSH_DSA)
        elif not os.path.exists(self.args.identity):
            error_msg = 'Cannot find the SSH key "{0}".'.format(self.args.identity)

        if error_msg:
            logger.error(format_error(error_msg))
            sys.exit(1)
        else:
            logger.debug('Found SSH key: %s', self.args.identity)

    def check_add_remove_options_exclusion(self):
        if self.args.add and self.args.remove:
            logger.error(format_error('argument -a/--add not allowed with argument -R/--remove.'))
            sys.exit(1)

    def get_parser(self):
        parser = argparse.ArgumentParser(description='Copy SSH keys to multiple servers.')
        parser.add_argument('hosts', metavar='host', nargs='+',
                            help='the remote hosts to copy the keys to.  Syntax: [user@]hostname')
        parser.add_argument('-k', '--known-hosts', default=DEFAULT_KNOWN_HOSTS,
                            help='the known_hosts file to use. Default: ~/.ssh/known_hosts')
        parser.add_argument('-n', '--dry', action='store_true', help='do a dry run. Do not change anything')
        parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose mode.')
        parser.add_argument('--version', action='version', version=msshcopyid.__version__)

        copy_group = parser.add_argument_group('Copy SSH keys')
        copy_group.add_argument('-A', '--no-add-host', action='store_true',
                                help='don\'t add automatically new hosts into "known_hosts" file')
        copy_group.add_argument('-C', '--clear', action='store_true',
                                help='clear the hosts from the "known_hosts" file before copying the SSH keys')
        copy_group.add_argument('-i', '--identity', help='the SSH identity file. Default: {0} or {1}'
                                                     .format(DEFAULT_SSH_RSA, DEFAULT_SSH_DSA))
        copy_group.add_argument('-p', '--port', type=int, help='the SSH port for the remote hosts')
        copy_group.add_argument('-P', '--password',
                                help='the password to log into the remote hosts.  It is NOT SECURED to set the '
                                     'password that way, since it stays in the bash history. Password can also be sent '
                                     'on the STDIN.')

        known_host_group = parser.add_argument_group('Manage the "known_host" file only')
        known_host_group.add_argument('-a', '--add', action='store_true',
                                      help='don\'t copy the SSH keys, but instead, add the hosts to the "known_hosts" '
                                           'file')
        known_host_group.add_argument('-R', '--remove', action='store_true',
                                      help='don\'t copy the SSH keys, but instead, remove the hosts from the '
                                           '"known_hosts" file')
        return parser

    def run(self):
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
                self.sshcopyid.add_to_known_hosts(self.hosts, known_hosts=self.args.known_hosts, dry=self.args.dry)
            else:
                self.sshcopyid.remove_from_known_hosts(self.hosts, known_hosts=self.args.known_hosts, dry=self.args.dry)

        else:
            # Copy the SSH keys to the hosts
            if self.args.clear:
                # Clear the hosts from the known_hosts file
                self.sshcopyid.remove_from_known_hosts(self.hosts, known_hosts=self.args.known_hosts, dry=self.args.dry)

            # Read the public key
            if not self.sshcopyid.pub_key_content:
                self.sshcopyid.read_pub_key()

            try:
                self.copy_ssh_keys_to_hosts(self.hosts, known_hosts=self.args.known_hosts, dry=self.args.dry)
            except Exception as ex:
                logger.error(format_error(format_exception(ex)))

    def copy_ssh_keys_to_hosts(self, hosts, known_hosts=DEFAULT_KNOWN_HOSTS, dry=False):
        """
        Copy the SSH keys to the given hosts.

        :param hosts: the list of `Host` objects to copy the SSH keys to.
        :param known_hosts: the `known_hosts` file to store the SSH public keys.
        :param dry: perform a dry run.
        """
        for host in hosts:
            logger.info('[%s] Copy the SSH public key [%s]...', host.hostname, self.sshcopyid.pub_key)
            if not dry:
                try:
                    self.copy_ssh_keys_to_host(host, known_hosts=known_hosts)
                except (paramiko.ssh_exception.SSHException, socket.error) as ex:
                    logger.error(format_error(format_exception(ex)))
                    logger.debug(traceback.format_exc())

    def copy_ssh_keys_to_host(self, host, known_hosts=DEFAULT_KNOWN_HOSTS):
        """
        Copy the SSH keys to the given host.

        :param host: the `Host` object to copy the SSH keys to.
        :param known_hosts: the `known_hosts` file to store the SSH public keys.
        """
        password = host.password or self.sshcopyid.default_password
        try:
            self.sshcopyid.copy_ssh_keys_to_host(host, password=password, no_add_host=self.args.no_add_host,
                                                 known_hosts=known_hosts)

        except paramiko.ssh_exception.AuthenticationException:
            if password:
                # A password was given, and it is wrong
                raise
            else:
                # Ask for password
                password = utils.get_password()
                self.sshcopyid.default_password = password

                # Try to connect again
                self.sshcopyid.copy_ssh_keys_to_host(host, password=password, no_add_host=self.args.no_add_host,
                                                     known_hosts=known_hosts)
