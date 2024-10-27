from core.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ExpCenterDb',
        'USER': 'wya',
        'PASSWORD': 'Yygzdnl!0627',
        'HOST': 'mysql',
        'PORT': '3306',
    }
}