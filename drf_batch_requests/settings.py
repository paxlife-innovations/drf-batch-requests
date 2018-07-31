from django.conf import settings
from django.test.signals import setting_changed


NAMESPACE = 'DRF_BATCH_REQUESTS'

DEFAULTS = {
    # Consumer backend
    'SUBREQ_CONSUMER_BACKEND':
    'drf_batch_requests.backends.sync.SyncRequestsConsumeBackend',

    # Subrequest ID settings
    'SUBREQ_ID_REQUIRED':
    True,

    'SUBREQ_ID_HEADER':
    'Content-ID',

    # Prefix for response ID header, including delimiter
    'SUBREQ_ID_RESPONSE_PREFIX':
    None,
}


class Config(object):
    """
    A config object, allowing config to be accessed as properties.
    """
    def __init__(self, user_config=None, defaults=None):
        self.defaults = defaults or DEFAULTS
        self._user_config = user_config
        self._cached_attrs = set()

    @property
    def user_config(self):
        if self._user_config is None:
            self._user_config = getattr(settings, NAMESPACE, {})
        return self._user_config

    def __getattr__(self, attr):
        # all valid user settings have defaults
        if attr not in self.defaults:
            raise AttributeError("Invalid %s setting: '%s'" % (NAMESPACE, attr))

        try:
            val = self.user_config[attr]
        except KeyError:
            val = self.defaults[attr]

        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, '_user_config'):
            delattr(self, '_user_config')


conf = Config(None, DEFAULTS)


def reload_conf(*args, **kwargs):
    setting = kwargs['setting']
    if setting == NAMESPACE:
        conf.reload()


setting_changed.connect(reload_conf)