import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

current_url = "https://www.moyoplan.com/plans/13891"
response = requests.get(current_url)
soup = BeautifulSoup(response.text, 'html.parser')

# Extract and print only the text
text = soup.get_text()
print(text)