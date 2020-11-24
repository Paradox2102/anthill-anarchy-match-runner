#!/usr/bin/env python3

# This module handles long-running tasks.

import threading
import math

import eventlet
eventlet.monkey_patch() # Changes the behaviour of "import time"
import time

import config
import sheet
import control
import overlay
import table

# Pointer to the current thread object so it can be stopped.
current_thread = None 

class Thread(threading.Thread):
    """
    This is an abstract parent class for the various threads that we might run to update the overlay.
    It mainly exists to support stopping.  Clients should check "is_stopped" and use the provided "sleep" method.
    """
    
    class StoppedException(Exception):
        pass
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_event = threading.Event()
        
    def stop(self):
        """Set flag to say stopped.  Thread-safe."""
        config.logger.info(f"Stopping thread {self.name}")
        self.stop_event.set()
        
    def is_stopped(self):
        """Check stopped flag.  Thread-safe."""
        return self.stop_event.is_set()
        
    def sleep(self, sleep_time):
        """Like time.sleep(), except checks "is_stopped" and raises Exception.
        If called with times longer than one second, will check "is_stopped" every second."""
        if self.is_stopped():
            raise StoppedException(f"Thread {self.name} stopped")
        start = time.time()
        while True:
            sleep_remaining = sleep_time + start - time.time()
            if sleep_remaining <= 0: break
            time.sleep(min(sleep_remaining, 1))
            if self.is_stopped():
                raise StoppedException(f"Thread {self.name} stopped")
                
    def run(self):
        try:
            self.exec()
        except StoppedException:
            return
                
        
class MatchThread(Thread):
    """Run a match from countdown to "scoring in progress".
    """
    # These constants control the timing of the game.  All are in seconds.
    match_length = 10 if config.impatient else 120 # Length of match play
    count_down = 3 # Number of beeps before match play
    count_down_delay = 2 # delay between pushing button and countdown starting
    end_game = 5 if config.impatient else 10 # When to sound warning during match play
    
    def __init__(self, match_id):
        super().__init__(name="Match " + match_id)
        self.match_id = match_id
        self.match = sheet.get_match(match_id)
    
    def exec(self):
        overlay.update_text(
            redteam=self.match["Red Competitors"],
            blueteam=self.match["Blue Competitors"],
            match=self.match_id,
            time="Starting",
        )
        
        control.set_buttons([dict(event='abort_match', arg=self.match_id, label=f"Abort match {self.match_id}")])

        old_seconds = self.match_length + self.count_down + self.count_down_delay
        now = time.time()
        end_time = now + old_seconds
        config.logger.info(f"Running match {self.match_id} from {now} to {end_time}")
        
        while not self.is_stopped():
            current_time = time.time()
            seconds = math.ceil(end_time - current_time)
            
            if seconds != old_seconds:
                config.logger.info(f"Match {self.match_id}, seconds={seconds}")
                old_seconds = seconds
                
                if seconds < 0: # Game over
                    overlay.update_text(middle="Game Over!<br/><br/>Scoring in Progress", clear=False)
                    control.set_buttons([
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
                        overlay.update_text(time="{min:02d}:{sec:02d}".format(min=seconds // 60, sec=seconds % 60), clear=False)
                    elif seconds > self.match_length and seconds <= self.match_length + self.count_down:
                        # Countdown
                        overlay.update_text(time=(seconds - self.match_length), clear=False)
                        
                    # Play sound
                    if seconds == 0:
                        overlay.play_audio('end')
                    elif seconds == self.end_game:
                        overlay.play_audio('warning')
                    elif seconds == self.match_length:
                        overlay.play_audio('start')
                    elif seconds > self.match_length and seconds <= self.match_length + self.count_down:
                        overlay.play_audio('countdown')
            self.sleep(0.25) # avoid skipping seconds because of oversleeping

            
class DefaultThread(Thread):
    """This thread runs by default if we're not showing anything special.
    It alternates between a table of teams, and a table of matches.
    Note: This ought to change behaviour for finals.
    """
    sleep_time = 5 if config.impatient else 10 
    
    def __init__(self):
        super().__init__(name="Default")
        #methods = [self.show_matches, self.show_team]
        
    def exec(self):
        # Create buttons for starting every possible match.
        # Note: We could program this only to offer the next match, but then we could not choose to play out of order.
        # Note: We could hide complete matches, but then we could not choose to replay a match.
        # TODO: Colour buttons by whether the matches already have scores
        buttons = [dict(event="next_match", arg=match['Match'], label=f"Next match {match['Match']}") 
                   for match in sheet.get_matches()]
        control.set_buttons(buttons)

        try:
            while not self.is_stopped():
                self.sleep(self.sleep_time)
                table.show_matches()
 
                self.sleep(self.sleep_time)   
                overlay.show_table()

                self.sleep(self.sleep_time)                   
                table.show_teams()

                self.sleep(self.sleep_time)   
                overlay.show_table()
        finally:
            overlay.show_table()
            

class MatchScoreThread(Thread):
    """Show the results of a single match.  
    Only available after completing a match, and automatically ends after 30 seconds."""
    sleep_time = 5 if config.impatient else 30
    
    def __init__(self, match_id):
        super().__init__(name="Match " + match_id)
        self.match_id = match_id
        self.match = sheet.get_match(match_id)
        
    def exec(self):
        try:
            overlay.update_text()
            table.show_match(self.match_id)
            control.set_buttons([dict(event='abort_match', arg=self.match_id,
                                label=f"Abandon match {self.match_id}")]);
            self.sleep(self.sleep_time)
        finally:
            overlay.show_table("", None)

        cycle()

        
def set_thread(thread=None):
    """Stops the current thread (if any) and launches a new thread (if not None)."""
    config.logger.info(f"set thread {thread}", exc_info=True)
    global current_thread
    if None != current_thread:
        current_thread.stop()
    current_thread = thread
    if None != thread:
        thread.start()
        
        
def cycle():
    """This invokes the default thread to cycle between interesting tables.
    """
    overlay.update_text();
    buttons = [dict(event="next_match", arg=match['Match'], label=f"Next match {match['Match']}") 
               for match in sheet.get_matches()]
    control.set_buttons(buttons)
    set_thread(DefaultThread())