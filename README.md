# Description

`mssh-copy-id` is a tool to copy SSH keys massively to multiple servers.

# Installation

## CentOS 6

TODO

## CentOS 7

TODO

## Ubuntu 14.04

TODO

# How to use

```
usage: mssh-copy-id [-h] [-a] [-A] [-i IDENTITY] [-k KNOWN_HOSTS] [-n]
                    [-p PORT] [-P PASSWORD] [-R] [-v]
                    host [host ...]

Massively copy SSH keys.

positional arguments:
  host                  the remote hosts to copy the keys to. Syntax:
                        [user@]hostname

optional arguments:
  -h, --help            show this help message and exit
  -a, --add             don't copy the SSH keys, but instead, add the hosts to
                        the known_hosts file
  -A, --no-add-host     don't add automatically new hosts into "known_hosts"
                        file
  -i IDENTITY, --identity IDENTITY
                        the SSH identity file. Default:
                        /home/xxx/.ssh/id_rsa or /home/xxx/.ssh/id_dsa
  -k KNOWN_HOSTS, --known-hosts KNOWN_HOSTS
                        the known_hosts file to use. Default:
                        /home/xxx/.ssh/known_hosts
  -n, --dry             do a dry run. Do not change anything
  -p PORT, --port PORT  the SSH port for the remote hosts
  -P PASSWORD, --password PASSWORD
                        the password to log into the remote hosts. It is NOT
                        SECURED to set the password that way, since it stays
                        in the bash history. Password can also be sent on the
                        STDIN.
  -R, --remove          don't copy the SSH keys, but instead, remove the hosts
                        from the known_hosts file
  -v, --verbose         enable verbose mode.
```

## Examples

Copy the SSH key to 2 servers:

```
mssh-copy-id me@server1.acme.com another@server2.acme.com
```

You can specify the SSH (public) key to send to the servers.

```
mssh-copy-id -i /path/to/custom/id_rsa root@server1
```

You can also use the bash expansion to specify several servers:

```
mssh-copy-id root@server{1..5}
```

is equivalent to:

```
mssh-copy-id root@server1 root@server2 root@server3 root@server4 root@server5
```

You can also send the password on the STDIN:

```
cat file_that_contains_password | mssh-copy-id root@server{1..5}
```

# Development guide

## Install `pyenv`

`pyenv` is a tool that allows you to choose different versions of Python for different projects. It has built-in `virtualenv` support.

### Install `pyenv`

```
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
```

To use `pyenv`, you need to source it first:

```
source pyenv.sh
```

Then, type:

```
pyenv update
```

In the following, we suppose that `pyenv` is sourced.

More info:

* https://github.com/yyuu/pyenv
* https://github.com/yyuu/pyenv-installer

## Install Python 2.6.6 and create a virtualenv

Before installing any Python interpreters, please install the **required dependencies**.

See https://github.com/yyuu/pyenv/wiki/Common-build-problems

Then install `gcc`:

```
yum install -y gcc
```

* Install Python 2.6.6 (default version of CentOS 6):

    ```
    pyenv install 2.6.6
    ```

* Create a virtualenv for `mssh-copy-id` using Python 2.6.6:

    ```
    pyenv virtualenv 2.6.6 mssh-copy-id
    ```

## How to use the virtualenv

* Activate:

    ```
    pyenv activate mssh-copy-id
    ```

Every time you work on the project, remember to activate your virtualenv first.

* Deactivate:

    ```
    pyenv deactivate
    ```

* Remove:

    ```
    pyenv virtualenv-delete mssh-copy-id
    ```

## How to install for development

We need to install Paramiko dependencies:

* For Ubuntu:

    ```
    sudo apt-get install build-essential libssl-dev libffi-dev python-dev
    ```

* For CentOS:

    ```
    yum install -y gcc libffi-devel python-devel openssl-devel
    ```

Go to the project directory, and run:

```
pip install -e .
```

To install the test libs as well, you can run: (recommended for development)

```
pip install -e .[test]
```

## How to run the unit tests

You need to install the libraries for tests (see above).

1. One way is to run:

    ```
    python setup.py test
    ```

2. The other way that allows more control & coverage annotations:

    ```
    ./run-tests.sh
    ```

## How to build

Go to the project directory, and run:

```
python setup.py bdist_wheel
```

You will find the Wheel package in the `dist` directory.

## How to test the installation `mssh-copy-id`

* Create a new virtualenv:

    ```
    pyenv virtualenv 2.6.6 foo
    pyenv activate foo
    ```

* Go to the `dist` directory, and run:

    ```
    pip install mssh_copy_id-0.0.1-py2-none-any.whl
    ```

You should be able to run `mssh-copy-id` as real production.

## How to preview the `README.md` locally

```
pip install grip
grip
```
