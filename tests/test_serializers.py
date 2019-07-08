import json

import pytest
from nap.serializers import BaseSerializer, JSONSerializer


def test_base_serializer():
    serializer = BaseSerializer()
    with pytest.raises(NotImplementedError):
        serializer.serialize({})

    with pytest.raises(NotImplementedError):
        serializer.deserialize('{}')


class TestJSONSerializer:
    def get_serializer(self):
        return JSONSerializer()

    def test_serialize(self):
        sample_dict = {
            'a': 1,
            'b': 2,
        }

        serializer = self.get_serializer()
        json_str = serializer.serialize(sample_dict)
        dict_from_json = json.loads(json_str)

        assert dict_from_json == sample_dict

    def test_deserialize(self):
        serializer = self.get_serializer()

        json_str = '{"a": 1, "b": 2}'
        json_dict = serializer.deserialize(json_str)

        assert json_dict['a'] == 1
        assert json_dict['b'] == 2
