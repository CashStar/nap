from unittest import mock

from nap.exceptions import InvalidStatusError, BadRequestError


def test_invalid_status():
    statuses = (200, 201)
    response = mock.Mock()
    response.status_code = 404
    response.url = 'naprulez.org'
    e = InvalidStatusError(statuses, response)
    try:
        raise e
    except InvalidStatusError as e:
        expected = InvalidStatusError.ERROR_MSG.format(
            statuses, 404, 'naprulez.org'
        )
        assert str(e) == expected


def test_bad_request():
    response = mock.Mock()
    errors = {'your_field': 'has errors!'}
    e = BadRequestError(response, errors)
    try:
        raise e
    except BadRequestError as e:
        assert e.args[0] == errors
        assert e.response == response
        assert issubclass(e.__class__, InvalidStatusError)
