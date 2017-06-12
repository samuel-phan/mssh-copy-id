from contextlib import contextmanager
import logging
import os
import shlex
import shutil
import subprocess
import uuid

import docker
import pytest

import constantstest
import filetest

logger = logging.getLogger(__name__)


@pytest.fixture(scope='session', autouse=True)
def docker_network():
    client = docker.from_env()
    docker_net = client.networks.create(constantstest.DOCKER_NETWORK_NAME)
    logger.info('Created the docker network "{}".'.format(docker_net.name))
    yield docker_net
    docker_net.remove()
    logger.info('Removed the docker network "{}".'.format(docker_net.name))


@contextmanager
def start_sshd_container(containers_dir):
    docker_image = constantstest.DOCKER_SSHD_IMAGE
    container_name = 'sshd_{0}'.format(str(uuid.uuid4()))
    container_dir = os.path.join(containers_dir, container_name)
    volumes = get_container_volumes(container_dir)
    container_id = start_container(docker_image,
                                   name=container_name,
                                   detach=True,
                                   network=constantstest.DOCKER_NETWORK_NAME,
                                   network_alias=container_name,
                                   remove=True,
                                   stdin_open=True,
                                   tty=False,
                                   volumes=volumes,
                                   create_volumes_dir=True)
    client = docker.from_env()
    ctn = client.containers.get(container_id)
    logger.info('Started the container "{}" (name: "{}").'.format(docker_image, ctn.name))
    yield ctn
    ctn.stop()
    logger.info('Stopped the container "{}" (name: "{}").'.format(docker_image, ctn.name))


@contextmanager
def start_msshcopyid_container(containers_dir, image):
    container_name = 'mssh-copy-id_{0}'.format(str(uuid.uuid4()))
    container_dir = os.path.join(containers_dir, container_name)
    volumes = get_container_volumes(container_dir)
    container_id = start_container(image,
                                   name=container_name,
                                   detach=True,
                                   network=constantstest.DOCKER_NETWORK_NAME,
                                   network_alias=container_name,
                                   remove=True,
                                   stdin_open=True,
                                   tty=False,
                                   volumes=volumes,
                                   create_volumes_dir=True)
    client = docker.from_env()
    ctn = client.containers.get(container_id)
    logger.info('Started the container "{}" (name: "{}").'.format(image, ctn.name))
    yield ctn
    socket = ctn.attach_socket(params={'stdin': 1, 'stream': 1})
    socket.send('exit\n')
    socket.close()
    ctn.stop()
    logger.info('Stopped the container "{}" (name: "{}").'.format(image, ctn.name))


def add_user_to_container(ctn, user, password, uid=None):
    if not uid:
        uid = os.getuid()
    ctn.exec_run('useradd -u {} -o {}'.format(uid, user))
    ctn.exec_run('bash -c \'echo "{}:{}" | chpasswd\''.format(user, password))


def copy_ssh_keys_to_container(ctn, user, ssh_keys):
    """
    Copy the given SSH keys for the given user into the container.

    :param ctn: the Container object.
    :param ssh_keys: (priv_key, pub_key) file paths tuple.
    :param user: the user.
    """
    if user == 'root':
        mount = get_container_root_ssh_mount(ctn)
        ssh_key_dir = mount['Source']
    else:
        mount = get_container_home_mount(ctn)
        ssh_key_dir = filetest.create_dir(os.path.join(mount['Source'], user, '.ssh'))

    for file_ in ssh_keys:
        shutil.copy(file_, ssh_key_dir)


def run_msshcopyid_in_container(ctn, args):
    ctn.exec_run('mssh-copy-id {}'.format(args))


def start_container(image, command=None, detach=False, name=None, network=None, network_alias=None, remove=False,
                    stdin_open=False, tty=False, volumes=None, create_volumes_dir=False):
    """
    Start a Docker container.

    :return: if detached, the container ID; the command stdout otherwise.
    """
    # FIXME: use docker CLI because of the issue about --net-alias https://github.com/docker/docker-py/issues/1571
    if volumes and create_volumes_dir:
        for mount_dir in volumes.iterkeys():
            filetest.create_dir(mount_dir)
    cmd = build_docker_cli_args(image,
                                command=command,
                                detach=detach,
                                name=name,
                                network=network,
                                network_alias=network_alias,
                                remove=remove,
                                stdin_open=stdin_open,
                                tty=tty,
                                volumes=volumes)
    logger.debug('Starting container: {0}'.format(' '.join(cmd)))
    return subprocess.check_output(cmd).strip()


def build_docker_cli_args(image, command=None, detach=False, name=None, network=None, network_alias=None, remove=False,
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
    if remove:
        cmd.append('--rm')
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


def get_container_root_ssh_mount(ctn):
    for mount in ctn.attrs['Mounts']:
        if mount['Destination'] == '/root/.ssh':
            return mount


def get_container_home_mount(ctn):
    for mount in ctn.attrs['Mounts']:
        if mount['Destination'] == '/home':
            return mount


def get_container_volumes(container_dir):
    return {os.path.join(container_dir, 'root'): {'bind': '/root/.ssh'},
            os.path.join(container_dir, 'home'): {'bind': '/home'}}
