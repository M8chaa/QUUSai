from Google1 import Create_Service

CLIENT_SECRET_FILE = "CrawlingAIforMoyo.json"
API_NAME = 'sheets'
API_VERSION = 'v4'
SCOPES = ['https://www.googleapis.com/auth/drive']
serviceInstance = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)


service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

print (dir(service))

# national_parks = ['Yellowstone', 'Rocky Mountains', 'Yosemite']

# for national_park in national_parks:
#     file_metatdata = {
#         'name': national_park,
#         'mimeType': 'application/vnd.google-apps.folder',
#         # 'parents': []
#     }