# Anthill Anarchy Match Runner

This software was written to assist Team Paradox (2102) with the administration of an off-season competition run along FRC-like lines.  It provides a simple text display that can be shown to competitors and also overlaid on a video feed.  It also provides a simple control interface that allows officials to start matches and display scores.

Team lists, match lists, and match scores are maintained in a Google spreadsheet, which this service accesses read-only.

Note: There is no attempt to interact with driver station software, so teams are responsible for complying with start/stop.

Two interfaces are provided:
* http://localhost:8081/overlay.html - Team/audience facing view suitable for video overlay.  Supports optional `delay` URL parameter giving a delay in seconds before server events are executed, e.g. http://localhost:8081/overlay.html?delay=10
* http://localhost:8081/control.html - Administration view with buttons that change the state

:warning: :sound: :mega: :boom: :headphones: :hear_no_evil: Warning: The overlay interface plays noises quite loudly.  You may not enjoy the unadjusted headphone experience.

Note: To use this yourself, you will minimally need to:
* Create a Google service user account and save the credentials in `service-credentials.json` (not saved in GitHub).
* Create a Google spreadsheet with the appropriate tables.  See `sheet.py` to find or change the table names, and the HTML files in `template` for the column names.
* Share the spreadsheet with the service user (read only)
* Change the spreadsheet id in `sheet.py`

To run, invoke `run.sh`.  The only pre-requisite is Docker.

## Implementation notes

The bulk of the implementation is in the module `app.py` which runs the microservice and handles the websocket messages.

The module `sheet.py` handles fetching the matches and teams from the Google spreadsheet.

The static HTML files `static/control.html` and `static/overlay.html` handle the client side of the two interfaces.  Each has an associated JavaScript file and CSS file.

The HTML tables are configured in the Jinja2 template HTML files in `template`.

## Future work

I really want to make the text and tables auto-scale their font size.  It turns out to be hard to predict/control what "screen size" OBS will use for a browser overlay.  There are parameters to tweak, but auto-scaling would be more convenient.

Control buttons ought to be coloured, ordered, or divided into sections depending on whether the match has been run already or whether it has been scored already.

Should provide volume control with, perhaps, a default that is not so obnoxiously loud.