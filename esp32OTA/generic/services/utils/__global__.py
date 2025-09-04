from flask import g


def set_current_user(user):
    return g.setdefault('user', user)


def get_current_user():
    return g.get('user', None)
