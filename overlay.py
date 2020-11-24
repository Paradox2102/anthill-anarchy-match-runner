#!/usr/bin/env python3

# Ths module provides the primitives that communicate to the overlay interface
# and the handlers that handle messages from it.

import config
import control

# These globals store the last value sent on various parts of the overlay
# We need to resend these if we get a "connect" message.
# Note: Not thread-safe, but doesn't seem to matter.
current_text = {} # dict of small text areas
current_table = ("", None) # id and HTML fragment.  Id is for debugging only.

def show_table(name="", content=None):
    """Shows arbitrary HTML fragment (usually a table) over full overlay screen."""
    config.socketio.emit('show_table', content, namespace="/overlay")
    global current_table
    current_table = (name, content)
    control.log_message(f"Show table {name}")

    
def play_audio(name):
    """Play an audio file in the overlay."""
    config.logger.info("Play audio: %s", name)
    config.socketio.emit('play_audio', name, namespace="/overlay")
    control.log_message(f"Play audio: {name}")
    config.socketio.sleep(0)
    

def update_text(clear=True, **d):
    """Update text in the overlay.  
    
    Args:
        clear: If set to false, existing text fields remain unchanged.   This is mainly used when setting the time.
        **d: Remaining keyword arguments are sent to the overlay interface.
        
    The overlay has five text areas, reflected in the additional keyword arguments:
        redteam: Top middle, styled in red, used for showing the name of the red competitor.
        blueteam: Bottom middle, styled in blue, used for showing the name of the blue competitor
        match: Middle left, neutral colour.  Used to show match number.
        middle: Middle middle, neutral colour.  Used to show important text when match not actually in progress.
        time: Middle right, neutral colour.  Used to show time remaining in match and countdown.
    
    TODO: Support swapping red and blue, and think about whether it should label the drive team or the anthill.
    """
    config.logger.info("Update text: %r", d)
    if clear:
        d = {**(dict(redteam="", blueteam="", middle="", time="", match="")), **d}
    global current_text
    current_text = {**current_text, **d}
    config.socketio.emit('update_text', d, namespace="/overlay")
    config.socketio.sleep(0)
        
    
@config.socketio.on('connect', namespace="/overlay")
def handle_overlay_connect():
    """Invoked when an overlay connects.  There will generally be three overlay connections during an event:
    * The overlay fetched by OBS to be used in the video stream.
    * The screen shown to competitors.
    * The iframe included in the control interface.  Note that this is muted to avoid competing noises.
    
    On connection, the current text and table (if any) are fetched from the globals and resent.
    """
    
    config.logger.info("Connect overlay")
    #update_text(redteam="Red", blueteam="Blue", match="R1", time="0:00", middle="Starting soon")
    
    #for i in range(30):
        #gevent.spawn_later(31-i, update_text, time="{min:02d}:{sec:02d}".format(min=i // 60, sec=i % 60))
    global current_text
    update_text(clear=False, **current_text)
    global current_table
    show_table(*current_table)
    config.logger.info("Connect overlay done")