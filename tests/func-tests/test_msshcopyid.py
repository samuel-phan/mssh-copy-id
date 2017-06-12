import os

import basetest
import dockertest
import sshtest


class TestCopyToOneServer(basetest.BaseTestClass):

    def test_copy_ssh_key_to_one_server(self, class_test_dir, function_test_dir):
        ssh_key_file, ssh_pub_file = sshtest.gen_ssh_keys(os.path.join(class_test_dir, 'ssh_keys'))
        with dockertest.start_sshd_container(function_test_dir) as sshd_ctn, \
                dockertest.start_msshcopyid_container(function_test_dir, image='mssh-copy-id-centos6') as msshcopyid_ctn:
            dockertest.add_user_to_container(sshd_ctn, 'user', 'user_password')
            dockertest.copy_ssh_keys_to_container(msshcopyid_ctn, 'root', (ssh_key_file, ssh_pub_file))
            dockertest.run_msshcopyid_in_container(msshcopyid_ctn, '-P user_password user@{}'.format(sshd_ctn.name))
