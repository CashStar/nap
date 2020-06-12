from nap.conf import NapConfig
from nap.exceptions import EmptyResponseError
from nap.fields import Field, ResourceField
from nap.engine import OpaqueFilterResourceEngine
from nap.lookup import default_lookup_urls
from nap.utils import to_unicode


class DataModelMetaClass(type):
    def __new__(mcs, name, bases, attrs):
        super_new = super().__new__
        parents = [b for b in bases if isinstance(b, DataModelMetaClass)]
        if not parents:
            return super_new(mcs, name, bases, attrs)

        model_cls = super_new(mcs, name, bases, attrs)
        fields = {}

        options = attrs.pop('Meta', None)
        default_name = model_cls.__name__.lower()
        resource_name = getattr(options, 'resource_name', default_name)

        urls = getattr(options, 'urls', default_lookup_urls)
        append_urls = tuple(getattr(options, 'append_urls', ()))
        prepend_urls = tuple(getattr(options, 'prepend_urls', ()))

        urls = prepend_urls + urls + append_urls

        meta_conf = {}
        for key in dir(options):
            if not key.startswith('__'):
                meta_conf[key] = getattr(options, key)

        _meta = NapConfig(
            meta_conf,
            resource_name=resource_name,
            urls=urls,
        )

        for name, attr in attrs.items():
            if isinstance(attr, Field):
                attr._name = name
                fields[name] = attr
                setattr(model_cls, name, attr)

                if attr.resource_id:
                    _meta['resource_id_field_name'] = name

        _meta['fields'] = fields
        setattr(model_cls, '_meta', _meta)

        setattr(model_cls, 'objects', _meta['engine_class'](model_cls))

        return model_cls


class ResourceModel(metaclass=DataModelMetaClass):
    def __init__(self, *args, **kwargs):
        """Construct a new model instance."""

        self._root_url = kwargs.get('root_url', self._meta['root_url'])
        self._request_args = kwargs.pop('request_args', {})

        self._saved = False
        self.update_fields(kwargs)

    def __eq__(self, other):
        if hasattr(other, 'to_python'):
            return self.to_python(for_read=True) == other.to_python(
                for_read=True
            )

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def update_fields(self, field_data):
        """Update object's values to values of field_data.

        :param field_data: dict-like object with 'Field Name'->'New  Value'
        """

        self._raw_field_data = field_data
        model_fields = self._meta['fields']
        api_name_map = {
            field.api_name or name: name
            for name, field in model_fields.items()
        }

        extra_data = set(field_data.keys()) - set(api_name_map.keys())
        for api_name, field_name in api_name_map.items():
            model_field = model_fields[field_name]

            if api_name in field_data:
                value = model_field.scrub_value(field_data[api_name])
            else:
                value = model_field.get_default()

            setattr(self, field_name, value)

        self.extra_data = {
            key: field_data[key]
            for key in extra_data
        }

    def update(self, **kwargs):
        """Shortcut function to force an update on an object."""

        obj = self.objects.update(self, **kwargs)
        if self._meta['update_from_write']:
            if not obj:
                raise EmptyResponseError(
                    'Cannot update fields: '
                    'update_from_write is True but no object was returned'
                )
            self.update_fields(obj._raw_field_data)

    def delete(self, **kwargs):
        self.objects.delete(self, **kwargs)
        self.resource_id = None

    def save(self, **kwargs):
        """Contextually save current object. If an object can generate an
        update URL, send an update command. Otherwise, create.
        """

        request_kwargs = kwargs.pop('request_kwargs', {})
        update_url = self.objects.get_update_url(self)
        if self._saved or self.full_url or update_url:
            obj = self.objects.modify_request(
                **request_kwargs
            ).update(self, **kwargs)
        else:
            obj = self.objects.modify_request(
                **request_kwargs
            ).create(self, **kwargs)

        if self._meta['update_from_write']:
            if not obj:
                raise EmptyResponseError(
                    'Cannot update fields: '
                    'update_from_write is True but no object was returned'
                )
            self.update_fields(obj._raw_field_data)

    # utility methods
    def to_python(self, for_read=False):
        """Converts editable field data to a python dictionary.

        :param for_read: include readonly fields.
        """

        obj_dict = {
            field_name: field.descrub_value(
                getattr(self, field_name), for_read
            )
            for field_name, field in self._meta['fields'].items()
            if for_read or field.readonly is False
        }

        return obj_dict

    @property
    def cache_key(self):

        # This really needs to be cleaned up
        lookup_url = self.objects.get_lookup_url(self)
        full_url = self.objects.get_full_url(lookup_url)
        cache_key = self.objects.cache.get_cache_key(self.__class__, full_url)

        return cache_key

    # properties
    @property
    def full_url(self):
        """"Return a pre-set resource URL if available."""

        return getattr(self, '_full_url', None)

    @property
    def _resource_id_name(self):
        return self._meta.get('resource_id_field_name', None)

    @property
    def logger(self):
        return self._meta['logger']

    @property
    def resource_id(self):
        """Return object's resource_id value. Returns None if not available"""

        if not self._resource_id_name:
            return None

        return getattr(self, self._resource_id_name, None)

    @resource_id.setter
    def resource_id(self, resource_id_value):
        """Set object's resource_id field to ``resource_id_value``."""

        if not self._resource_id_name:
            return None

        setattr(self, self._resource_id_name, resource_id_value)

    # etc
    def __unicode__(self):
        val = to_unicode(self.resource_id)
        return val or ''

    def __repr__(self):
        val = '<{}: {}>'.format(self.__class__.__name__, self.__unicode__())
        return val


class OpaqueFilterResourceModel(ResourceModel):
    @staticmethod
    def recursive_resource_field_generator(parent_class, name, value):
        if isinstance(value, dict):
            # Use type to dynamically define new ResourceModel class
            temp_resource_class_name = ''.join([w.capitalize() for w in name.split('_')]) + 'Resource'
            temp_resource_class = type(temp_resource_class_name, (ResourceModel,), {})
            for sub_name, sub_value in value.items():
                OpaqueFilterResourceModel.recursive_resource_field_generator(temp_resource_class, sub_name, sub_value)
            temp_field = ResourceField(temp_resource_class)

        else:
            temp_field = Field()

        # see DataModelMetaClass.__new__
        temp_field._name = name
        parent_class._meta['fields'][name] = temp_field
        setattr(parent_class, name, temp_field)

    @classmethod
    def update_resource_fields(cls, attributes):
        """Dynamically setting Resource fields based off response fields"""
        for attribute_name, attribute_value in attributes.items():
            if not hasattr(cls, attribute_name):
                OpaqueFilterResourceModel.recursive_resource_field_generator(cls, attribute_name, attribute_value)

    class Meta:
        engine_class = OpaqueFilterResourceEngine
