import sys
sys.path.insert(0, '/var/www/progs/chat-app')

import logging
# for log to apache logs.
logging.basicConfig(stream = sys.stderr)

import os

os.environ['FLASK_APP'] = 'flaskr'
os.environ['FLASK_ENV'] = 'development'
os.environ['OPENAI_API_KEY'] = '<API Key of OpenAI API>'
os.environ['GOOGLE_AI_API_KEY'] = '<API Key of Google AI API>'
os.environ['REMOTE_URL'] = '/chat-evil'
os.environ['MODERATION_ACCESS_KEY'] = 'oki87uy6:testuser'
os.environ['SECRET_KEY'] = '0okju7654rewsd'

from flaskr import app as application
