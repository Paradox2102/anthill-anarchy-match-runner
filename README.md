# Anthill Anarchy Match Runner

This software was written to assist Team Paradox (2102) with the administration of an off-season competition run along FRC-like lines.  It provides a simple text display that can be shown to competitors and also overlaid on a video feed.  It also provides a simple control interface that allows officials to start matches and display scores.

Team lists, match lists, and match scores are maintained in a Google spreadsheet.

Note: There is no attempt to interact with driver station software, so teams are responsible for complying with start/stop.

Two interfaces are provided:
    http://localhost:8081/overlay.html - Team/audience facing view suitable for video overlay
    http://localhost:8081/control.html - Administration view with buttons that change the state

Note: To use this yourself, you will minimally need to:
    * Create a Google service user account and save the credentials in `service-credentials.json` (not saved in GitHub).
    * Create a new Google spreadsheet with the appropriate tables.  See `sheet.py` for the tabe names, and the HTML files in `template` for the column names.
    * Share the spreadsheet with the service user (read only)
    * Change the spreadsheet id in `sheet.py`