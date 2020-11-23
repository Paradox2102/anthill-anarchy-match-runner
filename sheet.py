# This module provides read access to the Google spreadsheet.
# As a design choice, we do not provide an interface to update scores in the match runner interface.
# The Google spreadsheet interface works perfectly well for this purpose.
# This means that the match runner can be restarted without losing much state (except the current match).

import pickle
import os.path
import logging

from apiclient import discovery
from google.oauth2 import service_account

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Note: this module won't work without a "service-credentials.json" file, 
# for a Google Service account that has read access to the spreadsheet.
# For security reasons, this file is not included in the github repo.
SECRET_FILE = os.path.join(os.getcwd(), 'service-credentials.json')

# If you re-use this, create your own spreadsheet.
# TODO: Should probably read these values from a config file.
# Note that the header row in the spreadsheet must match the values used throughout the code, and in templates.
# TODO: Provide config to allow header keys mapping?
SPREADSHEET_ID = '1i9qLuN4PvYHannhivg4ZGla0Yh7DTqdWOUIADFNxZAQ'
MATCHES_RANGE_NAME = 'Matches!A1:Z'
TEAMS_RANGE_NAME = 'Teams!A1:Z'

sheet = None
matches = None
teams = None

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)

def init():
    """Open sheet API and get initial teams and matches."""
    
    credentials = service_account.Credentials.from_service_account_file(SECRET_FILE, scopes=SCOPES)
    service = discovery.build('sheets', 'v4', credentials=credentials, cache_discovery=False)

    # Call the Sheets API
    logger.info("Getting spreadsheets")
    global sheet
    sheet = service.spreadsheets()
    get_matches()
    get_teams()

    
def read_header_row_into_dicts(sheet, spreadsheet_id, range_name):
    """Reads a range from a spreadsheet.
    First row is treated as a header row.
    Subsequent rows are converted into dicts using header keys.
    
    Args:
        sheet: Sheet object to use.
        spreadsheet_id: ID string for spreadsheet.
        range_name: Range to pull from spreadsheet in usual Sheet/Excel syntax.
    
    Returns:
        results: List of dicts with keys from header row and values from each row.
    """
    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=range_name).execute()
    values = result.get('values', [])
    headers = values[0]
    return [ dict(zip(headers, row)) for row in values[1:] ]


def get_matches(flush=False):
    """Returns list of match objects.  
    
    Args:
        flush: If set to true, then results will be fetched from the spreadsheet, otherwise a cache will be used.
        
    Returns:
        matches: List of match objects.  
        
    TODO: Cache timeout?
    """
    global matches

    if flush:
        matches = None

    if matches is None:
        if sheet is None: init()
        matches = read_header_row_into_dicts(sheet, SPREADSHEET_ID, MATCHES_RANGE_NAME)

    return matches


def get_match(match_id, flush=False):
    """Returns object for specific match.
    
    Args:
        match_id: Identifier for specific match, e.g. "R!"
        flush: As for get_matches()
        
    Returns:
        match: dict for specific match or raise StopIteration exception.
    """
    
    return next(m for m in get_matches(flush=flush) if m['Match'] == match_id)


def get_teams(flush=False):
    """Returns list of team objects.  
    
    Args:
        flush: If set to true, then results will be fetched from the spreadsheet, otherwise a cache will be used.
        
    Returns:
        teams: List of team objects.
        
    TODO: Cache timeout?
    """
    global teams

    if flush:
        teams = None
    
    if teams is None:
        if sheet is None: init()
        teams = read_header_row_into_dicts(sheet, SPREADSHEET_ID, TEAMS_RANGE_NAME)

    return teams