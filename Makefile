VERSION=0.0.1
default: test

test:
	DJANGO_SETTINGS_MODULE=tests.django_settings python setup.py test

.PHONY: build watch
