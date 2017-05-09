from __future__ import print_function

import datetime
import logging
import os
import re
import shlex
import subprocess

import docker
from getgauge.python import after_scenario, before_scenario, before_spec, step

DOCKER_SSHD_IMAGE = 'sshd-mssh-copy-id'

NOW = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
GAUGE_PROJECT_ROOT = os.environ['GAUGE_PROJECT_ROOT']
WORK_DIR = os.path.join(GAUGE_PROJECT_ROOT, os.environ['work_directory'])
MY_WORK_DIR = os.path.join(WORK_DIR, NOW)

# Living infos that change for every scenario
SPEC = None
SPEC_WD = None  # working dir
SCENARIO = None
SCENARIO_WD = None  # working dir
DOCKER_NETWORK = None  # Docker Network object
CONTAINERS = {}  # key: container name / value: Container object


@before_spec
def before_spec_hook(context):
    global SPEC, SPEC_WD
    SPEC = context.specification.name
    SPEC_WD = os.path.join(MY_WORK_DIR, SPEC)
    if not os.path.isdir(SPEC_WD):
        os.makedirs(SPEC_WD)


@before_scenario
def before_scenario_hook(context):
    global SCENARIO, SCENARIO_WD
    SCENARIO = context.scenario.name
    SCENARIO_WD = os.path.join(SPEC_WD, SCENARIO)
    os.mkdir(SCENARIO_WD)

    # Create a Docker network
    global DOCKER_NETWORK
    network_name = escape_name('mssh-copy-id_{}_{}_{}'.format(SPEC, SCENARIO, NOW))
    client = docker.from_env()
    if network_name not in [n.name for n in client.networks.list()]:
        # Create the Docker network
        DOCKER_NETWORK = client.networks.create(network_name)


@after_scenario
def after_scenario_hook():
    global DOCKER_NETWORK
    if CONTAINERS:
        logging.warning('There are still running containers after the scenario "{}": {}'
                        .format(SCENARIO, ', '.join(c.name for c in CONTAINERS.itervalues())))
        logging.warning('Couldn\'t delete the Docker network "{}" because of the living containers.'
                        .format(DOCKER_NETWORK.name))
    else:
        DOCKER_NETWORK.remove()
        DOCKER_NETWORK = None


@step('Start sshd as <container_name>')
def start_sshd(container_name):
    real_container_name = gen_real_container_name(container_name)
    volumes = get_container_volumes(container_name)
    container_id = start_container(DOCKER_SSHD_IMAGE,
                                   detach=True,
                                   name=real_container_name,
                                   network=DOCKER_NETWORK.name,
                                   network_alias=container_name,
                                   stdin_open=True,
                                   tty=False,
                                   volumes=volumes,
                                   create_volumes_dir=True)
    add_container(container_name, container_id)


@step('Add user <user> with password <password> to container <container_name>')
def add_user_to_container(user, password, container_name):
    container = CONTAINERS[container_name]
    container.exec_run('useradd -u {} -o {}'.format(os.getuid(), user))
    container.exec_run('bash -c \'echo "{}:{}" | chpasswd\''.format(user, password))


@step('Generate SSH keys for <user>@<container_name>')
def generate_ssh_keys(user, container_name):
    container_mount_dir = get_container_mount_dir(container_name)
    if user == 'root':
        ssh_dir = os.path.join(container_mount_dir, 'root')
    else:
        ssh_dir = os.path.join(container_mount_dir, 'home', user, '.ssh')
    if not os.path.isdir(ssh_dir):
        os.makedirs(ssh_dir)

    ssh_key_file = os.path.join(ssh_dir, 'id_rsa')
    subprocess.check_call(['ssh-keygen', '-N', "", '-f', ssh_key_file], stdout=open(os.devnull, 'wb'))


@step('Run mssh-copy-id as <user>@<container_name> using <image> with args <args>')
def run_mssh_copy_id(user, container_name, image, args):
    # TODO: take into account the "user"
    real_container_name = gen_real_container_name(container_name)
    volumes = get_container_volumes(container_name)
    start_container(image,
                    command="mssh-copy-id " + args,
                    name=real_container_name,
                    network=DOCKER_NETWORK.name,
                    stdin_open=True,
                    tty=False,
                    volumes=volumes,
                    create_volumes_dir=True)


@step('Test SSH from <src_user>@<container_name> using <image> to <dst_user>@<dst_container>')
def test_ssh(src_user, src_container, image, dst_user, dst_container):
    # TODO: implement
    pass


@step('Stop container <container_name>')
def stop_container(container_name):
    CONTAINERS[container_name].remove(force=True)
    del CONTAINERS[container_name]


def start_container(image, command=None, detach=False, name=None, network=None, network_alias=None, stdin_open=False,
                    tty=False, volumes=None, create_volumes_dir=False):
    """
    Start a Docker container.
    
    :return: if detached, the container ID; the command stdout otherwise.
    """
    # FIXME: use docker CLI because of the issue about --net-alias https://github.com/docker/docker-py/issues/1571
    if volumes and create_volumes_dir:
        for mount_dir in volumes.iterkeys():
            if not os.path.isdir(mount_dir):
                os.makedirs(mount_dir)
    cmd = build_docker_cli_args(image,
                                command=command,
                                detach=detach,
                                name=name,
                                network=network,
                                network_alias=network_alias,
                                stdin_open=stdin_open,
                                tty=tty,
                                volumes=volumes)
    return subprocess.check_output(cmd).strip()


def build_docker_cli_args(image, command=None, detach=False, name=None, network=None, network_alias=None,
                          stdin_open=False, tty=False, volumes=None):
    cmd = ['docker', 'run']
    if detach:
        cmd.append('-d')
    if name:
        cmd.extend(['--name', name])
    if network:
        cmd.extend(['--network', network])
    if network_alias:
        cmd.extend(['--network-alias', network_alias])
    if stdin_open:
        cmd.append('-i')
    if tty:
        cmd.append('-t')
    if volumes:
        for mount_point, volume in volumes.iteritems():
            cmd.extend(['-v', '{}:{}'.format(mount_point, volume['bind'])])
    cmd.append(image)
    if command:
        cmd.extend(shlex.split(command))

    return cmd


def gen_real_container_name(name):
    return escape_name('{}_{}_{}_{}'.format(name, SPEC, SCENARIO, NOW))


def add_container(container_name, container_id):
    client = docker.from_env()
    container = client.containers.get(container_id)
    if not container_name:
        container_name = container.name
    CONTAINERS[container_name] = container


def escape_name(name):
    return re.sub(r'[^a-zA-Z0-9_.-]', '-', name)


def get_container_mount_dir(container_name):
    return os.path.join(SCENARIO_WD, container_name)


def get_container_volumes(container_name):
    container_mount_dir = get_container_mount_dir(container_name)
    return {os.path.join(container_mount_dir, 'root'): {'bind': '/root/.ssh'},
            os.path.join(container_mount_dir, 'home'): {'bind': '/home'}}
