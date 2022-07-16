# Anthill Anarchy Match Runner

This software was written to assist Team Paradox (2102) with the administration of an off-season competition run along FRC-like lines.  It provides a simple text display that can be shown to competitors and also overlaid on a video feed.  It also provides a simple control interface that allows officials to start matches and display scores.

Team lists, match lists, and match scores are maintained in a Google spreadsheet, which this service accesses read-only.  (This is a deliberate design choice not to implement a user interface for entering data in a table and storing them persistently.)

Note: There is no attempt to interact with driver station software, so teams are responsible for complying with start/stop.

Two interfaces are provided:
* http://localhost:8081/overlay.html - Team-/audience-facing view suitable for video overlay.  Supports optional `delay` URL parameter giving a delay in seconds before server events are executed, e.g. http://localhost:8081/overlay.html?delay=10 ; this is useful if the video feed has a significant (but consistent) delay.
* http://localhost:8081/control.html - Administration view with buttons that change the state

:warning: :sound: :mega: :boom: :headphones: :hear_no_evil: Warning: The overlay interface (and, via its preview iframe, the control interface) plays loud noises during the match, intended to be heard over speakers in a noisy competition environment.  You may not enjoy the unadjusted headphone experience.  

Note: To use this yourself, you will minimally need to:
* Create a Google service user account (see [Creating and managing service accounts](https://cloud.google.com/iam/docs/creating-managing-service-accounts))
* Save the credentials in `service-credentials.json` (see [Creating and managing service account keys](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)).  For security reasons, this file should not be saved in GitHub.
* Create a Google spreadsheet with the appropriate tables.  See `sheet.py` to find or change the table names, and the HTML files in `template` for the column names.  Or copy [this example](https://docs.google.com/spreadsheets/d/1BNnA14cs9spTda4PTTuU-bUsmUI4uJ3H_fQOJnVx3xQ/edit?usp=sharing)
* Share the spreadsheet with the service user (read-only)
* Change the spreadsheet id in `sheet.py`

To run, invoke `./run.sh`.  The only pre-requisite is Docker.

## Implementation notes

The microservice implementation is divided between several Python modules:
* `app`: Top level microservice application
* `control`: Handles messages to and from control interface
* `overlay`: Handles messages to and from overlay interface
* `table`: Instantiating complex tables
* `thread`: Performs long-running tasks like the match runner
* `sheet`: Fetches the matches and teams from the Google spreadsheet
* `config`: Useful globals and central configuration

The static HTML files `static/control.html` and `static/overlay.html` handle the client side of the two interfaces.  Each has an associated JavaScript file and CSS file.

The various HTML tables are configured in the Jinja2 template HTML fragment files in `template`.

## Future work

I really want to make the text and tables auto-scale their font size.  It turns out to be hard to predict/control what "screen size" OBS will use for a browser overlay.  There are parameters to tweak, but auto-scaling would be more convenient.

There is great scope to style buttons by function using colour, icons, order and dividing into sections.  In particular, "Start Match" buttons ought to indicate either whether the match has been run already or whether it has been scored already.

Although it is easy to adjust the overlay's volume in OBS, I should provide volume control with, perhaps, a default that is not so obnoxiously loud.  Also want to disable audio for the overlay preview within the control interface.  (For some reason, I have been unable to get AUDIO elements to honour a volume setting.)