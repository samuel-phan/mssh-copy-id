import filecmp
import os

import dockertest


class TestCopyToOneServer(object):

    def test_copy_ssh_key_to_one_server(self, function_test_dir, ssh_keys):
        """
        root@msshcopyid_ctn -> user@sshd_ctn
        """
        with dockertest.start_sshd_container(function_test_dir) as sshd_ctn, \
                dockertest.start_msshcopyid_container(function_test_dir, image='mssh-copy-id-centos6')\
                as msshcopyid_ctn:
            sshd_ctn.add_user('user', 'user_password')
            msshcopyid_ctn.import_ssh_keys('root', ssh_keys)
            msshcopyid_ctn.run_msshcopyid('-P user_password user@{}'.format(sshd_ctn.name))

        assert filecmp.cmp(msshcopyid_ctn.get_ssh_pub_key_file("root"), sshd_ctn.get_authorized_key_file("user"))

    def test_copy_ssh_key_to_one_server_with_wrong_password(self, function_test_dir, ssh_keys):
        """
        root@msshcopyid_ctn -> user@sshd_ctn
        """
        with dockertest.start_sshd_container(function_test_dir) as sshd_ctn, \
                dockertest.start_msshcopyid_container(function_test_dir, image='mssh-copy-id-centos6')\
                as msshcopyid_ctn:
            sshd_ctn.add_user('user', 'user_password')
            msshcopyid_ctn.import_ssh_keys('root', ssh_keys)
            _, exit_status = msshcopyid_ctn.run_msshcopyid('-P wrong_password user@{}'.format(sshd_ctn.name), exit_status_ok=None)
            assert exit_status != 0

        assert not os.path.exists(sshd_ctn.get_authorized_key_file("user"))
