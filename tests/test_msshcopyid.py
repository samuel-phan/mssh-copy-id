from mock import mock_open, patch
import unittest

import msshcopyid


class TestMSSHCopyId(unittest.TestCase):

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
