from contextlib import contextmanager
import logging
import os
import shlex
import shutil
import subprocess
import uuid

import docker
import pytest

from conf import REMOVE_CONTAINERS
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
                                   remove=REMOVE_CONTAINERS,
                                   stdin_open=True,
                                   tty=False,
                                   volumes=volumes,
                                   create_volumes_dir=True)
    client = docker.from_env()
    ctn = Container(client.containers.get(container_id))
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
                                   remove=REMOVE_CONTAINERS,
                                   stdin_open=True,
                                   tty=False,
                                   volumes=volumes,
                                   create_volumes_dir=True)
    client = docker.from_env()
    ctn = MsshcopyidContainer(client.containers.get(container_id))
    logger.info('Started the container "{}" (name: "{}").'.format(image, ctn.name))
    yield ctn
    socket = ctn.attach_socket(params={'stdin': 1, 'stream': 1})
    socket.send('exit\n')
    socket.close()
    ctn.stop()
    logger.info('Stopped the container "{}" (name: "{}").'.format(image, ctn.name))


class Container(docker.models.containers.Container):
    """
    Wrapper class around docker.models.containers.Container to add useful methods for our tests.
    """

    def __init__(self, ctn):
        self.__ctn = ctn

    def __getattr__(self, name):
        try:
            return getattr(self.__ctn, name)
        except AttributeError:
            return getattr(self, name)

    def add_user(self, user, password, uid=None):
        if not uid:
            uid = os.getuid()
        self.exec_run('useradd -u {} -o {}'.format(uid, user))
        self.exec_run('bash -c \'echo "{}:{}" | chpasswd\''.format(user, password))

    def get_ssh_pub_key_file(self, user, pub_key=constantstest.ID_RSA_PUB_FILENAME):
        return os.path.join(self.get_ssh_dir(user), pub_key)

    def get_authorized_key_file(self, user):
        return os.path.join(self.get_ssh_dir(user), constantstest.AUTHORIZED_KEYS_FILENAME)

    def get_ssh_dir(self, user):
        """
        :param user: the user whose SSH directory we want to get the path.
        :return: the mounted SSH directory on the host for the given user.
                 The mount points of either "/root/.ssh" or "/home/<user>/.ssh"
        """
        if user == 'root':
            return self.get_root_ssh_dir()
        else:
            return os.path.join(self.get_home_dir(), user, '.ssh')

    def get_home_dir(self):
        """
        :return: the mounted directory of the /home inside the container.
        :raise KeyError: if the container doesn't have a /home mount point.
        """
        # Example of the content of the variable `mount`:
        # {u'Destination': u'/home',
        #  u'Mode': u'',
        #  u'Propagation': u'rprivate',
        #  u'RW': True,
        #  u'Source': u'/path/to/mount/dir',
        #  u'Type': u'bind'},
        for mount in self.attrs['Mounts']:
            if mount['Destination'] == '/home':
                return mount['Source']
        else:
            raise KeyError('No mount point for "/home".')

    def get_root_ssh_dir(self):
        """
        :return: the mounted directory of the /root/.ssh inside the container.
        :raise KeyError: if the container doesn't have a /root/.ssh mount point.
        """
        # Example of the content of the variable `mount`:
        # {u'Destination': u'/root/.ssh',
        #  u'Mode': u'',
        #  u'Propagation': u'rprivate',
        #  u'RW': True,
        #  u'Source': u'/path/to/mount/dir',
        #  u'Type': u'bind'},
        for mount in self.attrs['Mounts']:
            if mount['Destination'] == '/root/.ssh':
                return mount['Source']
        else:
            raise KeyError('No mount point for "/root/.ssh".')

    def import_ssh_keys(self, user, ssh_keys):
        """
        Import the given SSH keys for the given user into the container.

        :param ssh_keys: (priv_key, pub_key) file paths tuple.
        :param user: the user.
        """
        ssh_key_dir = self.get_ssh_dir(user)
        if user != 'root':
            filetest.create_dir(ssh_key_dir)

        for file_ in ssh_keys:
            shutil.copy(file_, ssh_key_dir)


class MsshcopyidContainer(Container):

    def run_msshcopyid(self, args):
        self.exec_run('mssh-copy-id {}'.format(args))


def start_container(image, command=None, detach=False, name=None, network=None, network_alias=None,
                    remove=REMOVE_CONTAINERS, stdin_open=False, tty=False, volumes=None, create_volumes_dir=False):
    """
    Start a Docker container.

    :return: if detached, the container ID; the command stdout otherwise.
    """
    # Use docker CLI because of the issue about --net-alias https://github.com/docker/docker-py/issues/1571
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


def build_docker_cli_args(image, command=None, detach=False, name=None, network=None, network_alias=None,
                          remove=REMOVE_CONTAINERS, stdin_open=False, tty=False, volumes=None):
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


def get_container_volumes(container_dir):
    return {os.path.join(container_dir, 'root'): {'bind': '/root/.ssh'},
            os.path.join(container_dir, 'home'): {'bind': '/home'}}
