# Description

`mssh-copy-id` is a tool to copy SSH keys massively to multiple servers.

# Installation

## CentOS 6

TODO

## CentOS 7

TODO

## Ubuntu 14.04

TODO

# Development guide

## Install `pyenv`

`pyenv` is a tool that allows you to choose different versions of Python for different projects. It has built-in `virtualenv` support.

### Install the required dependencies.

See https://github.com/yyuu/pyenv/wiki/Common-build-problems

### Install `pyenv`

```
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
pyenv update
```

To use `pyenv`, you need to source it first:

```
source pyenv.sh
```

In the following, we suppose that `pyenv` is sourced.

More info:

* https://github.com/yyuu/pyenv
* https://github.com/yyuu/pyenv-installer

## Install Python 2.6.6 and create a virtualenv

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

## How to install `mssh-copy-id` for development

Go to the project directory, and run:

```
pip install -e .
```

To download the dev & test libs, you can run: (recommended for development)
 
```
pip install -e .[dev,test]
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
