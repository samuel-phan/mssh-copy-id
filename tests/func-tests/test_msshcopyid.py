import filecmp
import os

import basetest
import dockertest
import sshtest


class TestCopyToOneServer(basetest.BaseTestClass):

    def test_copy_ssh_key_to_one_server(self, class_test_dir, function_test_dir):
        """
        root@msshcopyid_ctn -> user@sshd_ctn
        """
        ssh_key_file, ssh_pub_file = sshtest.gen_ssh_keys(os.path.join(class_test_dir, 'ssh_keys'))
        with dockertest.start_sshd_container(function_test_dir) as sshd_ctn, \
                dockertest.start_msshcopyid_container(function_test_dir, image='mssh-copy-id-centos6')\
                as msshcopyid_ctn:
            sshd_ctn.add_user('user', 'user_password')
            msshcopyid_ctn.import_ssh_keys('root', (ssh_key_file, ssh_pub_file))
            msshcopyid_ctn.run_msshcopyid('-P user_password user@{}'.format(sshd_ctn.name))

        assert filecmp.cmp(msshcopyid_ctn.get_ssh_pub_key_file("root"), sshd_ctn.get_authorized_key_file("user"))
