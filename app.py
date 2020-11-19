#!/usr/bin/env python3

import logging

from flask import Flask, render_template
from flask_socketio import SocketIO
import jinja2 
import gevent

import sheet

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['SECRET_KEY'] = 'secret!'
#app.config['DEBUG'] = True
socketio = SocketIO(app, always_connect=True)

loader = jinja2.FileSystemLoader('/usr/src/app/templates')
env = jinja2.Environment(loader=loader, autoescape=False)

def update_text(**d):
    logger.info("Update: %r", d)
    socketio.emit('update_text', d, namespace="/overlay")
    
    
def clear_text():
    update_text(redteam="", blueteam="", middle="", time="", match="")

    
@socketio.on('connect', namespace="/overlay")
def handle_overlay_connect():
    logger.info("Connect")
    #update_text(redteam="Red", blueteam="Blue", match="R1", time="0:00", middle="Starting soon")
    
    #for i in range(30):
        #gevent.spawn_later(31-i, update_text, time="{min:02d}:{sec:02d}".format(min=i // 60, sec=i % 60))
    clear_text()
    next_match("R1")
    logger.info("Connect done")
    
    
def next_match(match_id):
    match = sheet.get_match(match_id);
    assert match
    update_text(
        redteam=match["Red Competitors"],
        blueteam=match["Blue Competitors"],
        match=match_id,
        middle="Starting soon")
    

if __name__ == '__main__':
    logger.info("Running")
    socketio.run(app, host="0.0.0.0", port=80)
    logger.info("Done")
