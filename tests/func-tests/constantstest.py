import datetime
import os


NOW = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_RUN_DIR = os.path.join(PROJECT_DIR, 'dist', 'func-tests', NOW)

DOCKER_NETWORK_NAME = 'mssh-copy-id'
DOCKER_SSHD_IMAGE = 'mssh-copy-id-sshd'
