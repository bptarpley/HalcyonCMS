from django.utils.html import escape


class SiteResponse(object):

    def __init__(self, user=None):
        self.fname = ''

        if user:
            if user.is_authenticated:
                self.fname = user.first_name

        self.messages = []
        self.errors = []
        self.success = ""


def _contains(obj, keys):
    has_keys = True
    for k in keys:
        if not k in obj:
            has_keys = False
    return has_keys


def _clean(obj, key, default_value=''):
    return escape(obj.get(key, default_value))