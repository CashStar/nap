from nap.conf import NapConfig, DEFAULT_CONFIG
from nap.auth import BaseAuthorization


def test_config_defaults():
    config = NapConfig()

    for key, value in DEFAULT_CONFIG.items():
        assert config[key] == value


def test_config_override():

    new_options = {
        'override_methood': 'PATCH',
        'add_slash': False,
    }

    config = NapConfig(
        new_options,
        collection_field='objects',
        override_method='POST'
    )

    assert config['override_method'] == 'POST'
    assert config['collection_field'] == 'objects'
    assert config['add_slash'] is False


def test_auth_added_to_middleware():

    conf_dict = {
        'auth': (BaseAuthorization,)
    }
    config = NapConfig(conf_dict)

    assert config['middleware'] == conf_dict['auth']
