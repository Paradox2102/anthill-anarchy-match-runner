#!/usr/bin/env python3

import logging

from flask import Flask
from flask_socketio import SocketIO
import jinja2
import eventlet
eventlet.monkey_patch() # Changes the behaviour of "import time"

# Note: this module won't work without a "service-credentials.json" file, 
# for a Google Service account that has read access to the spreadsheet.
# For security reasons, this file is not included in the github repo.
import sheet

# If set to true, this reduces the time of various things like running the match and showing a table.
# This makes it easier to test and debug.  Set it to false for actual competition.
impatient = False 

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)

# Serve files from local static folder
app = Flask(__name__, static_url_path='', static_folder='static')

app.config['SECRET_KEY'] = 'secret!'
#app.config['DEBUG'] = True
socketio = SocketIO(app, always_connect=True)
# Note that there are two namespaces in use here:
# * overlay: This is output-only and is used as an overlay over the video feed.
# * control: This is an interface that consists of buttons that change behaviour.

# Load Jinja2 templates from template folder
_loader = jinja2.FileSystemLoader('template')
env = jinja2.Environment(loader=_loader, autoescape=False)