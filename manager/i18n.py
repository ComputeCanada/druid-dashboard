# vi: set softtabstop=2 ts=2 sw=2 expandtab:
# pylint:
#
from flask import request
from flask_babel import Babel

# languages are not configurable
SUPPORTED_LANGUAGES = ['en', 'fr']

# declare Babel object to be initialized in factory
babel = Babel()

@babel.localeselector
def get_locale():
  return request.accept_languages.best_match(SUPPORTED_LANGUAGES) or 'en'
