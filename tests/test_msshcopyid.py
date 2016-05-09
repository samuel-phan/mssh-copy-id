from mock import MagicMock, mock_open, patch
import unittest

import msshcopyid


class TestMain(unittest.TestCase):

    def setUp(self):
        self.main = msshcopyid.Main()

    def test_main(self):
        # TODO:
        pass

    @patch('msshcopyid.Main.parse_hosts')
    @patch('msshcopyid.load_config')
    @patch('msshcopyid.logger')
    @patch('msshcopyid.logging')
    @patch('msshcopyid.Main.parse_args')
    def test_init_no_verbose(self, mock_parse_args, mock_logging, mock_logger, mock_load_config, mock_parse_hosts):
        args = mock_parse_args.return_value
        args.verbose = False
        args.identity = '/home/user/.ssh/id_rsa'

        self.main.init()

        self.assertEqual(self.main.args, mock_parse_args.return_value)
        self.assertEqual(self.main.priv_key, '/home/user/.ssh/id_rsa')
        self.assertEqual(self.main.pub_key, '/home/user/.ssh/id_rsa.pub')
        self.assertEqual(self.main.hosts, mock_parse_hosts.return_value)

        mock_logger.setLevel.assert_called_once_with(mock_logging.INFO)
        mock_load_config.assert_called_once_with()
        mock_parse_hosts.assert_called_once_with(self.main.args.hosts, mock_load_config.return_value)

    @patch('msshcopyid.Main.parse_hosts')
    @patch('msshcopyid.load_config')
    @patch('msshcopyid.logger')
    @patch('msshcopyid.logging')
    @patch('msshcopyid.Main.parse_args')
    def test_init_verbose(self, mock_parse_args, mock_logging, mock_logger, mock_load_config, mock_parse_hosts):
        args = mock_parse_args.return_value
        args.verbose = True
        args.identity = '/home/user/.ssh/id_rsa'

        self.main.init()

        self.assertEqual(self.main.args, mock_parse_args.return_value)
        self.assertEqual(self.main.priv_key, '/home/user/.ssh/id_rsa')
        self.assertEqual(self.main.pub_key, '/home/user/.ssh/id_rsa.pub')
        self.assertEqual(self.main.hosts, mock_parse_hosts.return_value)

        mock_logger.setLevel.assert_called_once_with(mock_logging.DEBUG)
        mock_load_config.assert_called_once_with()
        mock_parse_hosts.assert_called_once_with(self.main.args.hosts, mock_load_config.return_value)

    @patch('msshcopyid.Main.parse_hosts')
    @patch('msshcopyid.load_config')
    @patch('os.path.exists', side_effect=[True])
    @patch('msshcopyid.logger')
    @patch('msshcopyid.logging')
    @patch('msshcopyid.Main.parse_args')
    def test_init_rsa(self, mock_parse_args, mock_logging, mock_logger, mock_exists, mock_load_config, mock_parse_hosts):
        args = mock_parse_args.return_value
        args.verbose = False
        args.identity = None

        self.main.init()

        self.assertEqual(self.main.args, mock_parse_args.return_value)
        self.assertEqual(self.main.priv_key, msshcopyid.DEFAULT_SSH_RSA)
        self.assertEqual(self.main.pub_key, '{0}.pub'.format(msshcopyid.DEFAULT_SSH_RSA))
        self.assertEqual(self.main.hosts, mock_parse_hosts.return_value)

        mock_logger.setLevel.assert_called_once_with(mock_logging.INFO)
        mock_load_config.assert_called_once_with()
        mock_parse_hosts.assert_called_once_with(self.main.args.hosts, mock_load_config.return_value)

    @patch('msshcopyid.Main.parse_hosts')
    @patch('msshcopyid.load_config')
    @patch('os.path.exists', side_effect=[False, True])
    @patch('msshcopyid.logger')
    @patch('msshcopyid.logging')
    @patch('msshcopyid.Main.parse_args')
    def test_init_dsa(self, mock_parse_args, mock_logging, mock_logger, mock_exists, mock_load_config, mock_parse_hosts):
        args = mock_parse_args.return_value
        args.verbose = False
        args.identity = None

        self.main.init()

        self.assertEqual(self.main.args, mock_parse_args.return_value)
        self.assertEqual(self.main.priv_key, msshcopyid.DEFAULT_SSH_DSA)
        self.assertEqual(self.main.pub_key, '{0}.pub'.format(msshcopyid.DEFAULT_SSH_DSA))
        self.assertEqual(self.main.hosts, mock_parse_hosts.return_value)

        mock_logger.setLevel.assert_called_once_with(mock_logging.INFO)
        mock_load_config.assert_called_once_with()
        mock_parse_hosts.assert_called_once_with(self.main.args.hosts, mock_load_config.return_value)

    @patch('msshcopyid.load_config')
    @patch('os.path.exists', return_value=False)
    @patch('msshcopyid.logger')
    @patch('msshcopyid.logging')
    @patch('msshcopyid.Main.parse_args')
    def test_init_no_ssh_key(self, mock_parse_args, mock_logging, mock_logger, mock_exists, mock_load_config):
        args = mock_parse_args.return_value
        args.verbose = False
        args.identity = None

        self.assertRaises(SystemExit, self.main.init)

        self.assertEqual(self.main.args, mock_parse_args.return_value)

        mock_logger.setLevel.assert_called_once_with(mock_logging.INFO)
        self.assertFalse(mock_load_config.called)

    @patch('getpass.getuser', return_value='me')
    def test_parse_hosts_no_port(self, mock_getuser):
        hosts = ['server1', 'server2', 'john@server3', 'doe@server4']
        config = MagicMock()
        config.lookup = MagicMock(side_effect=[{'hostname': 'server1'},
                                               {'hostname': 'server2', 'user': 'alice', 'port': 987},
                                               {'hostname': 'server3'},
                                               {'hostname': 'server4', 'user': 'bob', 'port': 654}])
        self.main.args = MagicMock()
        self.main.args.port = None

        result = self.main.parse_hosts(hosts, config)

        self.assertEqual(result[0].__dict__, {'hostname': 'server1', 'port': 22, 'user': 'me', 'password': None})
        self.assertEqual(result[1].__dict__, {'hostname': 'server2', 'port': 987, 'user': 'alice', 'password': None})
        self.assertEqual(result[2].__dict__, {'hostname': 'server3', 'port': 22, 'user': 'john', 'password': None})
        self.assertEqual(result[3].__dict__, {'hostname': 'server4', 'port': 654, 'user': 'doe', 'password': None})

    @patch('getpass.getuser', return_value='me')
    def test_parse_hosts_with_port(self, mock_getuser):
        hosts = ['server1', 'server2', 'john@server3', 'doe@server4']
        config = MagicMock()
        config.lookup = MagicMock(side_effect=[{'hostname': 'server1'},
                                               {'hostname': 'server2', 'user': 'alice', 'port': 987},
                                               {'hostname': 'server3'},
                                               {'hostname': 'server4', 'user': 'bob', 'port': 654}])
        self.main.args = MagicMock()
        self.main.args.port = 12345

        result = self.main.parse_hosts(hosts, config)

        self.assertEqual(result[0].__dict__, {'hostname': 'server1', 'port': 12345, 'user': 'me', 'password': None})
        self.assertEqual(result[1].__dict__, {'hostname': 'server2', 'port': 12345, 'user': 'alice', 'password': None})
        self.assertEqual(result[2].__dict__, {'hostname': 'server3', 'port': 12345, 'user': 'john', 'password': None})
        self.assertEqual(result[3].__dict__, {'hostname': 'server4', 'port': 12345, 'user': 'doe', 'password': None})

    def test_add_to_known_hosts(self):
        # TODO:
        pass

    def test_remove_from_known_hosts(self):
        # TODO:
        pass

    def test_run_copy_ssh_keys(self):
        # TODO:
        pass

    def test_copy_ssh_keys(self):
        # TODO:
        pass


class TestModule(unittest.TestCase):

    @patch('msshcopyid.open', new_callable=mock_open)
    @patch('os.path.isfile', return_value=True)
    @patch('paramiko.config.SSHConfig')
    def test_load_config_exists(self, mock_ssh_config, mock_isfile, mock_bopen):
        config_obj = mock_ssh_config.return_value

        result = msshcopyid.load_config()

        self.assertEqual(result, config_obj)
        config_obj.parse.assert_called_once_with(mock_bopen.return_value)

    @patch('msshcopyid.open', new_callable=mock_open)
    @patch('os.path.isfile', return_value=False)
    @patch('paramiko.config.SSHConfig')
    def test_load_config_not_exist(self, mock_ssh_config, mock_isfile, mock_bopen):
        config_obj = mock_ssh_config.return_value

        result = msshcopyid.load_config()

        self.assertEqual(result, config_obj)
        config_obj.parse.assert_not_called()

    @patch('sys.stdin.readline')
    @patch('sys.stdin.isatty', return_value=False)
    def test_get_password_stdin(self, mock_isatty, mock_readline):
        result = msshcopyid.get_password()
        self.assertEqual(result, mock_readline.return_value.strip.return_value)
        mock_isatty.assert_called_once_with()

    @patch('getpass.getpass')
    @patch('sys.stdin.isatty', return_value=True)
    def test_get_password_prompt(self, mock_isatty, mock_getpass):
        result = msshcopyid.get_password()
        self.assertEqual(result, mock_getpass.return_value)
        mock_isatty.assert_called_once_with()
        mock_getpass.assert_called_once_with('Enter the password: ')
