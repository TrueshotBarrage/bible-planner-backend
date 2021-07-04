import django_heroku

DEBUG = True

# ALLOWED_HOSTS = [
#     "bible-planner-backend.herokuapp.com", "127.0.0.1", "localhost"
# ]
ALLOWED_HOSTS = ["*"]

# Activate Django-Heroku.
django_heroku.settings(locals())