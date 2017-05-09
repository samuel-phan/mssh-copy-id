# Main

## Copy key to one server

* Start sshd as "sshd"
* Add user "user" with password "user_password" to container "sshd"
* Generate SSH keys for "root"@"cli"
* Run mssh-copy-id as "root"@"cli" using "centos6-run-mssh-copy-id" with args "-P user_password user@sshd"
* Test SSH from "root"@"cli" using "centos6-run-mssh-copy-id" to "user"@"sshd"
* Stop container "sshd"
