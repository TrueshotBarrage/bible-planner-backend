import django_heroku

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Activate Django-Heroku.
django_heroku.settings(locals())