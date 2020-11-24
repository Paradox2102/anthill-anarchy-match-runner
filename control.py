#!/usr/bin/env python3

# This module provides the handlers for messages from the control interface 
# and the primitives for communicating to the control interface.

import config
import sheet
import thread
import overlay

# These globals store the last value sent on various parts of the overlay
# We need to resend these if we get a "connect" message.
# Note: Not thread-safe, but doesn't seem to matter.
current_buttons = [] # list of button dicts

def log_message(message):
    """This sends a log message to the control interface.
    This is printed on-screen and also sent to log.
    """
    config.socketio.emit('log_message', message, namespace="/control")
    config.socketio.sleep(0)
    print(message)


def set_buttons(buttons, clear=True):
    """Sets the buttons in the interface.
    TODO: Add button colours, sections.
    
    Args:
        buttons: List of dicts with fields:
            event: Event to invoke on the websocket.
            label: Text for button.
            arg: Argument to send in event.
        clear: If set to false, then new buttons are appended to existing ones.
    """
            
    config.logger.info("Setting buttons: %r", buttons)
    global current_buttons
    current_buttons = buttons
    config.socketio.emit('set_buttons', dict(buttons=buttons, clear=clear), namespace="/control")
    
    
@config.socketio.on('next_match', namespace="/control")
def next_match(match_id):
    """Display a message in the overlay about which match is starting next.
    Changes buttons to start and cancel.
    
    Args:
        match_id: E.g. "R1"
    """
    thread.set_thread()
    match = sheet.get_match(match_id);
    assert match
    log_message(f"Next match {match_id}")
    overlay.update_text(
        redteam=match["Red Competitors"],
        blueteam=match["Blue Competitors"],
        middle=f"Next match<br/>{match_id}<br/>Starting soon")
    set_buttons([
        dict(event="start_match", arg=match_id, label=f"Start match {match_id}"),
        dict(event="abort_match", arg="", label=f"Cancel next match {match_id}"),
    ])
    
    
@config.socketio.on('abort_match', namespace="/control")
def abort_match(match_id):
    """Returns to cycling, whatever is happening.  Can be used as a general abort on a specific match regardless of state.
    
    Args:
        match_id: Identifer for match being aborted.  Used only for logging.
    """
    log_message(f"Aborting match {match_id}")
    thread.cycle()
    
   
@config.socketio.on('start_match', namespace="/control")
def start_match(match_id):
    """Starts the runner for a match.
    The button for this will only be available when this match is next.
    
    Args:
        match_id: Identifier like "R1".
    """
    overlay.update_text(middle=f"Starting Match {match_id}")
    thread.set_thread(thread.MatchThread(match_id))
    
    
@config.socketio.on('show_match_scores', namespace="/control")
def show_match_scores(match_id):
    """Show scores for a specific match.
    Button only available after match has run to completion."""
    thread.set_thread(thread.MatchScoreThread(match_id))
    
    
@config.socketio.on('connect', namespace="/control")
def handle_control_connect():
    """Invoked when the control interface connects.
    Sends current buttons.
    Should only be one of these at a time.
    """
    config.logger.info("Connect control")
    log_message("Connected")
    global current_buttons
    set_buttons(current_buttons)
    config.logger.info("Connect control done")
    if config.impatient:
        log_message("Warning: Impatient mode is set, so many times are much shorter than they should be")