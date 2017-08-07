import datetime
import os


# Test directories
NOW = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_RUN_DIR = os.path.join(PROJECT_DIR, 'dist', 'func-tests', NOW)

# Docker
DOCKER_NETWORK_NAME = 'mssh-copy-id'
DOCKER_SSHD_IMAGE = 'mssh-copy-id-sshd'

# SSH
AUTHORIZED_KEYS_FILENAME = 'authorized_keys'
ID_RSA_PUB_FILENAME = 'id_rsa.pub'
