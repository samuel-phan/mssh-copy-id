import os

DEFAULT_SSH_DIR = os.path.join(os.path.expanduser("~"), '.ssh')

DEFAULT_KNOWN_HOSTS = os.path.join(DEFAULT_SSH_DIR, 'known_hosts')
DEFAULT_SSH_CONFIG = os.path.join(DEFAULT_SSH_DIR, 'config')
DEFAULT_SSH_DSA = os.path.join(DEFAULT_SSH_DIR, 'id_dsa')
DEFAULT_SSH_RSA = os.path.join(DEFAULT_SSH_DIR, 'id_rsa')
DEFAULT_SSH_PORT = 22
