class MSSHCopyIdException(Exception):
    pass


class CopySSHKeyError(MSSHCopyIdException):
    """
    This exception contains the host name and the exception.
    """

    def __init__(self, host=None, exception=None):
        self.host = host
        self.exception = exception

    def __str__(self):
        return '[{0}] {1}'.format(self.host, str(self.exception))


class CopySSHKeysError(MSSHCopyIdException):
    """
    This exception contains several exceptions during a copy of SSH keys to several hosts.
    """

    def __init__(self, exceptions=None):
        """
        :param exceptions: list of `CopySSHKeyError` objects.
        """
        self.exceptions = exceptions

    def __str__(self):
        return '\n'.join(self.exceptions)
