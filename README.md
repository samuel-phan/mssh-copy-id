# Description

`mssh-copy-id` is a tool to simplify the copy of SSH keys to multiple
servers.

# Installation

## CentOS 6

TODO

## CentOS 7

TODO

## Ubuntu 14.04

TODO

# How to use

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

`pyenv` is a tool that allows you to choose different versions of Python
for different projects. It has built-in `virtualenv` support.

### Install `pyenv`

```
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
```

To use `pyenv`, you need to source it first. Go to the project source
and source the file `pyenv.sh`:

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

Before installing any Python interpreters, install the **required
dependencies**.

* Ubuntu/Debian:

    ```
    sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev
    ```

* Fedora/CentOS/RHEL:

    ```
    sudo yum install -y zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel patch
    ```

Source: https://github.com/yyuu/pyenv/wiki/Common-build-problems

Then install `gcc`:

```
sudo yum install -y gcc
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

Every time you work on the project, remember to activate your virtualenv
first.

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
    sudo yum install -y gcc libffi-devel python-devel openssl-devel
    ```

Go to the project directory, and run:

```
pip install -e .
```

To install the dev & test libs as well, you can run: (recommended for
development)

```
pip install -e .[dev,test]
```

## How to run the unit tests

You need to install the libraries for tests (see above).

1. One way is to run:

    ```
    python setup.py test
    ```

2. The other way that allows more control & coverage annotations:

    ```
    inv test
    ```

## How to build

### How to build a wheel package

The python wheel package is more for development purpose, as it requires
lib headers for dependencies and compilation tools to be installed.

#### Requirements

Install the same dependencies as in
[How to install for development](#how-to-install-for-development).

#### Build the wheel package

Go to the project directory, and run:

```
inv build_wheel
```

You will find the Wheel package in the `dist` directory.

#### Test the installation of the wheel package

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

### How to build an RPM package for CentOS 6 & 7

#### Requirements

* [Docker](https://docs.docker.com/): I tested with version `1.11.2` but
  I assume that it will work on older versions.

#### Build the docker image

Run:

```
inv build_docker -i centos6
inv build_docker -i centos7
```

It will build the new docker images:

* `centos6-build-mssh-copy-id`
* `centos7-build-mssh-copy-id`

Check it:

```
docker images
```

#### Build the RPM packages

Run:

```
inv build_rpm -t centos6
inv build_rpm -t centos7
```

The RPM packages will be in `dist/rpmbuild/RPMS/noarch`.

### How to build a deb package

#### Requirements

* [Docker](https://docs.docker.com/): I tested with version `1.11.2` but
  I assume that it will work on older versions.

#### Build the docker image

Run:

```
inv build_docker -i ubuntu14.04
```

It will build the new docker images:

* `ubuntu14.04-build-mssh-copy-id`

Check it:

```
docker images
```

#### Build the deb package

Run:

```
inv build_deb
```

The deb package will be in `dist/deb`.

## How to upload to PyPI

Source documentation: https://packaging.python.org/en/latest/distributing/#uploading-your-project-to-pypi

### Requirements

* `twine`: tool to upload to PyPI. It is part of the extra `dev`
  dependencies. (`pip install -e .[dev,test]`)

### How to upload to PyPI

Create a file `~/.pypirc`:

```
[distutils]
index-servers=
    pypi
    pypitest

[pypi]
repository: https://pypi.python.org/pypi
username: <login>
password: <password>

[pypitest]
repository: https://testpypi.python.org/pypi
username: <login>
password: <password>
```

Build and upload:

```
inv clean build_src build_wheel
twine upload dist/*.tar.gz dist/*.whl
```

## How to preview the `README.md` locally

```
pip install grip
grip
```
