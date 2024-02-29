from email import header
from hmac import new
import pickle
import os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json

def Create_Service(client_secret_file, api_name, api_version, *scopes):
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]

    conn = st.connection("gsheets", type=GSheetsConnection)

    df = conn.read(
        worksheet="Authtoken", 
        usecols=[0, 1],
        header=None )

    auth_tokens = {row[0]: row[1] for index, row in df.iterrows()}
    
    token = auth_tokens.get("token", "")
    client_id = auth_tokens.get("client_id", "")
    client_secret = auth_tokens.get("client_secret", "")
    refresh_token = auth_tokens.get("refresh_token", "")
    token_uri = auth_tokens.get("token_uri", "")
    scopes = auth_tokens.get("SCOPES", "")
    universe_domain = auth_tokens.get("universe_domain", "")
    account = auth_tokens.get("account", "")
    expiry = auth_tokens.get("expiry", "")
    
    cred = None
    # Create a Credentials object
    cred = Credentials.from_authorized_user_info({
        "token": token,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "token_uri": token_uri,
        "universe_domain": universe_domain,
        "account": account,
        "expiry": expiry
    }, SCOPES)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
            new_credentials = cred.to_json()
            new_credentials_dict = json.loads(new_credentials)
            df = [{'key': key, 'value': value} for key, value in new_credentials_dict.items()]
            conn.update(worksheet="Authtoken",
                        data = df)
        else:

            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()
            print("token recreated")

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        print(API_SERVICE_NAME, 'Cred valid. Service created successfully')
        return service
    except Exception as e:
        print('Unable to connect.')
        print(e)
        return None

