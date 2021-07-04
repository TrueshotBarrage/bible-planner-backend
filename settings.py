import django_heroku

ALLOWED_HOSTS = [
    '127.0.0.1', 'localhost', "bible-planner-backend.herokuapp.com"
]

# Activate Django-Heroku.
django_heroku.settings(locals())