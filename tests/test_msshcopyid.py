from __future__ import unicode_literals

import subprocess
import sys

import paramiko
from mock import call, MagicMock, mock_open, patch
import unittest2 as unittest

import msshcopyid


class TestSSHCopyId(unittest.TestCase):

    def setUp(self):
        self.sshcopyid = msshcopyid.SSHCopyId()

    def test_set_pub_key_none(self):
        self.sshcopyid.set_pub_key(None)
        self.assertEqual(self.sshcopyid.pub_key, None)

    def test_set_pub_key_none_no_priv_key(self):
        self.sshcopyid.priv_key = None
        self.sshcopyid.set_pub_key(None)
        self.assertEqual(self.sshcopyid.pub_key, None)

    def test_set_pub_key_none_default_priv_key(self):
        self.sshcopyid.priv_key = '/home/user/.ssh/id_rsa'
        self.sshcopyid.set_pub_key(None)
        self.assertEqual(self.sshcopyid.pub_key, '/home/user/.ssh/id_rsa.pub')

    def test_set_pub_key(self):
        self.sshcopyid.priv_key = '/home/user/.ssh/id_rsa'
        self.sshcopyid.set_pub_key('/home/user/.ssh/pub_key_file')
        self.assertEqual(self.sshcopyid.pub_key, '/home/user/.ssh/pub_key_file')

    @patch('msshcopyid.os.path.exists', return_value=True)
    def test_read_pub_key_file_exists(self, mock_exists):
        pub_key_content = 'pub key content'
        self.sshcopyid.pub_key = '/home/user/.ssh/id_rsa.pub'

        with patch('msshcopyid.open', mock_open(read_data=pub_key_content)) as mock_bopen:
            self.sshcopyid.read_pub_key()

        mock_exists.assert_called_once_with(self.sshcopyid.pub_key)
        self.sshcopyid.pub_key_content = pub_key_content

    @patch('msshcopyid.os.path.exists', return_value=False)
    def test_read_pub_key_file_not_exist(self, mock_exists):
        self.sshcopyid.pub_key = '/home/user/.ssh/id_rsa.pub'

        with self.assertRaises(SystemExit) as exctx:
            self.sshcopyid.read_pub_key()

        # Behavior is different between Python 2.6 and 2.7 when catching SystemExit
        if sys.version_info < (2, 7):
            self.assertEquals(exctx.exception, 1)
        else:
            self.assertEquals(exctx.exception.args, (1,))

        mock_exists.assert_called_once_with(self.sshcopyid.pub_key)

    @patch('msshcopyid.subprocess.Popen')
    def test_add_to_known_hosts(self, mock_popen):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = MagicMock()

        server1_ssh_key = 'server1 ssh-rsa KRDZhqpguSRxeiqLseaD'
        server2_ssh_key = 'server2 ssh-rsa AAAAB3NzaC1yc2EAAAAB'
        server3_ssh_key = 'server3 ssh-rsa O2gDXC6h6QDXCaHo6pOH'
        server4_ssh_key = 'server4 ssh-rsa hdHWpZ8fDvQArTUFCfgU'

        keyscans = [server2_ssh_key,
                    server3_ssh_key,
                    server1_ssh_key]
        mock_popen.return_value.communicate.return_value = ('\n'.join(keyscans), MagicMock())

        known_hosts_content = [server1_ssh_key,
                               server4_ssh_key]
        mock_bopen = mock_open(read_data='\n'.join(known_hosts_content))

        with patch('msshcopyid.open', mock_bopen):
            self.sshcopyid.add_to_known_hosts(hosts, known_hosts=known_hosts, dry=False)

        mock_bopen.return_value.writelines.assert_any_call(['{0}\n'.format(k)
                                                            for k in (server2_ssh_key, server3_ssh_key)])

    @patch('msshcopyid.subprocess.Popen')
    def test_add_to_known_hosts_dry(self, mock_popen):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = MagicMock()

        server1_ssh_key = 'server1 ssh-rsa KRDZhqpguSRxeiqLseaD'
        server2_ssh_key = 'server2 ssh-rsa AAAAB3NzaC1yc2EAAAAB'
        server3_ssh_key = 'server3 ssh-rsa O2gDXC6h6QDXCaHo6pOH'
        server4_ssh_key = 'server4 ssh-rsa hdHWpZ8fDvQArTUFCfgU'

        keyscans = [server2_ssh_key,
                    server3_ssh_key,
                    server1_ssh_key]
        mock_popen.return_value.communicate.return_value = ('\n'.join(keyscans), MagicMock())

        known_hosts_content = [server1_ssh_key,
                               server4_ssh_key]
        mock_bopen = mock_open(read_data='\n'.join(known_hosts_content))

        with patch('msshcopyid.open', mock_bopen):
            self.sshcopyid.add_to_known_hosts(hosts, known_hosts=known_hosts, dry=True)

        mock_bopen.return_value.writelines.assert_not_called()

    @patch('msshcopyid.subprocess.check_call')
    def test_remove_from_known_hosts(self, mock_check_call):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = '/path/to/known_hosts'

        self.sshcopyid.remove_from_known_hosts(hosts, known_hosts=known_hosts, dry=False)

        for host in hosts:
            cmd = ['ssh-keygen', '-f', known_hosts, '-R', host.hostname]
            mock_check_call.assert_any_call(cmd)

    @patch('msshcopyid.subprocess.check_call')
    def test_remove_from_known_hosts_dry(self, mock_check_call):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = '/path/to/known_hosts'

        self.sshcopyid.remove_from_known_hosts(hosts, known_hosts=known_hosts, dry=True)

        mock_check_call.assert_not_called()

    @patch('msshcopyid.format_exception')
    @patch('msshcopyid.format_error')
    @patch('msshcopyid.subprocess.check_call')
    @patch('msshcopyid.logger')
    def test_remove_from_known_hosts_error(self, mock_logger, mock_check_call, mock_format_error,
                                           mock_format_exception):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = '/path/to/known_hosts'
        cmds = []
        check_call_side_effect = []
        for host in hosts:
            cmd = ['ssh-keygen', '-f', known_hosts, '-R', host.hostname]
            cmds.append(cmd)
            check_call_side_effect.append(subprocess.CalledProcessError(1, cmd))
        mock_check_call.side_effect = check_call_side_effect

        self.sshcopyid.remove_from_known_hosts(hosts, known_hosts=known_hosts, dry=False)

        for cmd, ex in zip(cmds, check_call_side_effect):
            mock_check_call.assert_any_call(cmd)
            mock_logger.error.assert_any_call(mock_format_error(mock_format_exception(ex)))

    @patch('msshcopyid.paramiko.client.AutoAddPolicy')
    @patch('msshcopyid.paramiko.SSHClient')
    def test_copy_ssh_keys_to_host(self, mock_ssh_client, mock_auto_add_policy):
        host = msshcopyid.Host(hostname='server1', port=12345, user='a_user', password='a_password')
        known_hosts = MagicMock()

        self.sshcopyid.priv_key = MagicMock()
        self.sshcopyid.pub_key_content = 'ssh-rsa AAAAB3NzaC1yc2EAAAAD'
        password = None

        self.sshcopyid.copy_ssh_keys_to_host(host, password=password, no_add_host=False, known_hosts=known_hosts)

        client = mock_ssh_client.return_value.__enter__.return_value
        client.set_missing_host_key_policy.assert_called_once_with(mock_auto_add_policy.return_value)
        client.connect.assert_called_once_with(host.hostname, port=host.port, username=host.user,
                                               password=password, key_filename=self.sshcopyid.priv_key)
        cmd = (r'''mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
k='{0}' && if ! grep -qFx "$k" ~/.ssh/authorized_keys; then echo "$k" >> ~/.ssh/authorized_keys; fi'''
               .format(self.sshcopyid.pub_key_content))
        client.exec_command.assert_called_once_with(cmd)

    @patch('msshcopyid.paramiko.client.AutoAddPolicy')
    @patch('msshcopyid.paramiko.SSHClient')
    def test_copy_ssh_keys_to_host_no_add_host(self, mock_ssh_client, mock_auto_add_policy):
        host = msshcopyid.Host(hostname='server1', port=12345, user='a_user', password='a_password')
        known_hosts = MagicMock()
        client = mock_ssh_client.return_value.__enter__.return_value
        ssh_exception = paramiko.ssh_exception.SSHException('ssh exception')
        client.connect.side_effect = ssh_exception

        self.sshcopyid.priv_key = MagicMock()
        self.sshcopyid.pub_key_content = 'ssh-rsa AAAAB3NzaC1yc2EAAAAD'
        password = None

        with self.assertRaises(paramiko.ssh_exception.SSHException) as exctx:
            self.sshcopyid.copy_ssh_keys_to_host(host, password=password, no_add_host=True, known_hosts=known_hosts)
            self.assertEqual(exctx.exception, ssh_exception)

        client = mock_ssh_client.return_value.__enter__.return_value
        client.set_missing_host_key_policy.assert_not_called()
        client.connect.assert_called_once_with(host.hostname, port=host.port, username=host.user,
                                               password=password, key_filename=self.sshcopyid.priv_key)
        client.exec_command.assert_not_called()

    @patch('msshcopyid.paramiko.client.AutoAddPolicy')
    @patch('msshcopyid.paramiko.SSHClient')
    def test_copy_ssh_keys_to_host_wrong_password(self, mock_ssh_client, mock_auto_add_policy):
        host = msshcopyid.Host(hostname='server1', port=12345, user='a_user', password='a_password')
        known_hosts = MagicMock()
        client = mock_ssh_client.return_value.__enter__.return_value
        auth_exception = paramiko.ssh_exception.AuthenticationException('authentication exception')
        client.connect.side_effect = auth_exception

        self.sshcopyid.priv_key = MagicMock()
        self.sshcopyid.pub_key_content = 'ssh-rsa AAAAB3NzaC1yc2EAAAAD'
        password = None

        with self.assertRaises(paramiko.ssh_exception.SSHException) as exctx:
            self.sshcopyid.copy_ssh_keys_to_host(host, password=password, no_add_host=True, known_hosts=known_hosts)
            self.assertEqual(exctx.exception, auth_exception)

        client = mock_ssh_client.return_value.__enter__.return_value
        client.set_missing_host_key_policy.assert_not_called()
        client.connect.assert_called_once_with(host.hostname, port=host.port, username=host.user,
                                               password=password, key_filename=self.sshcopyid.priv_key)
        client.exec_command.assert_not_called()
