import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

current_url = "https://www.moyoplan.com/plans/10431"
response = requests.get(current_url)
soup = BeautifulSoup(response.text, 'html.parser')
strSoup = soup.get_text()
print(strSoup)

# Find the <a> tag
a_tags = soup.find_all('a', class_='e3509g015')

# Extract the href attribute
links = [a_tag['href'] for a_tag in a_tags]

print(links)


# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin

# def decode_unicode_escapes(text):
#     return text.encode('utf-8').decode('unicode_escape')

# base_url = "https://www.moyoplan.com/plans/15007"
# response = requests.get(base_url)
# soup = BeautifulSoup(response.content, 'html.parser')

# scripts = soup.find_all('script')

# for script in scripts:
#     if script.string and 'alert(' in script.string:
#         print("Alert found in inline script:")
#         decoded_script = decode_unicode_escapes(script.string)
#         print(decoded_script)
#     elif script.get('src'):
#         # Convert relative URL to absolute URL
#         script_url = urljoin(base_url, script.get('src'))
#         print(f"External script: {script_url}")
#         try:
#             external_response = requests.get(script_url)
#             if 'alert(' in external_response.text:
#                 print("Alert found in external script:")
#                 decoded_script = decode_unicode_escapes(external_response.text)
#                 print(decoded_script)
#         except requests.exceptions.RequestException as e:
#             print(f"Error fetching script {script_url}: {e}")


# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin
# import codecs

# def decode_unicode_escapes(text):
#     return codecs.decode(text, 'unicode_escape', 'ignore')

# base_url = "https://www.moyoplan.com/plans/15007"
# response = requests.get(base_url)
# soup = BeautifulSoup(response.content, 'html.parser')

# scripts = soup.find_all('script')

# for script in scripts:
#     if script.string and 'alert(' in script.string:
#         print("Alert found in inline script:")
#         decoded_script = decode_unicode_escapes(script.string)
#         print(decoded_script)
#     elif script.get('src'):
#         # Convert relative URL to absolute URL
#         script_url = urljoin(base_url, script.get('src'))
#         try:
#             external_response = requests.get(script_url)
#             if 'alert(' in external_response.text:
#                 print("Alert found in external script:")
#                 decoded_script = decode_unicode_escapes(external_response.text)
#                 print(decoded_script)
#         except requests.exceptions.RequestException as e:
#             print(f"Error fetching script {script_url}: {e}")
