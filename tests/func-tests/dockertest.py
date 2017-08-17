from contextlib import contextmanager
import datetime
import logging
import os
import shlex
import shutil
import subprocess
import uuid

import docker
import pytest

import conf
import constantstest
import filetest

logger = logging.getLogger(__name__)


@pytest.fixture(scope='session', autouse=True)
def docker_network():
    client = docker.from_env()
    try:
        docker_net = client.networks.get(constantstest.DOCKER_NETWORK_NAME)
    except docker.errors.NotFound:
        docker_net = client.networks.create(constantstest.DOCKER_NETWORK_NAME)
        logger.info('Created the docker network "{}".'.format(docker_net.name))

    yield docker_net

    if conf.DOCKER_CONTAINERS_TERMINATION == conf.REMOVE:
        docker_net.remove()
        logger.info('Removed the docker network "{}".'.format(docker_net.name))
    else:
        logger.info('The docker network "{}" has NOT been removed.'.format(docker_net.name))


@contextmanager
def start_sshd_container(containers_dir):
    start_dt = datetime.datetime.now()
    docker_image = constantstest.DOCKER_SSHD_IMAGE
    container_name = 'sshd_{0}'.format(str(uuid.uuid4()))
    container_dir = os.path.join(containers_dir, container_name)
    volumes = get_container_volumes(container_dir)
    container_id = start_container(docker_image,
                                   name=container_name,
                                   detach=True,
                                   network=constantstest.DOCKER_NETWORK_NAME,
                                   network_alias=container_name,
                                   remove=conf.DOCKER_CONTAINERS_TERMINATION == conf.REMOVE,
                                   stdin_open=True,
                                   tty=False,
                                   volumes=volumes,
                                   create_volumes_dir=True)
    client = docker.from_env()
    ctn = Container(client.containers.get(container_id))
    logger.info('Started the container "{}" (name: "{}"). (elapsed: {})'.format(docker_image, ctn.name,
                                                                                datetime.datetime.now() - start_dt))
    yield ctn

    if conf.DOCKER_CONTAINERS_TERMINATION in (conf.STOP, conf.REMOVE):
        stop_dt = datetime.datetime.now()
        ctn.stop()
        logger.info('Stopped the container "{}" (name: "{}"). (elapsed: {})'.format(docker_image, ctn.name,
                                                                                    datetime.datetime.now() - stop_dt))


@contextmanager
def start_msshcopyid_container(containers_dir, image):
    start_dt = datetime.datetime.now()
    container_name = 'mssh-copy-id_{0}'.format(str(uuid.uuid4()))
    container_dir = os.path.join(containers_dir, container_name)
    volumes = get_container_volumes(container_dir)
    container_id = start_container(image,
                                   name=container_name,
                                   detach=True,
                                   network=constantstest.DOCKER_NETWORK_NAME,
                                   network_alias=container_name,
                                   remove=conf.DOCKER_CONTAINERS_TERMINATION == conf.REMOVE,
                                   stdin_open=True,
                                   tty=False,
                                   volumes=volumes,
                                   create_volumes_dir=True)
    client = docker.from_env()
    ctn = MSSHCopyIdContainer(client.containers.get(container_id))
    logger.info('Started the container "{}" (name: "{}"). (elapsed: {})'.format(image, ctn.name,
                                                                                datetime.datetime.now() - start_dt))
    yield ctn

    if conf.DOCKER_CONTAINERS_TERMINATION in (conf.STOP, conf.REMOVE):
        stop_dt = datetime.datetime.now()
        socket = ctn.attach_socket(params={'stdin': 1, 'stream': 1})
        socket.send('exit\n')
        socket.close()
        ctn.stop()
        logger.info('Stopped the container "{}" (name: "{}"). (elapsed: {})'.format(image, ctn.name,
                                                                                    datetime.datetime.now() - stop_dt))


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

    def exec_run2(self, cmd, stdout=True, stderr=True, stdin=False, tty=False,
                  privileged=False, user='', detach=False, stream=False,
                  socket=False, environment=None):
        """
        Run a command inside this container. Similar to
        ``docker exec``.

        Args:
            cmd (str or list): Command to be executed
            stdout (bool): Attach to stdout. Default: ``True``
            stderr (bool): Attach to stderr. Default: ``True``
            stdin (bool): Attach to stdin. Default: ``False``
            tty (bool): Allocate a pseudo-TTY. Default: False
            privileged (bool): Run as privileged.
            user (str): User to execute command as. Default: root
            detach (bool): If true, detach from the exec command.
                Default: False
            stream (bool): Stream response data. Default: False
            environment (dict or list): A dictionary or a list of strings in
                the following format ``["PASSWORD=xxx"]`` or
                ``{"PASSWORD": "xxx"}``.

        Returns:
            tuple:
                (generator or str): If ``stream=True``, a generator yielding
                    response chunks. A string containing response data otherwise.
                int: Return code of the exec

        Raises:
            :py:class:`docker.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.exec_create(
            self.id, cmd, stdout=stdout, stderr=stderr, stdin=stdin, tty=tty,
            privileged=privileged, user=user, environment=environment
        )
        exec_output = self.client.api.exec_start(
            resp['Id'], detach=detach, tty=tty, stream=stream, socket=socket
        )
        exec_inspect = self.client.api.exec_inspect(resp['Id'])
        return exec_output, exec_inspect['ExitCode']

    def run_cmd(self, cmd, stdout=True, stderr=True, stdin=False, tty=False, privileged=False, user='', detach=False,
                stream=False, socket=False, environment=None, exit_status_ok=0):
        """
        Run a command but stops as soon as there is a command error.

        :param cmd: the command to run. Can be either a `str` or a `list`.
        :param exit_status_ok: what will be considered as an OK exit status. If `None`, don't check the exit code.
        :return: a tuple (output, exit status) whose type is (str or generator, int).
        :raise docker.errors.ContainerError: if a command's exit status is different from the `exit_status_ok`
        """
        cmd_str = ' '.join(cmd) if isinstance(cmd, (list, tuple)) else cmd
        logger.debug('Running "{}" in container "{}"'.format(cmd_str, self.name))
        out, exit_status = self.exec_run2(cmd, stdout=stdout, stderr=stderr, stdin=stdin, tty=tty,
                                          privileged=privileged, user=user, detach=detach, stream=stream,
                                          socket=socket, environment=environment)
        logger.debug('Result of running "{}" in container "{}" (exit status: {}):\n{}'
                     .format(cmd_str, self.name, exit_status, out))
        if exit_status_ok is not None and exit_status != exit_status_ok:
            raise docker.errors.ContainerError(self,
                                               exit_status,
                                               ' '.join(cmd) if isinstance(cmd, (list, tuple)) else cmd,
                                               self.image,
                                               out)
        else:
            return out, exit_status

    def run_cmds(self, cmds, stdout=True, stderr=True, stdin=False, tty=False, privileged=False, user='', detach=False,
                 stream=False, socket=False, environment=None, exit_status_ok=0):
        """
        Run several commands but stops as soon as there is a command error.

        :param cmds: a list of commands to run. A command can be either a `str` or a `list`.
        :param exit_status_ok: what will be considered as an OK exit status.
        :return: a list of tuples (output, exit status) whose type is (str or generator, int).
        :raise docker.errors.ContainerError: if a command's exit status is different from the `exit_status_ok`
        """
        results = []
        for cmd in cmds:
            out, exit_status = self.run_cmd(cmd, stdout=stdout, stderr=stderr, stdin=stdin, tty=tty,
                                            privileged=privileged, user=user, detach=detach, stream=stream,
                                            socket=socket, environment=environment)
            results.append((out, exit_status))

        return results

    def add_user(self, user, password, uid=None):
        if not uid:
            uid = os.getuid()

        self.run_cmds(('useradd -u {} -o {}'.format(uid, user),
                       'bash -c \'echo "{}:{}" | chpasswd\''.format(user, password)))

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

        :param ssh_keys: an SSHKeys object.
        :param user: the user.
        """
        ssh_key_dir = self.get_ssh_dir(user)
        if user != 'root':
            filetest.create_dir(ssh_key_dir)

        for ssh_file in (ssh_keys.ssh_key_file, ssh_keys.ssh_pub_file):
            shutil.copy(ssh_file, ssh_key_dir)


class MSSHCopyIdContainer(Container):

    def run_msshcopyid(self, args, exit_status_ok=0):
        return self.run_cmd('mssh-copy-id {}'.format(args), exit_status_ok=exit_status_ok)


def start_container(image, command=None, detach=False, name=None, network=None, network_alias=None,
                    remove=False, stdin_open=False, tty=False, volumes=None, create_volumes_dir=False):
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
                          remove=False, stdin_open=False, tty=False, volumes=None):
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
