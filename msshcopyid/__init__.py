from __future__ import print_function

import argparse
import getpass
import os
import sys


DEFAULT_SSH_RSA = '~/.ssh/id_rsa'
DEFAULT_SSH_DSA = '~/.ssh/id_dsa'


def main():
    mc = Main()
    mc.main()


class Main(object):

    def __init__(self):
        self.args = None

    def main(self):
        # Parse input arguments
        self.args = self.parse_args(sys.argv)

        if not self.args.identity:
            self.args.identity = os.path.expanduser(DEFAULT_SSH_RSA)
            if not os.path.exists(self.args.identity):
                self.args.identity = os.path.expanduser(DEFAULT_SSH_DSA)
                if not os.path.exists(self.args.identity):
                    print('Error: Cannot find any SSH keys in {0} and {1}.'.format(DEFAULT_SSH_RSA, DEFAULT_SSH_DSA),
                          file=sys.stderr)
                    sys.exit(1)

        if not self.args.password:
            self.args.password = getpass.getpass('Enter the common password: ')

        # Copy the SSH keys to the hosts
        for host in self.args.hosts:
            self.copy_ssh_keys(host)

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

    def copy_ssh_keys(self, host):
        # TODO: implement it
        print('I copy the SSH keys [{0}] to the host [{1}]...'.format(self.args.identity, host))
