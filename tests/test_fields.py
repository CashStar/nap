import datetime
from decimal import Decimal

import pytest
from nap.fields import (
    DateField,
    DateTimeField,
    DecimalField,
    DictField,
    Field,
    ListField,
    ResourceField,
    SimpleListField
)
from tests import AuthorModel


class TestFields:
    def test_field(self):
        field = Field(default='xyz')

        assert field.get_default() == 'xyz'
        assert field.scrub_value('123') == '123'

    def test_readonly(self):
        field = Field()
        assert field.readonly is False

        readonly_field = Field(readonly=True)
        assert readonly_field.readonly is True

        pk_field = Field(resource_id=True)
        assert pk_field.readonly is True

        pk_readonly_field = Field(resource_id=True, readonly=False)
        assert pk_readonly_field.readonly is False

    def test_resource_field(self):
        field = ResourceField(AuthorModel)

        assert field.scrub_value('') is None
        assert field.descrub_value('') is None

        author_dict = {
            'name': 'Jacob',
            'email': 'elitist@gmail.com',
        }

        resource = field.scrub_value(author_dict)
        assert resource.name == 'Jacob'
        assert resource.email == 'elitist@gmail.com'

        new_author_dict = field.descrub_value(resource)

        assert new_author_dict == author_dict

        assert field.coerce(resource) == resource

    def test_list_field(self):
        field = ListField(AuthorModel)

        author_dict_list = [
            {
                'name': 'Jacob',
                'email': 'elitist@gmail.com',
            },
            {
                'name': 'Bob',
                'email': None
            },
            {
                'name': 'Jane',
                'email': 'jane@doe.com',
            }
        ]
        resource_list = field.scrub_value(author_dict_list)

        assert len(resource_list) == 3
        assert resource_list[0].name == 'Jacob'
        assert resource_list[1].name == 'Bob'
        assert resource_list[2].name == 'Jane'

        assert resource_list[0].email == 'elitist@gmail.com'
        assert resource_list[1].email is None
        assert resource_list[2].email == 'jane@doe.com'

        new_author_dict_list = field.descrub_value(resource_list)

        assert new_author_dict_list == author_dict_list

    def test_empty_list_field(self):
        field = ListField(AuthorModel)
        for val in ('', None, {}):
            for result in (field.scrub_value(val), field.descrub_value(val)):
                assert hasattr(result, '__iter__')
                assert len(result) == 0

    def test_empty_dict_field(self):
        field = DictField(AuthorModel)
        for val in ('', None, {}):
            for result in (field.scrub_value(val), field.descrub_value(val)):
                assert hasattr(result, 'keys')
                assert len(result) == 0

    def test_dict_field(self):
        field = DictField(AuthorModel)
        author_dict_dict = {
            'main': {
                'name': 'Jacob',
                'email': 'elitist@gmail.com',
            },
            'ghost_writer': {
                'name': 'Bob',
                'email': None,
            },
        }
        resource_dict = field.scrub_value(author_dict_dict)

        assert len(resource_dict.keys()) == 2
        assert resource_dict['main'].name == 'Jacob'
        assert resource_dict['main'].email == 'elitist@gmail.com'

        assert resource_dict['ghost_writer'].name == 'Bob'

        new_author_dict_dict = field.descrub_value(resource_dict)
        assert new_author_dict_dict == author_dict_dict

    def test_datetime_field(self):
        field = DateTimeField()

        dt_str = '2012-08-21T22:30:14'
        expected_dt = datetime.datetime(year=2012, month=8, day=21,
                                        hour=22, minute=30, second=14)
        assert field.scrub_value(dt_str) == expected_dt
        assert field.descrub_value(expected_dt) == dt_str

        # make sure microseconds is stripped
        micro_dt_str = '2012-08-21T22:30:14.24234234'
        assert field.scrub_value(micro_dt_str) == expected_dt
        assert field.descrub_value(expected_dt) == dt_str

    def test_empty_datetime_field(self):

        field = DateTimeField()
        assert field.scrub_value(None) is None
        assert field.descrub_value(None) is None

    def test_datetime_field_new_dt_format(self):
        boring_format = '%Y-%m-%d %H:%M:%S'
        field = DateTimeField(dt_format=boring_format)

        dt_str = '2010-06-02 16:30:06'
        expected_dt = datetime.datetime(year=2010, month=6, day=2,
                                        hour=16, minute=30, second=6)
        assert field.scrub_value(dt_str) == expected_dt
        assert field.descrub_value(expected_dt) == dt_str

        field = DateTimeField(dt_formats=(boring_format, '%Y-%m-%dT%H:%M:%S'))
        dt_str2 = '2010-06-02T16:30:06'
        bad_string = '2010/06/02 16:30 06 seconds'
        expected_dt = datetime.datetime(year=2010, month=6, day=2,
                                        hour=16, minute=30, second=6)
        assert field.scrub_value(dt_str) == expected_dt
        assert field.scrub_value(dt_str2) == expected_dt
        assert field.descrub_value(expected_dt) == dt_str

        with pytest.raises(ValueError):
            field.scrub_value(bad_string)

        # make sure microseconds is stripped
        micro_dt_str = '2010-06-02 16:30:06.24234234'
        assert field.scrub_value(micro_dt_str) == expected_dt
        assert field.descrub_value(expected_dt) == dt_str

    def test_date_field(self):
        field = DateField()

        dt_str = '2012-08-21'
        expected_dt = datetime.date(year=2012, month=8, day=21)
        assert field.scrub_value(dt_str) == expected_dt
        assert field.descrub_value(expected_dt) == dt_str

    def test_empty_date_field(self):
        field = DateField()
        assert field.scrub_value(None) is None
        assert field.descrub_value(None) is None

    def test_date_field_new_dt_format(self):
        american_format = '%m/%d/%Y'
        field = DateField(dt_format=american_format)

        dt_str = '08/21/2012'
        expected_dt = datetime.date(year=2012, month=8, day=21)
        assert field.scrub_value(dt_str) == expected_dt
        assert field.descrub_value(expected_dt) == dt_str

        field = DateField(dt_formats=(american_format, '%Y-%m-%d'))
        dt_str2 = '08/21/2012'
        bad_string = '2010~06~02'
        expected_dt = datetime.date(year=2012, month=8, day=21)
        assert field.scrub_value(dt_str) == expected_dt
        assert field.scrub_value(dt_str2) == expected_dt
        assert field.descrub_value(expected_dt) == dt_str

        with pytest.raises(ValueError):
            field.scrub_value(bad_string)

    def test_simple_list_field(self):
        field = SimpleListField()

        # existing list returns the same list
        assert [1, 2, 3, 4] == field.scrub_value([1, 2, 3, 4])

        # existing tuple
        assert [123] == field.scrub_value(123,)

        # None results in an empty list for ease of use
        assert [] == field.scrub_value(None)

        # Single values become a single item list
        assert ['1234'] == field.scrub_value('1234')
        assert ['0'] == field.scrub_value('0')
        assert [''], field.scrub_value('')

        # ---- descrub
        # existing list returns the same list
        assert [1, 2, 3, 4] == field.descrub_value([1, 2, 3, 4])

        # existing tuple
        assert [123] == field.descrub_value(123,)

        # None results in an empty list for ease of use
        assert [] == field.descrub_value(None)

        # Single values become a single item list
        assert ['1234'] == field.descrub_value('1234')
        assert ['0'] == field.descrub_value('0')
        assert [''], field.descrub_value('')

    def test_decimal_field(self):
        # Given a decimal field
        field = DecimalField()

        # When de-serialized values are provided
        # Then it converts them to Decimals
        assert Decimal('10.0') == field.scrub_value(Decimal('10.0'))
        assert Decimal('10.0') == field.scrub_value('10.0')
        assert Decimal('10.0') == field.scrub_value(float('10.0'))
        assert Decimal('0') == field.scrub_value(Decimal('0.0'))
        assert Decimal('0') == field.scrub_value('0.0')
        assert Decimal('0') == field.scrub_value(float('0.0'))

        # When empty de-serialized values are provided
        # Then it converts them to None
        assert field.scrub_value(None) is None
        assert field.scrub_value('') is None

        # When serialized values are provided
        # Then it converts them to strings
        assert '10.0' == field.descrub_value(Decimal('10.0'))
        assert '10.0' == field.descrub_value('10.0')
        assert '10.0' == field.descrub_value(float('10.0'))
        assert '0.0' == field.descrub_value(Decimal('0.0'))
        assert '0.0' == field.descrub_value('0.0')
        assert '0.0' == field.descrub_value(float('0.0'))

        # When empty serialized values are provided
        # Then it converts them to None
        assert field.descrub_value(None) is None
        assert field.descrub_value('') is None
