# encoding: utf-8
import os
import re
import sys
import paramiko

#def main():
#    print('mssh-copy-id entry point')

# PS : y a pas des cons qui l'ont deja fait ?
# https://pypi.python.org/pypi/ssh-deploy-key/0.1.1

# Constants
hostFile = '/etc/hosts'
# todo: test file exists/readable ?
keyfile = os.getenv('HOME')+'/.ssh/id_rsa.pub'
# todo: notre clé publique est toujours la? ... il y a d'autre types de clés possible, faire mieux....

# todo: write def usage()
# todo: parse args
# test values
hostExp = 'localh*'
username = 'toto'
port = 22

# Retrieve matching hosts/ip from hosts file
info = 'matching hosts : '
hosts = []
for line in open(hostFile).readlines():
    lineWithoutEOF = line.splitlines()[0]
    lineWithoutComments = lineWithoutEOF.split('#')[0]
    for host in lineWithoutComments.split():
        try:
            if re.match(hostExp, host):
                hosts.append(host)
                info += host
        except re.error as e:
            print('ERROR: Host shall be a regular expression.')
            sys.exit(1)
print(info)

# retrieve user key
if not os.path.isfile(keyfile):
    print('ERROR: No public key file '+keyfile)
    sys.exit(1)
# read all lines, keep first, remove EOF,
userkey = open(keyfile).readlines()[0].splitlines()[0]
print('key:'+userkey)

# ask for password
password = raw_input('password for remote user '+username+':')

# manual ssh-copy-id requests - search/find a best/clean way to do this... !!??
for host in hosts:
    client = paramiko.Transport((host, port))
    client.connect(username=username, password=password)
    command = 'mkdir -p $HOME/.ssh; echo "' + userkey + '" >> $HOME/.ssh/authorized_keys'
    session = client.open_channel(kind='session')
    session.exec_command(command)
    while True:
        if session.exit_status_ready():
            break
    print 'exit status: ', session.recv_exit_status()
    # todo: compute return code...


