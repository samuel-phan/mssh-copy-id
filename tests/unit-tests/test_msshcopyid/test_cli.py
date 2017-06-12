from __future__ import unicode_literals

import socket
import sys

from mock import MagicMock, mock_open, patch
import paramiko
import unittest2 as unittest

import msshcopyid.cli
from msshcopyid.constants import DEFAULT_SSH_DSA
from msshcopyid.constants import DEFAULT_SSH_RSA


class TestMain(unittest.TestCase):

    def setUp(self):
        self.main = msshcopyid.cli.Main()

    @patch('msshcopyid.cli.logging')
    def test_init_log_no_verbose(self, mock_logging):
        root_logger = MagicMock()
        mock_logging.getLogger.side_effect = [root_logger, MagicMock()]

        self.main.init_log(False)

        root_logger.setLevel.assert_called_once_with(mock_logging.INFO)

    @patch('msshcopyid.cli.logging')
    def test_init_log_verbose(self, mock_logging):
        root_logger = mock_logging.getLogger.return_value

        self.main.init_log(True)

        root_logger.setLevel.assert_called_once_with(mock_logging.DEBUG)

    @patch('msshcopyid.cli.os.path.exists')
    def test_check_ssh_key_exists_ok(self, mock_exists):
        self.main.args = MagicMock()
        self.main.args.identity = '/home/user/.ssh/my_ssh_key'

        exists_values = {'/home/user/.ssh/my_ssh_key': True,
                         DEFAULT_SSH_RSA: False,
                         DEFAULT_SSH_DSA: False}
        mock_exists.side_effect = lambda key_file: exists_values[key_file]

        self.main.check_ssh_key_exists()

        self.main.args.identity = '/home/user/.ssh/my_ssh_key'

    @patch('msshcopyid.cli.os.path.exists')
    def test_check_ssh_key_exists_default_rsa(self, mock_exists):
        self.main.args = MagicMock()
        self.main.args.identity = None

        exists_values = {DEFAULT_SSH_RSA: True,
                         DEFAULT_SSH_DSA: False}
        mock_exists.side_effect = lambda key_file: exists_values[key_file]

        self.main.check_ssh_key_exists()

        self.main.args.identity = DEFAULT_SSH_RSA

    @patch('msshcopyid.cli.os.path.exists')
    def test_check_ssh_key_exists_default_dsa(self, mock_exists):
        self.main.args = MagicMock()
        self.main.args.identity = None

        exists_values = {DEFAULT_SSH_RSA: False,
                         DEFAULT_SSH_DSA: True}
        mock_exists.side_effect = lambda key_file: exists_values[key_file]

        self.main.check_ssh_key_exists()

        self.main.args.identity = DEFAULT_SSH_DSA

    @patch('msshcopyid.cli.os.path.exists')
    def test_check_ssh_key_exists_no_default_found(self, mock_exists):
        self.main.args = MagicMock()
        self.main.args.identity = None

        exists_values = {DEFAULT_SSH_RSA: False,
                         DEFAULT_SSH_DSA: False}
        mock_exists.side_effect = lambda key_file: exists_values[key_file]

        with self.assertRaises(SystemExit) as exctx:
            self.main.check_ssh_key_exists()

        # Behavior is different between Python 2.6 and 2.7 when catching SystemExit
        if sys.version_info < (2, 7):
            self.assertEquals(exctx.exception, 1)
        else:
            self.assertEquals(exctx.exception.args, (1,))

    @patch('msshcopyid.cli.os.path.exists')
    def test_check_ssh_key_exists_not_exists(self, mock_exists):
        self.main.args = MagicMock()
        self.main.args.identity = '/home/user/.ssh/my_ssh_key'

        exists_values = {'/home/user/.ssh/my_ssh_key': False,
                         DEFAULT_SSH_RSA: False,
                         DEFAULT_SSH_DSA: False}
        mock_exists.side_effect = lambda key_file: exists_values[key_file]

        with self.assertRaises(SystemExit) as exctx:
            self.main.check_ssh_key_exists()

        # Behavior is different between Python 2.6 and 2.7 when catching SystemExit
        if sys.version_info < (2, 7):
            self.assertEquals(exctx.exception, 1)
        else:
            self.assertEquals(exctx.exception.args, (1,))

    @patch('msshcopyid.cli.open', new_callable=mock_open)
    @patch('msshcopyid.cli.os.path.exists', return_value=False)
    def test_run_add(self, mock_exists, mock_bopen):
        sshcopyid = MagicMock()
        self.main.sshcopyid = sshcopyid
        self.main.hosts = MagicMock()
        self.main.args = MagicMock()
        self.main.args.add = True
        self.main.args.remove = False

        self.main.run()

        mock_bopen.assert_called_once_with(self.main.args.known_hosts, 'w')
        sshcopyid.add_to_known_hosts.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                             dry=self.main.args.dry)

    @patch('msshcopyid.cli.open', new_callable=mock_open)
    @patch('msshcopyid.cli.os.path.exists', return_value=False)
    def test_run_remove(self, mock_exists, mock_bopen):
        sshcopyid = MagicMock()
        self.main.sshcopyid = sshcopyid
        self.main.hosts = MagicMock()
        self.main.args = MagicMock()
        self.main.args.add = False
        self.main.args.remove = True

        self.main.run()

        mock_bopen.assert_called_once_with(self.main.args.known_hosts, 'w')
        sshcopyid.remove_from_known_hosts.assert_called_once_with(self.main.hosts,
                                                                  known_hosts=self.main.args.known_hosts,
                                                                  dry=self.main.args.dry)

    @patch('msshcopyid.cli.Main.copy_ssh_keys_to_hosts')
    def test_run_copy_ssh_keys_to_hosts_no_clear_hosts(self, mock_copy_ssh_keys_to_hosts):
        sshcopyid = MagicMock()
        self.main.sshcopyid = sshcopyid
        self.main.hosts = MagicMock()
        self.main.args = MagicMock()
        self.main.args.add = False
        self.main.args.remove = False
        self.main.args.clear = False

        self.main.run()

        sshcopyid.remove_from_known_hosts.assert_not_called()
        mock_copy_ssh_keys_to_hosts.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                            dry=self.main.args.dry)

    @patch('msshcopyid.cli.Main.copy_ssh_keys_to_hosts')
    def test_run_copy_ssh_keys_to_hosts_clear_hosts(self, mock_copy_ssh_keys_to_hosts):
        sshcopyid = MagicMock()
        self.main.sshcopyid = sshcopyid
        self.main.hosts = MagicMock()
        self.main.args = MagicMock()
        self.main.args.add = False
        self.main.args.remove = False
        self.main.args.clear = True

        self.main.run()

        sshcopyid.remove_from_known_hosts.assert_called_once_with(self.main.hosts,
                                                                  known_hosts=self.main.args.known_hosts,
                                                                  dry=self.main.args.dry)
        mock_copy_ssh_keys_to_hosts.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                            dry=self.main.args.dry)

    @patch('msshcopyid.cli.format_exception')
    @patch('msshcopyid.cli.format_error')
    @patch('msshcopyid.cli.logger')
    @patch('msshcopyid.cli.Main.copy_ssh_keys_to_hosts')
    def test_run_copy_ssh_keys_to_hosts_catch_exception(self, mock_copy_ssh_keys_to_hosts, mock_logger,
                                                        mock_format_error, mock_format_exception):
        sshcopyid = MagicMock()
        self.main.sshcopyid = sshcopyid
        self.main.hosts = MagicMock()
        self.main.args = MagicMock()
        self.main.args.add = False
        self.main.args.remove = False
        self.main.args.clear = True
        exception = Exception('copy ssh exception')
        mock_copy_ssh_keys_to_hosts.side_effect = exception

        self.main.run()

        sshcopyid.remove_from_known_hosts.assert_called_once_with(self.main.hosts,
                                                                  known_hosts=self.main.args.known_hosts,
                                                                  dry=self.main.args.dry)
        mock_copy_ssh_keys_to_hosts.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                            dry=self.main.args.dry)
        mock_logger.error.assert_called_once_with(mock_format_error.return_value)
        mock_format_error.assert_called_once_with(mock_format_exception.return_value)
        mock_format_exception.assert_called_once_with(exception)

    @patch('msshcopyid.cli.Main.copy_ssh_keys_to_host')
    def test_copy_ssh_keys_to_hosts_not_dry(self, mock_copy_ssh_keys_to_host):
        host1 = msshcopyid.Host(hostname='server1')
        host2 = msshcopyid.Host(hostname='server2')
        host3 = msshcopyid.Host(hostname='server3')
        hosts = [host1, host2, host3]
        known_hosts = MagicMock()
        dry = False

        self.main.sshcopyid = MagicMock()

        self.main.copy_ssh_keys_to_hosts(hosts, known_hosts=known_hosts, dry=dry)

        mock_copy_ssh_keys_to_host.assert_any_call(host1, known_hosts=known_hosts)
        mock_copy_ssh_keys_to_host.assert_any_call(host2, known_hosts=known_hosts)
        mock_copy_ssh_keys_to_host.assert_any_call(host3, known_hosts=known_hosts)

    @patch('msshcopyid.cli.Main.copy_ssh_keys_to_host')
    def test_copy_ssh_keys_to_hosts_dry(self, mock_copy_ssh_keys_to_host):
        host1 = msshcopyid.Host(hostname='server1')
        host2 = msshcopyid.Host(hostname='server2')
        host3 = msshcopyid.Host(hostname='server3')
        hosts = [host1, host2, host3]
        known_hosts = MagicMock()
        dry = True

        self.main.sshcopyid = MagicMock()

        self.main.copy_ssh_keys_to_hosts(hosts, known_hosts=known_hosts, dry=dry)

        mock_copy_ssh_keys_to_host.assert_not_called()

    @patch('msshcopyid.cli.format_exception')
    @patch('msshcopyid.cli.format_error')
    @patch('msshcopyid.cli.logger')
    @patch('msshcopyid.cli.Main.copy_ssh_keys_to_host')
    def test_copy_ssh_keys_to_hosts_exception(self, mock_copy_ssh_keys_to_host, mock_logger, mock_format_error,
                                              mock_format_exception):
        host1 = msshcopyid.Host(hostname='server1')
        host2 = msshcopyid.Host(hostname='server2')
        host3 = msshcopyid.Host(hostname='server3')
        hosts = [host1, host2, host3]
        known_hosts = MagicMock()
        dry = False

        self.main.sshcopyid = MagicMock()
        ssh_exception = paramiko.ssh_exception.SSHException('ssh exception')
        socket_error = socket.error('socket error')
        mock_copy_ssh_keys_to_host.side_effect = [ssh_exception, socket_error, None]

        self.main.copy_ssh_keys_to_hosts(hosts, known_hosts=known_hosts, dry=dry)

        mock_copy_ssh_keys_to_host.assert_any_call(host1, known_hosts=known_hosts)
        mock_copy_ssh_keys_to_host.assert_any_call(host2, known_hosts=known_hosts)
        mock_copy_ssh_keys_to_host.assert_any_call(host3, known_hosts=known_hosts)

        mock_logger.error.assert_any_call(mock_format_error.return_value)
        mock_format_error.assert_any_call(mock_format_exception.return_value)
        mock_format_exception.assert_any_call(ssh_exception)
        mock_format_exception.assert_any_call(socket_error)

    @patch('msshcopyid.utils.get_password')
    def test_copy_ssh_keys_to_host_prompt_password(self, mock_get_password):
        host = msshcopyid.Host(hostname='server1')
        known_hosts = MagicMock()

        self.main.args = MagicMock()
        sshcopyid = MagicMock()
        sshcopyid.default_password = None
        sshcopyid.copy_ssh_keys_to_host.side_effect = [paramiko.ssh_exception.AuthenticationException, None]
        self.main.sshcopyid = sshcopyid

        self.main.copy_ssh_keys_to_host(host, known_hosts=known_hosts)

        sshcopyid.copy_ssh_keys_to_host.assert_any_call(host, password=None, no_add_host=self.main.args.no_add_host,
                                                        known_hosts=known_hosts)
        sshcopyid.copy_ssh_keys_to_host.assert_any_call(host, password=mock_get_password.return_value,
                                                        no_add_host=self.main.args.no_add_host, known_hosts=known_hosts)
        self.assertEqual(sshcopyid.default_password, mock_get_password.return_value)

    def test_copy_ssh_keys_to_host_using_host_password_authentication_exception(self):
        host = msshcopyid.Host(hostname='server1', password='server1 password')
        known_hosts = MagicMock()

        self.main.args = MagicMock()
        sshcopyid = MagicMock()
        sshcopyid.default_password = 'default password'
        sshcopyid.copy_ssh_keys_to_host.side_effect = paramiko.ssh_exception.AuthenticationException
        self.main.sshcopyid = sshcopyid

        with self.assertRaises(paramiko.ssh_exception.AuthenticationException) as exctx:
            self.main.copy_ssh_keys_to_host(host, known_hosts=known_hosts)

        sshcopyid.copy_ssh_keys_to_host.assert_called_once_with(host, password='server1 password',
                                                                no_add_host=self.main.args.no_add_host,
                                                                known_hosts=known_hosts)
        self.assertEqual(sshcopyid.default_password, 'default password')

    def test_copy_ssh_keys_to_host_using_default_password_authentication_exception(self):
        host = msshcopyid.Host(hostname='server1')
        known_hosts = MagicMock()

        self.main.args = MagicMock()
        sshcopyid = MagicMock()
        sshcopyid.default_password = 'default password'
        sshcopyid.copy_ssh_keys_to_host.side_effect = paramiko.ssh_exception.AuthenticationException
        self.main.sshcopyid = sshcopyid

        with self.assertRaises(paramiko.ssh_exception.AuthenticationException) as exctx:
            self.main.copy_ssh_keys_to_host(host, known_hosts=known_hosts)

        sshcopyid.copy_ssh_keys_to_host.assert_called_once_with(host, password='default password',
                                                                no_add_host=self.main.args.no_add_host,
                                                                known_hosts=known_hosts)
        self.assertEqual(sshcopyid.default_password, 'default password')
