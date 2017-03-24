from __future__ import print_function

import glob
import os
import sys

from invoke import task


PROJECT_DIR = os.path.dirname(__file__)

DOCKER_IMGS = {
    'centos6': {'name': 'centos6-build-mssh-copy-id', 'path': 'docker/centos6-build-mssh-copy-id'},
    'centos7': {'name': 'centos7-build-mssh-copy-id', 'path': 'docker/centos7-build-mssh-copy-id'},
    'ubuntu14.04': {'name': 'ubuntu14.04-build-mssh-copy-id', 'path': 'docker/ubuntu14.04-build-mssh-copy-id'},
    'sshd': {'name': 'sshd-mssh-copy-id', 'path': 'docker/sshd-mssh-copy-id'},
}


@task
def clean(ctx):
    """
    clean generated project files
    """
    os.chdir(PROJECT_DIR)
    patterns = ['.coverage', '.eggs', 'build', 'dist']
    ctx.run('rm -vrf {0}'.format(' '.join(patterns)))
    ctx.run('''find . \( -name '*,cover' -o -name '__pycache__' -o -name '*.py[co]' \) -exec rm -vrf '{}' \;''')


@task(help={'image': 'the docker image. Can be: {0}'.format(', '.join(DOCKER_IMGS))})
def build_docker(ctx, image):
    """
    build docker images
    """
    if image not in DOCKER_IMGS:
        print('Error: unknown docker image "{0}"!'.format(image), file=sys.stderr)
        sys.exit(1)

    dinfo = DOCKER_IMGS[image]
    ctx.run('docker rmi -f {0}'.format(dinfo['name']), warn=True)
    ctx.run('docker build -t {0} {1}'.format(dinfo['name'], os.path.join(PROJECT_DIR, dinfo['path'])))


@task(help={'target': 'the target OS. Can be: ubuntu14.04'})
def build_deb(ctx, target='ubuntu14.04'):
    """
    build a deb package
    """
    if target not in ('ubuntu14.04',):
        print('Error: unknown target "{0}"!'.format(target), file=sys.stderr)
        sys.exit(1)

    os.chdir(PROJECT_DIR)
    debbuild_dir = os.path.join(PROJECT_DIR, 'dist/deb')

    # Create directories layout
    ctx.run('mkdir -p {0}'.format(debbuild_dir))

    # Copy the sources
    build_src(ctx, dest=debbuild_dir)
    src_archive = glob.glob(os.path.join(debbuild_dir, 'mssh-copy-id-*.tar.gz'))[0]
    ctx.run('tar -xvf {0} -C {1}'.format(src_archive, debbuild_dir))
    src_dir = src_archive[:-7]  # uncompressed directory
    ctx.run('cp -r {0} {1}'.format(os.path.join(PROJECT_DIR, 'deb/debian'), src_dir))

    # Build the deb
    ctx.run('docker run -v {0}:{1} {2}'
            .format(debbuild_dir, '/deb', DOCKER_IMGS[target]['name']))


@task(help={'target': 'the target OS. Can be: centos6, centos7'})
def build_rpm(ctx, target='centos7'):
    """
    build an RPM package
    """
    if target not in ('centos6', 'centos7'):
        print('Error: unknown target "{0}"!'.format(target), file=sys.stderr)
        sys.exit(1)

    os.chdir(PROJECT_DIR)
    rpmbuild_dir = os.path.join(PROJECT_DIR, 'dist/rpmbuild')

    # Create directories layout
    ctx.run('mkdir -p {0}'.format(' '.join(os.path.join(rpmbuild_dir, d)
                                           for d in ('BUILD', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS'))))

    # Copy the sources & spec file
    build_src(ctx, dest=os.path.join(rpmbuild_dir, 'SOURCES'))
    ctx.run('cp -f {0} {1}'.format(os.path.join(PROJECT_DIR, 'rpm/centos/mssh-copy-id.spec'),
                                   os.path.join(rpmbuild_dir, 'SPECS')))

    # Build the RPM
    ctx.run('docker run -v {0}:{1} {2}'
            .format(rpmbuild_dir, '/rpmbuild', DOCKER_IMGS[target]['name']))


@task(help={'dest': 'destination directory of the archive'})
def build_src(ctx, dest=None):
    """
    build source archive
    """
    if dest:
        if not dest.startswith('/'):
            # Relative
            dest = os.path.join(os.getcwd(), dest)

        os.chdir(PROJECT_DIR)
        ctx.run('python setup.py sdist --dist-dir {0}'.format(dest))
    else:
        os.chdir(PROJECT_DIR)
        ctx.run('python setup.py sdist')


@task
def build_wheel(ctx):
    """
    build a wheel package
    """
    os.chdir(PROJECT_DIR)
    ctx.run('python setup.py bdist_wheel')


@task
def test(ctx):
    """
    run the tests
    """
    os.chdir(PROJECT_DIR)
    ctx.run('py.test --color yes --cov msshcopyid --cov-report annotate --cov-report term-missing -v tests')
