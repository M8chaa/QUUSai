import pickle
import os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

def Create_Service(client_secret_file, api_name, api_version, *scopes):
    print(client_secret_file, api_name, api_version, scopes, sep='-')
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]
    print(SCOPES)

    cred = None

    # pickle_file = f'token_{API_VERSION}.pickle'
    # print(pickle_file)
    # if os.path.exists(pickle_file):
    #     with open(pickle_file, 'rb') as token:
    #         cred = pickle.load(token)
    
    if os.path.exists("token.json"):
        cred = Credentials.from_authorized_user_file("token.json", SCOPES)
    # client_id = st.secrets["AuthToken"]["client_id"]
    # client_secret = st.secrets["AuthToken"]["client_secret"]
    # refresh_token = st.secrets["AuthToken"]["refresh_token"]
    # token_uri = "https://oauth2.googleapis.com/token"  # Default token URI for Google

    # Create a Credentials object
    # cred = Credentials.from_authorized_user_info({
    #     "client_id": client_id,
    #     "client_secret": client_secret,
    #     "refresh_token": refresh_token,
    #     "token_uri": token_uri
    # }, SCOPES)


    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
            print("token refreshed")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()
            print("token recreated")
            # cred1 = flow.redirect_uri()

        # with open(pickle_file, 'wb') as token:
            # pickle.dump(cred, token)
        with open("token.json", "w") as token:
            token.write(cred.to_json())
    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        print(API_SERVICE_NAME, 'Cred valid. Service created successfully')
        return service
    except Exception as e:
        print('Unable to connect.')
        print(e)
        return None
