from __future__ import print_function

import glob
import os
import sys

from invoke import task


PROJECT_DIR = os.path.dirname(__file__)
DIST_DIR = os.path.join(PROJECT_DIR, 'dist')

DOCKER_DIR = os.path.join(PROJECT_DIR, 'docker')
DOCKER_COMMON_DIR = os.path.join(DOCKER_DIR, 'common')

DOCKER_IMGS = {
    'centos6': {'name': 'mssh-copy-id-build-centos6', 'path': os.path.join(DOCKER_DIR, 'mssh-copy-id-build-centos6')},
    'centos7': {'name': 'mssh-copy-id-build-centos7', 'path': os.path.join(DOCKER_DIR, 'mssh-copy-id-build-centos7')},
    'ubuntu-trusty': {'name': 'mssh-copy-id-build-ubuntu-trusty',
                      'path': os.path.join(DOCKER_DIR, 'mssh-copy-id-build-ubuntu-trusty')},
}

DOCKER_RUN_IMGS = {
    'centos6': {'name': 'mssh-copy-id-centos6', 'path': os.path.join(DOCKER_DIR, 'mssh-copy-id-centos6')},
    'centos7': {'name': 'mssh-copy-id-centos7', 'path': os.path.join(DOCKER_DIR, 'mssh-copy-id-centos7')},
}

DOCKER_SSHD_IMG = {'name': 'mssh-copy-id-sshd', 'path': os.path.join(DOCKER_DIR, 'mssh-copy-id-sshd')}


@task
def clean(ctx):
    """
    clean generated project files
    """
    os.chdir(PROJECT_DIR)
    patterns = ['.cache',
                '.coverage',
                '.eggs',
                'build',
                'dist',
                'func-tests/.gauge',
                'func-tests/logs',
                'func-tests/reports']
    ctx.run('rm -vrf {0}'.format(' '.join(patterns)))
    ctx.run('''find . \( -name '*,cover' -o -name '__pycache__' -o -name '*.py[co]' -o -name '_work' \) '''
            '''-exec rm -vrf '{}' \; || true''')


@task
def build_docker_sshd(ctx):
    """
    build docker image sshd-mssh-copy-id
    """
    dinfo = DOCKER_SSHD_IMG
    ctx.run('docker rmi -f {0}'.format(dinfo['name']), warn=True)
    ctx.run('docker build -t {0} {1}'.format(dinfo['name'], dinfo['path']))


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
    dinfo_work_dir = os.path.join(dinfo['path'], '_work')
    ctx.run('mkdir -p {0}'.format(dinfo_work_dir))
    ctx.run('cp {0} {1}'.format(os.path.join(DOCKER_COMMON_DIR, 'sudo-as-user.sh'), dinfo_work_dir))
    ctx.run('docker build -t {0} {1}'.format(dinfo['name'], dinfo['path']))


@task(help={'target': 'the target OS. Can be: ubuntu-trusty'})
def build_deb(ctx, target):
    """
    build a deb package
    """
    if target not in ('ubuntu-trusty',):
        print('Error: unknown target "{0}"!'.format(target), file=sys.stderr)
        sys.exit(1)

    os.chdir(PROJECT_DIR)
    debbuild_dir = os.path.join(DIST_DIR, 'deb')

    # Create directories layout
    ctx.run('mkdir -p {0}'.format(debbuild_dir))

    # Copy the sources
    build_src(ctx, dest=debbuild_dir)
    src_archive = glob.glob(os.path.join(debbuild_dir, 'mssh-copy-id-*.tar.gz'))[0]
    ctx.run('tar -xvf {0} -C {1}'.format(src_archive, debbuild_dir))
    src_dir = src_archive[:-7]  # uncompressed directory
    ctx.run('cp -r {0} {1}'.format(os.path.join(PROJECT_DIR, 'deb/debian'), src_dir))

    # Build the deb
    ctx.run('docker run -e LOCAL_USER_ID={local_user_id} -v {local}:{cont} {img}'
            .format(local_user_id=os.getuid(),
                    local=debbuild_dir,
                    cont='/deb',
                    img=DOCKER_IMGS[target]['name']))

    ctx.run('mv -f {0} {1}'.format(os.path.join(debbuild_dir, 'mssh-copy-id_*.deb'), DIST_DIR))


@task(help={'target': 'the target OS. Can be: centos6, centos7'})
def build_rpm(ctx, target):
    """
    build an RPM package
    """
    if target not in ('centos6', 'centos7'):
        print('Error: unknown target "{0}"!'.format(target), file=sys.stderr)
        sys.exit(1)

    os.chdir(PROJECT_DIR)
    rpmbuild_dir = os.path.join(DIST_DIR, 'rpmbuild')

    # Create directories layout
    ctx.run('mkdir -p {0}'.format(' '.join(os.path.join(rpmbuild_dir, d)
                                           for d in ('BUILD', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS'))))

    # Copy the sources & spec file
    build_src(ctx, dest=os.path.join(rpmbuild_dir, 'SOURCES'))
    ctx.run('cp -f {0} {1}'.format(os.path.join(PROJECT_DIR, 'rpm/centos/mssh-copy-id.spec'),
                                   os.path.join(rpmbuild_dir, 'SPECS')))

    # Build the RPM
    ctx.run('docker run -e LOCAL_USER_ID={local_user_id} -v {local}:{cont} {img}'
            .format(local_user_id=os.getuid(),
                    local=rpmbuild_dir,
                    cont='/rpmbuild',
                    img=DOCKER_IMGS[target]['name']))

    ctx.run('mv -f {0} {1}'.format(os.path.join(rpmbuild_dir, 'RPMS/noarch/mssh-copy-id-*.rpm'), DIST_DIR))


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


@task(pre=[clean], help={'image': 'the docker image. Can be: {0}'.format(', '.join(DOCKER_RUN_IMGS))})
def build_docker_run(ctx, image):
    """
    build docker images to run mssh-copy-id (functional test)
    """
    if image not in DOCKER_RUN_IMGS:
        print('Error: unknown docker image "{0}"!'.format(image), file=sys.stderr)
        sys.exit(1)

    # Build the RPM & deb
    if image in ('centos6', 'centos7'):
        build_rpm(ctx, target=image)
    elif image in ('ubuntu-trusty',):
        # TODO: add ubuntu-trusty
        build_deb(ctx, target=image)

    dinfo = DOCKER_RUN_IMGS[image]
    dinfo_work_dir = os.path.join(dinfo['path'], '_work')
    ctx.run('mkdir -p {0}'.format(dinfo_work_dir))
    ctx.run('cp {0} {1}'.format(os.path.join(DIST_DIR, 'mssh-copy-id-*.rpm'), dinfo_work_dir))
    ctx.run('docker rmi -f {0}'.format(dinfo['name']), warn=True)
    ctx.run('docker build -t {0} {1}'.format(dinfo['name'], dinfo['path']))


@task
def tests(ctx):
    """
    run the unit tests
    """
    os.chdir(PROJECT_DIR)
    ctx.run('py.test --color yes --cov msshcopyid --cov-report annotate --cov-report term-missing -v tests/unit-tests')


@task
def func_tests(ctx):
    """
    run the functional tests
    """
    if sys.version_info < (2, 7):
        raise SystemExit('Error: functional tests require Python 2.7 or higher.')

    os.chdir(PROJECT_DIR)
    ctx.run('py.test --color yes -v tests/func-tests')
