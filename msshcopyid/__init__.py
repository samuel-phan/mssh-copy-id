from __future__ import print_function

import argparse
import getpass
import os
import sys

import paramiko


DEFAULT_SSH_DIR = os.path.join(os.path.expanduser("~"), '.ssh')
DEFAULT_SSH_RSA = os.path.join(DEFAULT_SSH_DIR, 'id_rsa')
DEFAULT_SSH_DSA = os.path.join(DEFAULT_SSH_DIR, 'id_dsa')
DEFAULT_KNOWN_HOSTS = os.path.join(DEFAULT_SSH_DIR, 'known_hosts')


def main():
    mc = Main()
    mc.main()


class Main(object):

    def __init__(self):
        self.args = None
        self.pub_key = None
        self.pub_key_content = None

    def main(self):
        # Parse input arguments
        self.args = self.parse_args(sys.argv)

        # Check SSH key argument
        if not self.args.identity:
            self.args.identity = os.path.expanduser(DEFAULT_SSH_RSA)
            if not os.path.exists(self.args.identity):
                self.args.identity = os.path.expanduser(DEFAULT_SSH_DSA)
                if not os.path.exists(self.args.identity):
                    print('Error: Cannot find any SSH keys in {0} and {1}.'.format(DEFAULT_SSH_RSA, DEFAULT_SSH_DSA),
                          file=sys.stderr)
                    sys.exit(1)
        self.pub_key = '{0}.pub'.format(self.args.identity)

        # Read the public key
        with open(self.pub_key) as fh:
            self.pub_key_content = fh.read().strip()

        # Check that a password is given
        if not self.args.password:
            if not sys.stdin.isatty():
                self.args.password = sys.stdin.readline().strip()
            else:
                self.args.password = getpass.getpass('Enter the common password: ')

        # Copy the SSH keys to the hosts
        for host in self.args.hosts:
            # TODO: add the username
            self.copy_ssh_keys(host, 'root', self.args.password)

    def parse_args(self, argv):
        parser = argparse.ArgumentParser(description='Massively copy SSH keys.')
        parser.add_argument('hosts', metavar='host', nargs='+',
                            help='the remote hosts to copy the keys to.  Syntax: [user@]hostname')
        parser.add_argument('-i', '--identity', help='the SSH identity file. Default: {0} or {1}'
                                                     .format(DEFAULT_SSH_RSA, DEFAULT_SSH_DSA))
        parser.add_argument('-P', '--password',
                            help='the password to log into the remote hosts.  It is NOT SECURED to set the password '
                                 'that way, since it stays in the bash history.  Password can also be sent on the '
                                 'STDIN.')
        return parser.parse_args(argv[1:])

    def copy_ssh_keys(self, host, username, password):
        print('Copying the SSH public key [{0}] to the host [{1}]...'.format(self.pub_key, host))
        with paramiko.SSHClient() as client:
            client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
            client.load_host_keys(filename=DEFAULT_KNOWN_HOSTS)
            client.connect(host, username=username, password=password, key_filename='/home/sphan/.ssh/id_rsa')
            cmd = r'''mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
k='{0}' && if ! grep -qFx "$k" ~/.ssh/authorized_keys; then echo "$k" >> ~/.ssh/authorized_keys; fi'''\
                    .format(self.pub_key_content)
            client.exec_command(cmd)
