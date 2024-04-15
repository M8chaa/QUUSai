import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

current_url = "https://www.moyoplan.com/plans/16181"
response = requests.get(current_url)
soup = BeautifulSoup(response.text, 'html.parser')
events_sections = soup.find_all('div', class_='css-mdplld eqp7k0x1')

for section in events_sections:
#         # Assuming each event has a title in a span with a specific class
        #check if there is a title of 사은품 및 이벤트
        try:
            title = section.find('span', class_='css-1dhu10z e8zn4re0').text
        except:
            title = ''
        if title == '사은품 및 이벤트':
            print(title)
            # print(section.text)
            # print link
            print(section.find('a', class_='css-1hdj7cf e17wbb0s4')['href'])
            #print title: css-1p5yo9l e8zn4re0
            print(section.find('span', class_='css-1p5yo9l e8zn4re0').text)
            # Check if description contains '대상' for all descriptions
            descriptions = section.find_all('p', class_='tw-m-0 css-1sfi3e1 e8zn4re0')
            for description in descriptions:
                if '대상' in description.text:
                    print(description.text)
                elif '지급시기' in description.text:
                    print(description.text)
            
        
#         # Further details can be extracted here based on the structure
#         # For example, extracting the event link and description
#         event_link = section.find('a', class_='css-1hdj7cf e17wbb0s4')['href']
#         description = section.find('div', class_='css-1kkt86i e17wbb0s2').text
        
#         print(f'Title: {title}')
#         print(f'Link: {event_link}')
#         print(f'Description: {description}\n')

