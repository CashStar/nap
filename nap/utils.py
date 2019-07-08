import itertools
from operator import itemgetter
from urllib.parse import urlencode


def handle_slash(url, add_slash=None):
    split = url.split('?')

    if add_slash and not split[0].endswith('/'):
        if len(split) > 1:
            url = '{}/?{}'.format(split[0], split[1])
        else:
            url = '{}/'.format(url)
    elif add_slash is False and split[0].endswith('/'):
        if len(split) > 1:
            url = "{}?{}".format(split[0][:-1], split[1])
        else:
            url = split[0][:-1]

    return url


def is_string_like(obj):
    return isinstance(obj, str)


def safe_encode(value):
    if isinstance(value, str):
        return value.encode('utf-8')
    return value


def make_url(base_url, params=None, add_slash=None):
    """Split off in case we need to handle more scrubbing."""

    base_url = handle_slash(base_url, add_slash)

    if params:
        # If we're given an non-string iterable as a params value,
        # we want to pass in multiple instances of that param key.
        def flatten_params(k, vs):
            if not hasattr(vs, '__iter__') or is_string_like(vs):
                return (k, safe_encode(vs)),
            return [(k, safe_encode(v)) for v in vs]

        flat_params = [
            flatten_params(k, v)
            for (k, v) in params.items()
        ]

        # since we can have more than one value for a single key, we use a
        # tuple of two tuples instead of a dictionary
        params_tuple = tuple(
            sorted(itertools.chain(*flat_params), key=itemgetter(0))
        )
        param_string = urlencode(params_tuple)
        base_url = '{}?{}'.format(base_url, param_string)

    return base_url


def to_unicode(s):
    if s is None:
        return None

    # unicode strings
    elif isinstance(s, str):
        return s

    # non-unicode strings
    elif isinstance(s, bytes):
        return str(s, 'utf-8')

    # non-string types
    else:
        return str(s)
