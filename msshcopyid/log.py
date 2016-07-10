def format_error(msg):
    return 'Error: {0}'.format(msg)


def format_exception(ex):
    return '{0}: {1}'.format(type(ex).__name__, ex)
