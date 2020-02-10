DEBUG = True

ALLOWED_HOSTS = ['*']

STATIC_ROOT = '/web/static/'

PRODUCTION = True

ADMIN_WEBSITE_HEADER = 'Stock Crawler'

if PRODUCTION:
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': '',
                'USER': '',
                'PASSWORD': '',
                'HOST': '127.0.0.1',
                'PORT': '3306',
                'TEST': {
                    'CHARSET': 'utf8',
                    'COLLATION': 'utf8_general_ci',
                }
            },
        }
else:
    DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': '',
                'USER': '',
                'PASSWORD': '',
                'HOST': '127.0.0.1',
                'PORT': '3306',
                'TEST': {
                    'CHARSET': 'utf8',
                    'COLLATION': 'utf8_general_ci',
                }
            },
        }

# Celery Task Basic Settings
CRAWLER_TASK_SOFTTIMELIMIT = 6 * 60 * 60
CRAWLER_TASK_TIMELIMIT = CRAWLER_TASK_SOFTTIMELIMIT + 10

NORMAL_TASK_SOFTTIMELIMIT = 60
NORMAL_TASK_TIMELIMIT = NORMAL_TASK_SOFTTIMELIMIT + 10
