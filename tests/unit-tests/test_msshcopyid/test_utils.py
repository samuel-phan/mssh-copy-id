from __future__ import unicode_literals

from mock import MagicMock, mock_open, patch
import unittest2 as unittest

import msshcopyid.cli


class TestUtilsModule(unittest.TestCase):

    @patch('msshcopyid.utils.sys.stdin.readline')
    @patch('msshcopyid.utils.sys.stdin.isatty', return_value=False)
    def test_get_password_has_stdin_from_stdin_only_false(self, mock_isatty, mock_readline):
        result = msshcopyid.utils.get_password(from_stdin_only=False)
        self.assertEqual(result, mock_readline.return_value.strip.return_value)
        mock_isatty.assert_called_once_with()

    @patch('msshcopyid.utils.getpass.getpass')
    @patch('msshcopyid.utils.sys.stdin.isatty', return_value=True)
    def test_get_password_no_stdin_from_stdin_only_false(self, mock_isatty, mock_getpass):
        result = msshcopyid.utils.get_password(from_stdin_only=False)
        self.assertEqual(result, mock_getpass.return_value)
        mock_isatty.assert_called_once_with()
        mock_getpass.assert_called_once_with('Enter the password: ')

    @patch('msshcopyid.utils.sys.stdin.isatty', return_value=True)
    def test_get_password_no_stdin_from_stdin_only_true(self, mock_isatty):
        result = msshcopyid.utils.get_password(from_stdin_only=True)
        self.assertEqual(result, None)
        mock_isatty.assert_called_once_with()

    @patch('msshcopyid.utils.open', new_callable=mock_open)
    @patch('msshcopyid.utils.os.path.isfile', return_value=True)
    @patch('msshcopyid.utils.paramiko.config.SSHConfig')
    def test_load_ssh_config_exists(self, mock_ssh_config, mock_isfile, mock_bopen):
        ssh_config = mock_ssh_config.return_value

        result = msshcopyid.utils.load_ssh_config()

        self.assertEqual(result, ssh_config)
        ssh_config.parse.assert_called_once_with(mock_bopen.return_value)

    @patch('msshcopyid.utils.open', new_callable=mock_open)
    @patch('msshcopyid.utils.os.path.isfile', return_value=False)
    @patch('msshcopyid.utils.paramiko.config.SSHConfig')
    def test_load_ssh_config_not_exist(self, mock_ssh_config, mock_isfile, mock_bopen):
        ssh_config = mock_ssh_config.return_value

        result = msshcopyid.utils.load_ssh_config()

        self.assertEqual(result, ssh_config)
        ssh_config.parse.assert_not_called()

    @patch('msshcopyid.utils.getpass.getuser', return_value='me')
    def test_parse_hosts_no_port_with_no_ssh_config(self, mock_getuser):
        hosts = ['server1', 'server2', 'john@server3', 'doe@server4']

        result = msshcopyid.utils.parse_hosts(hosts, ssh_port=None, ssh_config=None)

        self.assertEqual(result[0].__dict__, {'hostname': 'server1', 'port': 22, 'user': 'me', 'password': None})
        self.assertEqual(result[1].__dict__, {'hostname': 'server2', 'port': 22, 'user': 'me', 'password': None})
        self.assertEqual(result[2].__dict__, {'hostname': 'server3', 'port': 22, 'user': 'john', 'password': None})
        self.assertEqual(result[3].__dict__, {'hostname': 'server4', 'port': 22, 'user': 'doe', 'password': None})

    @patch('msshcopyid.utils.getpass.getuser', return_value='me')
    def test_parse_hosts_no_port_with_ssh_config(self, mock_getuser):
        hosts = ['server1', 'server2', 'john@server3', 'doe@server4']
        ssh_config = MagicMock()
        ssh_config.lookup = MagicMock(side_effect=[{'hostname': 'server1'},
                                               {'hostname': 'server2', 'user': 'alice', 'port': 987},
                                               {'hostname': 'server3'},
                                               {'hostname': 'server4', 'user': 'bob', 'port': 654}])

        result = msshcopyid.utils.parse_hosts(hosts, ssh_port=None, ssh_config=ssh_config)

        self.assertEqual(result[0].__dict__, {'hostname': 'server1', 'port': 22, 'user': 'me', 'password': None})
        self.assertEqual(result[1].__dict__, {'hostname': 'server2', 'port': 987, 'user': 'alice', 'password': None})
        self.assertEqual(result[2].__dict__, {'hostname': 'server3', 'port': 22, 'user': 'john', 'password': None})
        self.assertEqual(result[3].__dict__, {'hostname': 'server4', 'port': 654, 'user': 'doe', 'password': None})

    @patch('msshcopyid.utils.getpass.getuser', return_value='me')
    def test_parse_hosts_with_port_with_ssh_config(self, mock_getuser):
        hosts = ['server1', 'server2', 'john@server3', 'doe@server4']
        ssh_config = MagicMock()
        ssh_config.lookup = MagicMock(side_effect=[{'hostname': 'server1'},
                                               {'hostname': 'server2', 'user': 'alice', 'port': 987},
                                               {'hostname': 'server3'},
                                               {'hostname': 'server4', 'user': 'bob', 'port': 654}])

        result = msshcopyid.utils.parse_hosts(hosts, ssh_port=12345, ssh_config=ssh_config)

        self.assertEqual(result[0].__dict__, {'hostname': 'server1', 'port': 12345, 'user': 'me', 'password': None})
        self.assertEqual(result[1].__dict__, {'hostname': 'server2', 'port': 12345, 'user': 'alice', 'password': None})
        self.assertEqual(result[2].__dict__, {'hostname': 'server3', 'port': 12345, 'user': 'john', 'password': None})
        self.assertEqual(result[3].__dict__, {'hostname': 'server4', 'port': 12345, 'user': 'doe', 'password': None})
