import subprocess

import paramiko
from mock import call, MagicMock, mock_open, patch
import unittest

import msshcopyid


class TestMain(unittest.TestCase):

    def setUp(self):
        self.main = msshcopyid.Main()

    @patch('msshcopyid.Main.add_to_known_hosts')
    @patch('msshcopyid.open', new_callable=mock_open)
    @patch('os.path.exists', return_value=False)
    @patch('msshcopyid.Main.init')
    def test_main_add(self, mock_init, mock_exists, mock_bopen, mock_add_to_known_hosts):
        self.main.args = MagicMock()
        self.main.args.add = True

        self.main.main()

        mock_init.assert_called_once_with()
        mock_bopen.assert_called_once_with(self.main.args.known_hosts, 'w')
        mock_add_to_known_hosts.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                        dry=self.main.args.dry)

    @patch('msshcopyid.Main.remove_from_known_hosts')
    @patch('msshcopyid.open', new_callable=mock_open)
    @patch('os.path.exists', return_value=False)
    @patch('msshcopyid.Main.init')
    def test_main_remove(self, mock_init, mock_exists, mock_bopen, mock_remove_from_known_hosts):
        self.main.args = MagicMock()
        self.main.args.add = False
        self.main.args.remove = True

        self.main.main()

        mock_init.assert_called_once_with()
        mock_bopen.assert_called_once_with(self.main.args.known_hosts, 'w')
        mock_remove_from_known_hosts.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                             dry=self.main.args.dry)

    @patch('os.path.exists', return_value=False)
    @patch('msshcopyid.Main.init')
    def test_main_copy_ssh_keys_no_pub_key(self, mock_init, mock_exists):
        self.main.args = MagicMock()
        self.main.args.add = False
        self.main.args.remove = False

        self.assertRaises(SystemExit, self.main.main)

    @patch('msshcopyid.Main.run_copy_ssh_keys')
    @patch('msshcopyid.Main.remove_from_known_hosts')
    @patch('os.path.exists', return_value=True)
    @patch('msshcopyid.Main.init')
    def test_main_copy_ssh_keys(self, mock_init, mock_exists, mock_remove_from_known_hosts, mock_run_copy_ssh_keys):
        self.main.args = MagicMock()
        self.main.args.add = False
        self.main.args.remove = False
        self.main.args.clear = False
        self.main.pub_key = MagicMock()

        with patch('msshcopyid.open', mock_open(read_data='pub key content')) as mock_bopen:
            self.main.main()

        mock_init.assert_called_once_with()
        mock_bopen.assert_called_once_with(self.main.pub_key)
        self.assertEqual(self.main.pub_key_content, 'pub key content')
        mock_remove_from_known_hosts.assert_not_called()
        mock_run_copy_ssh_keys.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                       dry=self.main.args.dry)

    @patch('msshcopyid.Main.run_copy_ssh_keys')
    @patch('msshcopyid.Main.remove_from_known_hosts')
    @patch('os.path.exists', return_value=True)
    @patch('msshcopyid.Main.init')
    def test_main_copy_ssh_keys_clear(self, mock_init, mock_exists, mock_remove_from_known_hosts, mock_run_copy_ssh_keys):
        self.main.args = MagicMock()
        self.main.args.add = False
        self.main.args.remove = False
        self.main.args.clear = True
        self.main.pub_key = MagicMock()

        with patch('msshcopyid.open', mock_open(read_data='pub key content')) as mock_bopen:
            self.main.main()

        mock_init.assert_called_once_with()
        mock_bopen.assert_called_once_with(self.main.pub_key)
        self.assertEqual(self.main.pub_key_content, 'pub key content')
        mock_remove_from_known_hosts.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                             dry=self.main.args.dry)
        mock_run_copy_ssh_keys.assert_called_once_with(self.main.hosts, known_hosts=self.main.args.known_hosts,
                                                       dry=self.main.args.dry)

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
        mock_load_config.assert_not_called()

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

    @patch('subprocess.Popen')
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
            self.main.add_to_known_hosts(hosts, known_hosts=known_hosts, dry=False)

        mock_bopen.return_value.writelines.assert_any_call(['{0}\n'.format(k)
                                                            for k in server2_ssh_key, server3_ssh_key])

    @patch('subprocess.Popen')
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
            self.main.add_to_known_hosts(hosts, known_hosts=known_hosts, dry=True)

        mock_bopen.return_value.writelines.assert_not_called()

    @patch('subprocess.check_call')
    def test_remove_from_known_hosts(self, mock_check_call):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = '/path/to/known_hosts'

        self.main.remove_from_known_hosts(hosts, known_hosts=known_hosts, dry=False)

        for host in hosts:
            cmd = ['ssh-keygen', '-f', known_hosts, '-R', host.hostname]
            mock_check_call.assert_any_call(cmd)

    @patch('subprocess.check_call')
    def test_remove_from_known_hosts_dry(self, mock_check_call):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = '/path/to/known_hosts'

        self.main.remove_from_known_hosts(hosts, known_hosts=known_hosts, dry=True)

        mock_check_call.assert_not_called()

    @patch('msshcopyid.format_exception')
    @patch('msshcopyid.format_error')
    @patch('subprocess.check_call')
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

        self.main.remove_from_known_hosts(hosts, known_hosts=known_hosts, dry=False)

        for cmd, ex in zip(cmds, check_call_side_effect):
            mock_check_call.assert_any_call(cmd)
            mock_logger.error.assert_any_call(mock_format_error(mock_format_exception(ex)))

    @patch('msshcopyid.Main.copy_ssh_keys')
    def test_run_copy_ssh_keys(self, mock_copy_ssh_keys):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = MagicMock()

        self.main.run_copy_ssh_keys(hosts, known_hosts=known_hosts, dry=False)

        for host in hosts:
            mock_copy_ssh_keys.assert_any_call(host, hosts, known_hosts=known_hosts)

    @patch('msshcopyid.Main.copy_ssh_keys')
    def test_run_copy_ssh_keys_dry(self, mock_copy_ssh_keys):
        hosts = [msshcopyid.Host(hostname='server1'),
                 msshcopyid.Host(hostname='server2'),
                 msshcopyid.Host(hostname='server3')]
        known_hosts = MagicMock()

        self.main.run_copy_ssh_keys(hosts, known_hosts=known_hosts, dry=True)

        mock_copy_ssh_keys.assert_not_called()

    @patch('paramiko.client.AutoAddPolicy')
    @patch('paramiko.SSHClient')
    def test_copy_ssh_keys(self, mock_ssh_client, mock_auto_add_policy):
        host1 = msshcopyid.Host(hostname='server1')
        host2 = msshcopyid.Host(hostname='server2', port=12345, user='a_user', password='a_password')
        host3 = msshcopyid.Host(hostname='server3')
        hosts = [host1, host2, host3]
        known_hosts = MagicMock()

        self.main.args = MagicMock()
        self.main.args.no_add_host = False
        self.main.priv_key = MagicMock()
        self.main.pub_key_content = 'ssh-rsa AAAAB3NzaC1yc2EAAAAD'

        self.main.copy_ssh_keys(host2, hosts, known_hosts=known_hosts)

        client = mock_ssh_client.return_value.__enter__.return_value
        client.set_missing_host_key_policy.assert_called_once_with(mock_auto_add_policy.return_value)
        client.connect.assert_called_once_with(host2.hostname, port=host2.port, username=host2.user,
                                               password=host2.password, key_filename=self.main.priv_key)
        cmd = (r'''mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
k='{0}' && if ! grep -qFx "$k" ~/.ssh/authorized_keys; then echo "$k" >> ~/.ssh/authorized_keys; fi'''
               .format(self.main.pub_key_content))
        client.exec_command.assert_called_once_with(cmd)

    @patch('msshcopyid.format_exception')
    @patch('msshcopyid.format_error')
    @patch('msshcopyid.logger')
    @patch('paramiko.SSHClient')
    def test_copy_ssh_keys_no_add_host(self, mock_ssh_client, mock_logger, mock_format_error, mock_format_exception):
        host1 = msshcopyid.Host(hostname='server1')
        host2 = msshcopyid.Host(hostname='server2', port=12345, user='a_user', password='a_password')
        host3 = msshcopyid.Host(hostname='server3')
        hosts = [host1, host2, host3]
        known_hosts = MagicMock()
        client = mock_ssh_client.return_value.__enter__.return_value
        ssh_exception = paramiko.ssh_exception.SSHException('ssh exception')
        client.connect.side_effect = ssh_exception

        self.main.args = MagicMock()
        self.main.args.no_add_host = True
        self.main.priv_key = MagicMock()
        self.main.pub_key_content = 'ssh-rsa AAAAB3NzaC1yc2EAAAAD'

        self.main.copy_ssh_keys(host2, hosts, known_hosts=known_hosts)

        client.set_missing_host_key_policy.assert_not_called()
        client.connect.assert_called_once_with(host2.hostname, port=host2.port, username=host2.user,
                                               password=host2.password, key_filename=self.main.priv_key)
        client.exec_command.assert_not_called()
        mock_logger.error.assert_called_once_with(mock_format_error(mock_format_exception(ssh_exception)))

    @patch('msshcopyid.format_exception')
    @patch('msshcopyid.format_error')
    @patch('msshcopyid.logger')
    @patch('msshcopyid.get_password')
    @patch('paramiko.client.AutoAddPolicy')
    @patch('paramiko.SSHClient')
    def test_copy_ssh_keys_ask_missing_password(self, mock_ssh_client, mock_auto_add_policy, mock_get_password,
                                                mock_logger, mock_format_error, mock_format_exception):
        host1 = msshcopyid.Host(hostname='server1')
        host2 = msshcopyid.Host(hostname='server2', port=12345, user='a_user', password=None)
        host3 = msshcopyid.Host(hostname='server3')
        hosts = [host1, host2, host3]
        known_hosts = MagicMock()
        client = mock_ssh_client.return_value.__enter__.return_value
        authentication_exception = paramiko.ssh_exception.AuthenticationException('authentication exception')
        client.connect.side_effect = authentication_exception

        self.main.args = MagicMock()
        self.main.args.no_add_host = False
        self.main.args.password = None
        self.main.priv_key = MagicMock()
        self.main.pub_key_content = 'ssh-rsa AAAAB3NzaC1yc2EAAAAD'

        self.main.copy_ssh_keys(host2, hosts, known_hosts=known_hosts)

        client.set_missing_host_key_policy.assert_called_once_with(mock_auto_add_policy.return_value)
        client.connect.assert_has_calls([call(host2.hostname, port=host2.port, username=host2.user,
                                              password=None, key_filename=self.main.priv_key),
                                         call(host2.hostname, port=host2.port, username=host2.user,
                                              password=host2.password, key_filename=self.main.priv_key)])
        client.exec_command.assert_not_called()
        mock_logger.error.assert_called_once_with(mock_format_error(mock_format_exception(authentication_exception)))

    @patch('msshcopyid.format_exception')
    @patch('msshcopyid.format_error')
    @patch('msshcopyid.logger')
    @patch('msshcopyid.get_password')
    @patch('paramiko.client.AutoAddPolicy')
    @patch('paramiko.SSHClient')
    def test_copy_ssh_keys_wrong_password(self, mock_ssh_client, mock_auto_add_policy, mock_get_password, mock_logger,
                                          mock_format_error, mock_format_exception):
        host1 = msshcopyid.Host(hostname='server1')
        host2 = msshcopyid.Host(hostname='server2', port=12345, user='a_user', password='wrong password')
        host3 = msshcopyid.Host(hostname='server3')
        hosts = [host1, host2, host3]
        known_hosts = MagicMock()
        client = mock_ssh_client.return_value.__enter__.return_value
        authentication_exception = paramiko.ssh_exception.AuthenticationException('authentication exception')
        client.connect.side_effect = authentication_exception

        self.main.args = MagicMock()
        self.main.args.no_add_host = False
        self.main.args.password = None
        self.main.priv_key = MagicMock()
        self.main.pub_key_content = 'ssh-rsa AAAAB3NzaC1yc2EAAAAD'

        self.main.copy_ssh_keys(host2, hosts, known_hosts=known_hosts)

        client.set_missing_host_key_policy.assert_called_once_with(mock_auto_add_policy.return_value)
        client.connect.assert_called_once_with(host2.hostname, port=host2.port, username=host2.user,
                                               password=host2.password, key_filename=self.main.priv_key)
        client.exec_command.assert_not_called()
        mock_logger.error.assert_called_once_with(mock_format_error(mock_format_exception(authentication_exception)))


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
