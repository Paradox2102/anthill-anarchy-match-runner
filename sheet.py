import pickle
import os.path
import logging

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SPREADSHEET_ID = '1i9qLuN4PvYHannhivg4ZGla0Yh7DTqdWOUIADFNxZAQ'
MATCHES_RANGE_NAME = 'Matches!A1:G'
MATCHES_RANGE_NAME = 'Teams!A1:H'

matches = None
teams = None

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.DEBUG)

def init():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            logger.info("Loading token pickle")
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing creds")
            creds.refresh(Request())
        else:
            logger.info("Loading credentials JSON")
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            logger.info("Running flow local server")
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            logger.info("Dumping pickle")
            pickle.dump(creds, token)

    logger.info("Buidling service")
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    logger.info("Getting spreadsheets")
    sheet = service.spreadsheets()
    global matches
    matches = read_header_row_into_dicts(sheet, SPREADSHEET_ID, MATCHES_RANGE_NAME)
    global teams
    teams = read_header_row_into_dicts(sheet, SPREADSHEET_ID, TEAMS_RANGE_NAME)

    
def read_header_row_into_dicts(sheet, spreadsheet_id, range_name):
    sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])
    headers = values[0]
    return [ dict(zip(headers, row)) for row in values[1:] ]


def get_matches():
    if matches is None:
        init()
    return matches


def get_match(match_id):
    return next(m for m in get_matches() if m['Match'] == match_id)


def get_teams():
    if teams is None:
        init()
    return teams