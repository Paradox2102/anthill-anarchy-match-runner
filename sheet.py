import pickle
import os.path
import logging

from apiclient import discovery
from google.oauth2 import service_account

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SECRET_FILE = os.path.join(os.getcwd(), 'service-credentials.json')

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
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    
    credentials = service_account.Credentials.from_service_account_file(SECRET_FILE, scopes=SCOPES)
    service = discovery.build('sheets', 'v4', credentials=credentials, cache_discovery=False)

    # Call the Sheets API
    logger.info("Getting spreadsheets")
    global sheet
    sheet = service.spreadsheets()
    get_matches()
    get_teams()

    
def read_header_row_into_dicts(sheet, spreadsheet_id, range_name):
    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=range_name).execute()
    values = result.get('values', [])
    headers = values[0]
    return [ dict(zip(headers, row)) for row in values[1:] ]


def get_matches(flush=False):
    global matches

    if flush:
        matches = None

    if matches is None:
        if sheet is None: init()
        matches = read_header_row_into_dicts(sheet, SPREADSHEET_ID, MATCHES_RANGE_NAME)

    return matches


def get_match(match_id, flush=False):
    return next(m for m in get_matches(flush=flush) if m['Match'] == match_id)


def get_teams(flush=False):
    global teams

    if flush:
        teams = None
    
    if teams is None:
        if sheet is None: init()
        teams = read_header_row_into_dicts(sheet, SPREADSHEET_ID, TEAMS_RANGE_NAME)

    return teams