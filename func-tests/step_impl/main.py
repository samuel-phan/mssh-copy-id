from getgauge.python import after_spec, before_spec, step


@before_spec
def before_spec_hook():
    pass


@after_spec
def after_spec_hook():
    pass


@step('Start sshd <server>')
def start_sshd(server):
    # TODO:
    pass
