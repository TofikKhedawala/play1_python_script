from google.oauth2 import service_account

# danish
API_KEY = 'AIzaSyApGkd__eT70QzJjSdyLHQMDW1NvvI1tJc'
cx = '955bccba6df524e44'

SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive']

SPREADSHEET_ID = "10dkmhxYlgCwqEhmQ0Q1ZjeqxjZH-l_La1bCJkqbIg1s"

SERVICE_ACCOUNT_FILE = r"credentials.json"


sheet_credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES)
drive_credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES)

MAX_WORKER = 2

INPUT_PATH = 'google_in'
GOOGLE_OUT_Path = 'google_out'
FINAL_OUTPUT_PATH = 'google_out_filtered'
DRIVE_FILE_PATH = "uploaded"

checkpoint_file = 'checkpoint.json'
cacheFile = 'cache.json'


INPUT_SHEET_RANGE = "InputSheet!A2:B"
OUTPUT_SHEET_NAME = "OutputSheet1"


LINK_KEYWORDS = ['contact', 'board', 'director','staff']
CONTAC_INPUT = r'contact_processing/contactsheet.csv'
CONTAC_OUTPUT = r'contact_processing/out.csv'
contact_csv = 'contact_csv'