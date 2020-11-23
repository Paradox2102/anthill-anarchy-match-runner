#!/usr/bin/env python3

import logging
import threading 
import math

from flask import Flask, render_template
from flask_socketio import SocketIO
import jinja2 
#import gevent
#import gevent.time as time
import eventlet
eventlet.monkey_patch()
import time

# Note: this module won't work without a "service-credentials.json" file, 
# for a Google Service account that has read access to the spreadsheet.
# For security reasons, this file is not included in the github repo.
import sheet

impatient = False # For debugging and testing; set to false for competition

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)

# Server files from local static folder
app = Flask(__name__, static_url_path='', static_folder='static')

app.config['SECRET_KEY'] = 'secret!'
#app.config['DEBUG'] = True
socketio = SocketIO(app, always_connect=True)
# Note that there are two namespaces in use here:
# * overlay: This is output-only and is used as an overlay over the video feed.
# * control: This is an interface that consists of buttons that change behaviour.

# Load Jinja2 templates from template folder
loader = jinja2.FileSystemLoader('template')
env = jinja2.Environment(loader=loader, autoescape=False)

# Pointed to the current thread object so it can be stopped.
current_thread = None 

# These globals store the last value sent on various parts of the overlay
# We need to resend these if we get a "connect" message.
# Note: Not thread-safe, but doesn't seem to matter.
current_buttons = [] # list of button dicts
current_text = {} # dict of small text areas
current_table = ("", None) # id and HTML fragment.  Id is for debugging only.


class Thread(threading.Thread):
    """
    This is an abstract parent class for the various threads that we might run to update the overlay.
    It mainly exists to support stopping.  Clients should check "is_stopped" and use the provided "sleep" method.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_event = threading.Event()
        
    def stop(self):
        """Set flag to say stopped.  Thread-safe."""
        logger.info(f"Stopping thread {self.name}")
        self.stop_event.set()
        
    def is_stopped(self):
        """Check stopped flag.  Thread-safe."""
        return self.stop_event.is_set()
        
    def sleep(self, sleep_time):
        """Like time.sleep(), except checks "is_stopped" and raises Exception.
        If called with times longer than one second, will check every second."""
        if self.is_stopped():
            raise Exception(f"Thread {self.name} stopped")
        start = time.time()
        while True:
            sleep_remaining = sleep_time + start - time.time()
            if sleep_remaining <= 0: break
            time.sleep(min(sleep_remaining, 1))
            if self.is_stopped():
                raise Exception(f"Thread {self.name} stopped")
        
        
class MatchThread(Thread):
    """Run a match from countdown to "scoring in progress".
    """
    # These constants control the timing of the game.  All are in seconds.
    match_length = 10 if impatient else 120 # Length of match play
    count_down = 3 # Number of beeps before match play
    count_down_delay = 2 # delay between pushing button and countdown starting
    end_game = 5 if impatient else 10 # When to sound warning during match play
    
    def __init__(self, match_id):
        super().__init__(name="Match " + match_id)
        self.match_id = match_id
        self.match = sheet.get_match(match_id)
    
    def run(self):
        update_text(
            redteam=self.match["Red Competitors"],
            blueteam=self.match["Blue Competitors"],
            match=self.match_id,
            time="Starting",
        )
        
        set_buttons([dict(event='abort_match', arg=self.match_id, label=f"Abort match {self.match_id}")])

        old_seconds = self.match_length + self.count_down + self.count_down_delay
        now = time.time()
        end_time = now + old_seconds
        logger.info(f"Running match {self.match_id} from {now} to {end_time}")
        
        while not self.is_stopped():
            current_time = time.time()
            seconds = math.ceil(end_time - current_time)
            
            if seconds != old_seconds:
                logger.info(f"Match {self.match_id}, seconds={seconds}")
                old_seconds = seconds
                
                if seconds < 0: # Game over
                    update_text(middle="Game Over!<br/><br/>Scoring in Progress", clear=False)
                    set_buttons([
                        dict(event='show_match_scores', arg=self.match_id,
                             label=f"Show scores for match {self.match_id}"),
                        dict(event='abort_match', arg=self.match_id,
                             label=f"Abandon match {self.match_id}"),
                    ])
                    break
                else:
                    # Set time field
                    if seconds <= self.match_length: 
                        # During match
                        update_text(time="{min:02d}:{sec:02d}".format(min=seconds // 60, sec=seconds % 60), clear=False)
                    elif seconds > self.match_length and seconds <= self.match_length + self.count_down:
                        # Countdown
                        update_text(time=(seconds - self.match_length), clear=False)
                        
                    # Play sound
                    if seconds == 0:
                        play_audio('end')
                    elif seconds == self.end_game:
                        play_audio('warning')
                    elif seconds == self.match_length:
                        play_audio('start')
                    elif seconds > self.match_length and seconds <= self.match_length + self.count_down:
                        play_audio('countdown')
            self.sleep(0.25) # avoid skipping seconds because of oversleeping

            
class DefaultThread(Thread):
    """This thread runs by default if we're not showing anything special.
    It alternates between a table of teams, and a table of matches.
    Note: This ought to change behaviour for finals.
    """
    sleep_time = 5 if impatient else 10 
    n_qualifying_rounds = 10 # TODO: Don't hard-code this!
    
    def __init__(self):
        super().__init__(name="Default")
        #methods = [self.show_matches, self.show_team]
        
    def run(self):
        # Create buttons for starting every possible match.
        # Note: We could program this only to offer the next match, but then we could not choose to play out of order.
        # Note: We could hide complete matches, but then we could not choose to replay a match.
        # TODO: Colour buttons by whether the matches already have scores
        buttons = [dict(event="next_match", arg=match['Match'], label=f"Next match {match['Match']}") 
                   for match in sheet.get_matches()]
        set_buttons(buttons)

        try:
            while not self.is_stopped():
                self.sleep(self.sleep_time)
                # Only show qualifying rounds, not final playoffs.
                matches = sheet.get_matches(flush=True)[:self.n_qualifying_rounds]
                text = env.get_template('match.html').render(matches=matches)
                logger.info(f"Match table: {text}")
                show_table("Matches", text)
                self.sleep(self.sleep_time)   
                show_table("", None)

                self.sleep(self.sleep_time)                   
                teams = sheet.get_teams(flush=True)
                teams = sorted(teams, key=lambda t: (t['Rank'], t['Team']))
                logger.info(f"Sorted teams: {teams}")
                text = env.get_template('team.html').render(teams=teams)
                logger.info(f"Team table: {text}")
                show_table("Teams", text)
                
                self.sleep(self.sleep_time)   
                show_table("", None)
        finally:
            show_table("", None)
            

class MatchScoreThread(Thread):
    """Show the results of a single match.  
    Only available after completing a match, and automatically ends after 30 seconds."""
    sleep_time = 5 if impatient else 30
    
    def __init__(self, match_id):
        super().__init__(name="Match " + match_id)
        self.match_id = match_id
        self.match = sheet.get_match(match_id)
        
    def run(self):
        try:
            update_text()
            match = sheet.get_match(self.match_id, flush=True)
            text = env.get_template('match_score.html').render(match=match)
            logger.info(f"Match score table: {text}")
            show_table("Match", text)
            set_buttons([dict(event='abort_match', arg=self.match_id,
                              label=f"Abandon match {self.match_id}")]);
            self.sleep(self.sleep_time)
        finally:
            show_table("", None)

        set_thread(DefaultThread())
    

def show_table(name, content):
    """Shows arbitrary HTML fragment (usually a table) over full overlay screen."""
    socketio.emit('show_table', content, namespace="/overlay")
    global current_table
    current_table = (name, content)
    log_message(f"Show table {name}")

    
def play_audio(name):
    """Play an audio file in the overlay."""
    logger.info("Play audio: %s", name)
    socketio.emit('play_audio', name, namespace="/overlay")
    log_message(f"Play audio: {name}")
    socketio.sleep(0)
    

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
    logger.info("Update text: %r", d)
    if clear:
        d = {**(dict(redteam="", blueteam="", middle="", time="", match="")), **d}
    global current_text
    current_text = {**current_text, **d}
    socketio.emit('update_text', d, namespace="/overlay")
    socketio.sleep(0)
        
    
@socketio.on('connect', namespace="/overlay")
def handle_overlay_connect():
    """Invoked when an overlay connects.  There will generally be three overlay connections during an event:
    * The overlay fetched by OBS to be used in the video stream.
    * The screen shown to competitors.
    * The iframe included in the control interface.  Note that this is muted to avoid competing noises.
    
    On connection, the current text and table (if any) are fetched from the globals and resent.
    """
    
    logger.info("Connect overlay")
    #update_text(redteam="Red", blueteam="Blue", match="R1", time="0:00", middle="Starting soon")
    
    #for i in range(30):
        #gevent.spawn_later(31-i, update_text, time="{min:02d}:{sec:02d}".format(min=i // 60, sec=i % 60))
    global current_text
    update_text(clear=False, **current_text)
    global current_table
    show_table(*current_table)
    logger.info("Connect overlay done")
    
    
def log_message(message):
    """This sends a log message to the control interface.
    This is printed on-screen and also sent to log.
    """
    socketio.emit('log_message', message, namespace="/control")
    socketio.sleep(0)
    print(message)


@socketio.on('next_match', namespace="/control")
def next_match(match_id):
    """Display a message in the overlay about which match is starting next.
    Changes buttons to start and cancel.
    
    Args:
        match_id: E.g. "R1"
    """
    set_thread()
    match = sheet.get_match(match_id);
    assert match
    log_message(f"Next match {match_id}")
    update_text(
        redteam=match["Red Competitors"],
        blueteam=match["Blue Competitors"],
        middle=f"Next match<br/>{match_id}<br/>Starting soon")
    set_buttons([
        dict(event="start_match", arg=match_id, label=f"Start match {match_id}"),
        dict(event="cycle", arg="", label=f"Cancel next match {match_id}"),
    ])

    
def set_thread(thread=None):
    """Stops the current thread (if any) and launches a new thread (if not None)."""
    logger.info(f"set thread {thread}", exc_info=True)
    global current_thread
    if None != current_thread:
        current_thread.stop()
    current_thread = thread
    if None != thread:
        thread.start()
    
    
def cycle():
    """This invokes the default thread to cycle between interesting tables.
    """
    update_text();
    buttons = [dict(event="next_match", arg=match['Match'], label=f"Next match {match['Match']}") 
               for match in sheet.get_matches()]
    set_buttons(buttons)
    set_thread(DefaultThread())
    
    
@socketio.on('abort_match', namespace="/control")
def abort_match(match_id):
    """Returns to cycling, whatever is happening.  Can be used as a general abort on a specific match regardless of state.
    
    Args:
        match_id: Identifer for match being aborted.  Used only for logging.
    """
    log_message(f"Aborting match {match_id}")
    cycle()
    
   
@socketio.on('start_match', namespace="/control")
def start_match(match_id):
    """Starts the runner for a match.
    The button for this will only be available when this match is next.
    
    Args:
        match_id: Identifier like "R1".
    """
    update_text(middle=f"Starting Match {match_id}")
    set_thread(MatchThread(match_id))
    
    
@socketio.on('show_match_scores', namespace="/control")
def show_match_scores(match_id):
    """Show scores for a specific match.
    Button only available after match has run to completion."""
    set_thread(MatchScoreThread(match_id))
    
    
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
            
    logger.info("Setting buttons: %r", buttons)
    global current_buttons
    current_buttons = buttons
    socketio.emit('set_buttons', dict(buttons=buttons, clear=clear), namespace="/control")
    
    
@socketio.on('connect', namespace="/control")
def handle_control_connect():
    """Invoked when the control interface connects.
    Sends current buttons.
    Should only be one of these at a time.
    """
    logger.info("Connect control")
    log_message("Connected")
    global current_buttons
    set_buttons(current_buttons)
    logger.info("Connect control done")
    if impatient:
        log_message("Warning: Impatient mode is set, so many times are much shorter than they should be")
    


if __name__ == '__main__':
    logger.info("Running")
    cycle()
    socketio.run(app, host="0.0.0.0", port=80)
    logger.info("Done")
