from Google import Create_Service

CLIENT_SECRET_FILE = 'QUUSai_clientID_webapp.json'
API_NAME = 'drive'
API_VERSION = 'v3'
SCOPES = ['https://www.googleapis.com/auth/drive']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

print (dir(service))

# national_parks = ['Yellowstone', 'Rocky Mountains', 'Yosemite']

# for national_park in national_parks:
#     file_metatdata = {
#         'name': national_park,
#         'mimeType': 'application/vnd.google-apps.folder',
#         # 'parents': []
#     }