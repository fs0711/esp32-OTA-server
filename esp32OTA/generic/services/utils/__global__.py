from flask import g


def set_current_user(user):
    return g.setdefault('user', user)


def get_current_user():
    return g.get('user', None)

def set_current_device(device):
    return g.setdefault('device', device)

def get_current_device():
    return g.get('device', None)