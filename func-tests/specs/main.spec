# Main

## Copy key to one server

* Start sshd as "sshd"
* Add user "user" with password "user_password" to container "sshd"
* Generate SSH keys for "root" in "cli"
* Run mssh-copy-id on "centos6" as "root" with args "-P user_password user@sshd" using "cli"
* Test SSH connection on "centos6" as "root" using "cli" to "sshd" as "user"
* Stop container "sshd"
