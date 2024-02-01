# coding:utf-8
from operator import call
from langchain.document_loaders import SitemapLoader
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.document_transformers import Html2TextTransformer
from langchain.schema import Document
from langchain.storage import LocalFileStore
import requests
from bs4 import BeautifulSoup
import re
import threading
import streamlit as st
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome import service as fs
from selenium.webdriver import ChromeOptions
# from webdriver_manager.core.utils import ChromeType
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager, ChromeType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import streamlit_extras
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.row import row
from Google import Create_Service
import os
from queue import Queue
import time
from ratelimit import limits, sleep_and_retry
import traceback

st.set_page_config(
    page_title="CrawlingAI_for_Moyo",
    page_icon="🖥️",
)

llm = ChatOpenAI(
    temperature=0.1,
)

answers_prompt = ChatPromptTemplate.from_template(
    """
    Using ONLY the following context answer the user's question. If you can't just say you don't know, don't make anything up.
                                                  
    Then, give a score to the answer between 0 and 5.

    If the answer answers the user question the score should be high, else it should be low.

    Make sure to always include the answer's score even if it's 0.

    Context: {context}
                                                  
    Examples:
                                                  
    Question: How far away is the moon?
    Answer: The moon is 384,400 km away.
    Score: 5
                                                  
    Question: How far away is the sun?
    Answer: I don't know
    Score: 0
                                                  
    Your turn!

    Question: {question}
"""
)
def googleDriveConnect():
    CLIENT_SECRETS = st.secrets["GoogleDriveAPISecrets"]
    # CLIENT_SECRETS = "QUUSai_clientID_desktop.json"
    API_NAME = 'drive'
    API_VERSION = 'v3'
    SCOPES = ['https://www.googleapis.com/auth/drive']
    serviceInstance = Create_Service(CLIENT_SECRETS, API_NAME, API_VERSION, SCOPES)
    return serviceInstance

def googleSheetConnect():
    CLIENT_SECRETS = st.secrets["GoogleDriveAPISecrets"]
    API_NAME = 'sheets'
    API_VERSION = 'v4'
    SCOPES = ['https://www.googleapis.com/auth/drive']
    serviceInstance = Create_Service(CLIENT_SECRETS, API_NAME, API_VERSION, SCOPES)
    return serviceInstance

def create_new_google_sheet(url1, url2):
    part1 = url1.split('/')
    part2 = url2.split('/')
    number1 = int(part1[-1])
    number2 = int(part2[-1])
    serviceInstance = googleDriveConnect()
    name = f'모요 요금제 {number1} ~ {number2}'
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    }
    file = serviceInstance.files().create(body=file_metadata, fields='id, webViewLink').execute()
    sheet_id = file.get('id')
    sheet_web_view_link = file.get('webViewLink')
    permission = {
            'type': 'anyone',
            'role': 'writer'
        }
    serviceInstance.permissions().create(fileId=sheet_id, body=permission).execute()

    return sheet_id, sheet_web_view_link


def pushToSheet(data, sheet_id, range='Sheet1!A:A'):
    serviceInstance = googleSheetConnect()
    body = {
        'values': [data]
    }
    result = serviceInstance.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range,
        valueInputOption='USER_ENTERED',  # or 'RAW'
        body=body
    ).execute()

    return result

def formatHeaderTrim(sheet_id, sheet_index=0):
    serviceInstance = googleSheetConnect()

    # Retrieve sheet metadata
    sheet_metadata = serviceInstance.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheet = sheet_metadata.get('sheets', '')[sheet_index]
    totalColumns = sheet.get('properties', {}).get('gridProperties', {}).get('columnCount', 0)
    sheetId = sheet.get('properties', {}).get('sheetId', 0)

    requests = []

    # Formatting header row
    header_format_request = {
        "repeatCell": {
            "range": {
                "sheetId": sheetId,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 20
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {
                        "red": 0.9, "green": 0.9, "blue": 0.9
                    },
                    "textFormat": {
                        "bold": True
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    }
    requests.append(header_format_request)

    # Trimming columns if necessary
    if totalColumns > 20:
        trim_columns_request = {
            "deleteDimension": {
                "range": {
                    "sheetId": sheetId,
                    "dimension": "COLUMNS",
                    "startIndex": 20,
                    "endIndex": totalColumns
                }
            }
        }
        requests.append(trim_columns_request)

    number_of_rows_to_freeze = 1  # Change this to the number of rows you want to freeze

    # Request body to freeze rows
    first_row_freeze_request = {
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheetId,  # Use the variable sheetId instead of hardcoding
                "gridProperties": {
                    "frozenRowCount": number_of_rows_to_freeze
                }
            },
            "fields": "gridProperties.frozenRowCount"
        }
    }

    requests.append(first_row_freeze_request)

    body = {"requests": requests}

    response = serviceInstance.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, 
        body=body
    ).execute()

    return response


def autoResizeColumns(sheet_id, sheet_index=0):
    serviceInstance = googleSheetConnect()
    sheet_metadata = serviceInstance.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheet = sheet_metadata.get('sheets', '')[sheet_index]
    sheetId = sheet.get('properties', {}).get('sheetId', 0)
    requests = []

    # # Loop through the first 12 columns
    # for i in range(12):  # Adjust the range if needed
    auto_resize_request = {
        "autoResizeDimensions": {
            "dimensions": {
                "sheetId": sheetId,
                "dimension": "COLUMNS",
                "startIndex": 0,  # Start index of the column
                "endIndex": 1  # End index (exclusive), so it's set to one more than the start index
            }
        }
    }
    requests.append(auto_resize_request)
    sort_request = [{
        "sortRange": {
            "range": {
                "sheetId": sheetId,
                "startRowIndex": 1,  # Assuming the first row is headers
            },
            "sortSpecs": [{
                "dimensionIndex": 0,
                "sortOrder": "ASCENDING"
            }]
        }
    }]
    requests.append(sort_request)
    body = {"requests": requests}
    response = serviceInstance.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, 
        body=body
    ).execute()

    return response




def get_answers(inputs):
    docs = inputs["docs"]
    question = inputs["question"]
    answers_chain = answers_prompt | llm
    return {
        "question": question,
        "answers": [
            {
                "answer": answers_chain.invoke(
                    {"question": question, "context": doc.page_content}
                ).content,
                "source": doc.metadata["source"],
                "date": doc.metadata["lastmod"],
            }
            for doc in docs
        ],
    }


choose_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Use ONLY the following pre-existing answers to answer the user's question.

            Use the answers that have the highest score (more helpful) and favor the most recent ones.

            Cite sources and return the sources of the answers as they are, do not change them.

            Answers: {answers}
            """,
        ),
        ("human", "{question}"),
    ]
)


def choose_answer(inputs):
    answers = inputs["answers"]
    question = inputs["question"]
    choose_chain = choose_prompt | llm
    condensed = "\n\n".join(
        f"{answer['answer']}\nSource:{answer['source']}\nDate:{answer['date']}\n"
        for answer in answers
    )
    return choose_chain.invoke(
        {
            "question": question,
            "answers": condensed,
        }
    )


def parse_page(soup):
    header = soup.find("header")
    footer = soup.find("footer")
    if header:
        header.decompose()
    if footer:
        footer.decompose()
    return (
        str(soup.get_text())
        .replace("\n", " ")
        .replace("\xa0", " ")
        .replace("CloseSearch Submit Blog", "")
    )


@st.cache_data(show_spinner="Loading website...")
def load_sitemap(url):
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000,
        chunk_overlap=200,
    )
    loader = SitemapLoader(
        url,
        parsing_function=parse_page,
    )
    loader.requests_per_second = 2
    docs = loader.load_and_split(text_splitter=splitter)
    vector_store = FAISS.from_documents(docs, OpenAIEmbeddings())
    return vector_store.as_retriever()
    

st.markdown(
    """
    # CrawlingAI for Moyo
            
    ### Extract Moyo's Mobile Phone Plans!

    Enter plan numbers at the sidebar and export data to text files or google sheet! 
"""
)

# def regex_extract(strSoup):
#     mvno_pattern = r"\[(.*?)\]"
#     plan_name_pattern = r"\]\s*(.*?)\s*\|"
#     monthly_fee_pattern = r"\|\s*([\d,]+원)\s*\|"
#     monthly_data_pattern = r"월\s*([.\d]+(?:GB|MB))"
#     daily_data_pattern = r"매일\s*([.\d]+(?:GB|MB))"
#     data_speed_pattern = r"\(([.\d]+(?:mbps|gbps))\)"
#     call_minutes_pattern = r"(\d+분|무제한)"
#     text_messages_pattern = r"(\d+건|무제한)"
#     carrier_pattern = r"(LG U\+|SKT|KT)"
#     network_type_pattern = r"(LTE|3G|4G|5G)"
#     discount_info_pattern = r"(\d+개월\s*이후\s*[\d,]+원)"
#     mvno = re.search(mvno_pattern, strSoup)
#     plan_name = re.search(plan_name_pattern, strSoup)
#     monthly_fee = re.search(monthly_fee_pattern, strSoup)
#     monthly_data = re.search(monthly_data_pattern, strSoup)
#     daily_data = re.search(daily_data_pattern, strSoup)
#     data_speed = re.search(data_speed_pattern, strSoup)
#     call_minutes = re.search(call_minutes_pattern, strSoup)
#     text_messages = re.search(text_messages_pattern, strSoup)
#     carrier = re.search(carrier_pattern, strSoup)
#     network_type = re.search(network_type_pattern, strSoup)
#     discount_info = re.search(discount_info_pattern, strSoup)

#     return [ mvno.group(1) if mvno else "제공안함", 
#             plan_name.group(1) if plan_name else "제공안함", 
#             monthly_fee.group(1) if monthly_fee else "제공안함", 
#             monthly_data.group(1) if monthly_data else "제공안함", 
#             daily_data.group(1) if daily_data else "제공안함", 
#             data_speed.group(1) if data_speed else "제공안함", 
#             call_minutes.group(1) if call_minutes else "제공안함", 
#             text_messages.group(1) if text_messages else "제공안함", 
#             carrier.group(1) if carrier else "제공안함", 
#             network_type.group(1) if network_type else "제공안함", 
#             discount_info.group(1) if discount_info else "제공안함"
#     ]

def regex_extract(strSoup):
    # Existing patterns
    mvno_pattern = r"\[(.*?)\]"
    plan_name_pattern = r"\]\s*(.*?)\s*\|"
    monthly_fee_pattern = r"\|\s*([\d,]+원)\s*\|"
    monthly_data_pattern = r"월\s*([.\d]+(?:GB|MB))"
    daily_data_pattern = r"매일\s*([.\d]+(?:GB|MB))"
    data_speed_pattern = r"\(([.\d]+(?:mbps|gbps))\)"
    call_minutes_pattern = r"(\d+분|무제한)"
    text_messages_pattern = r"(\d+건|무제한)"
    carrier_pattern = r"(LG U\+|SKT|KT)"
    network_type_pattern = r"(LTE|3G|4G|5G)"
    discount_info_pattern = r"(\d+개월\s*이후\s*[\d,]+원)"

    # New patterns
    between_contract_and_call_pattern = r"(?<=통신사 약정)(.*?)(?=통화|펼쳐보기)"
    between_number_transfer_fee_and_sim_delivery_pattern = r"(?<=번호이동 수수료)(.*?)(?=일반 유심 배송)"
    between_sim_delivery_pattern_and_nfc_sim = r"(?<=일반 유심 배송)(.*?)(?=NFC 유심 배송)"
    between_nfc_sim_and_esim_pattern = r"(?<=NFC 유심 배송)(.*?)(?=eSIM)"
    between_esim_and_support_pattern = r"(?<=eSIM)(.*?)(?=지원(?! 안함| 안 함))"

    # New patterns for 지원 and 미지원
    pattern_support_with_boundary = r'지원\s*(.*?)\s*미지원'
    pattern_no_support_with_boundary = r'미지원\s*(.*?)\s*(접기|기본)'

    # Extracting information using existing patterns
    mvno = re.search(mvno_pattern, strSoup)
    plan_name = re.search(plan_name_pattern, strSoup)
    monthly_fee = re.search(monthly_fee_pattern, strSoup)
    monthly_data = re.search(monthly_data_pattern, strSoup)
    daily_data = re.search(daily_data_pattern, strSoup)
    data_speed = re.search(data_speed_pattern, strSoup)
    call_minutes = re.search(call_minutes_pattern, strSoup)
    text_messages = re.search(text_messages_pattern, strSoup)
    carrier = re.search(carrier_pattern, strSoup)
    network_type = re.search(network_type_pattern, strSoup)
    discount_info = re.search(discount_info_pattern, strSoup)

    # Extracting information using new patterns
    between_contract_and_call = re.search(between_contract_and_call_pattern, strSoup)
    between_number_transfer_fee_and_sim_delivery = re.search(between_number_transfer_fee_and_sim_delivery_pattern, strSoup)
    between_sim_delievery_and_nfc_sim = re.search(between_sim_delivery_pattern_and_nfc_sim, strSoup)
    between_nfc_sim_and_esim = re.search(between_nfc_sim_and_esim_pattern, strSoup)
    between_esim_and_support = re.search(between_esim_and_support_pattern, strSoup)

    # Extracting 지원 and 미지원 information
    text_support_boundary = re.search(pattern_support_with_boundary, strSoup, re.DOTALL)
    text_no_support_boundary = re.search(pattern_no_support_with_boundary, strSoup, re.DOTALL)

    # Function to format the extracted text based on the user's requirements
    def format_extracted_categories(matches, categories):
        formatted = []
        for category in categories:
            for match in matches:
                if category in match:
                    start_index = match.find(category)
                    end_index = min([match.find(cat, start_index + 1) for cat in categories if cat in match[start_index + 1:]] + [len(match)])
                    additional_text = match[start_index + len(category):end_index].strip()
                    formatted_text = f"{category}: {additional_text}" if additional_text else category
                    formatted.append(formatted_text)
                    break
        return ', '.join(formatted)

    # Categories for 지원 and 미지원
    categories_support = ['모바일 핫스팟', '소액 결제', '해외 로밍', '인터넷 결합', '데이터 쉐어링']
    categories_no_support = ['모바일 핫스팟', '소액 결제', '해외 로밍', '인터넷 결합', '데이터 쉐어링']

    # Formatting the support and no support texts
    formatted_text_support = format_extracted_categories([text_support_boundary.group(1) if text_support_boundary else ""], categories_support)
    formatted_text_no_support = format_extracted_categories([text_no_support_boundary.group(1) if text_no_support_boundary else ""], categories_no_support)

    return [
        mvno.group(1) if mvno else "제공안함", 
        plan_name.group(1) if plan_name else "제공안함", 
        monthly_fee.group(1) if monthly_fee else "제공안함", 
        monthly_data.group(1) if monthly_data else "제공안함", 
        daily_data.group(1) if daily_data else "제공안함", 
        data_speed.group(1) if data_speed else "제공안함", 
        call_minutes.group(1) if call_minutes else "제공안함", 
        text_messages.group(1) if text_messages else "제공안함", 
        carrier.group(1) if carrier else "제공안함", 
        network_type.group(1) if network_type else "제공안함", 
        discount_info.group(1) if discount_info else "제공안함",
        between_contract_and_call.group(1) if between_contract_and_call else "제공안함",
        between_number_transfer_fee_and_sim_delivery.group(1) if between_number_transfer_fee_and_sim_delivery else "제공안함",
        between_sim_delievery_and_nfc_sim.group(1) if between_sim_delievery_and_nfc_sim else "제공안함",
        between_nfc_sim_and_esim.group(1) if between_nfc_sim_and_esim else "제공안함",
        between_esim_and_support.group(1) if between_esim_and_support else "제공안함",
        formatted_text_support if formatted_text_support else "제공안함",
        formatted_text_no_support if formatted_text_no_support else "제공안함"
    ]

def regex_extract_for_sheet():
    mvno_pattern = r"\[(.*?)\]"
    plan_name_pattern = r"\]\s*(.*?)\s*\|"
    monthly_fee_pattern = r"\|\s*([\d,]+원)\s*\|"
    monthly_data_pattern = r"월\s*([.\d]+(?:GB|MB))"
    daily_data_pattern = r"매일\s*([.\d]+(?:GB|MB))"
    data_speed_pattern = r"\(([.\d]+(?:mbps|gbps))\)"
    call_minutes_pattern = r"(\d+분|무제한)"
    text_messages_pattern = r"(\d+건|무제한)"
    carrier_pattern = r"(LG U\+|SKT|KT)"
    network_type_pattern = r"(LTE|3G|4G|5G)"
    discount_info_pattern = r"(\d+개월\s*이후\s*[\d,]+원)"

    return [mvno_pattern, plan_name_pattern, monthly_fee_pattern, monthly_data_pattern, daily_data_pattern, data_speed_pattern, call_minutes_pattern, text_messages_pattern, carrier_pattern, network_type_pattern, discount_info_pattern]


def update_google_sheet(data, sheet_id):
    pushToSheet(data, sheet_id, range='Sheet1!A:B')

def sort_sheet_by_column(sheet_id, column_index=0):
    serviceInstance = googleSheetConnect()

    # Specify the sort request
    requests = [{
        "sortRange": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,  # Assuming the first row is headers
            },
            "sortSpecs": [{
                "dimensionIndex": column_index,
                "sortOrder": "ASCENDING"
            }]
        }
    }]

    # Send the request
    body = {
        'requests': requests
    }
    serviceInstance.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()


def fetch_data(driver, url_queue, data_queue):
    try:
        while not url_queue.empty():
            url = url_queue.get()
            # Fetch and process data from the URL
            driver.get(url)

            try:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                driver.switch_to.alert.accept()
                alert_present = True
            except (NoAlertPresentException, TimeoutException):
                alert_present = False
            expired = None
            result = ""
            if alert_present:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    strSoup = soup.get_text()
                    expired = "종료 되었습니다"

            else: 
                try:
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    strSoup = soup.get_text()
                    pattern1 = r"서버에 문제가 생겼어요"
                    pattern2 = r"존재하지 않는 요금제에요"

                    # Combine patterns with | which acts as logical OR
                    combined_pattern = pattern1 + "|" + pattern2

                    # Searching for the combined pattern in the text
                    match = re.search(combined_pattern, strSoup)
                    result = match.group() if match else ""
                except Exception as e:
                    st.write(f"An Error Occurred: {e}")
                driver.refresh()
                if result is "":
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "css-yg1ktq")))
                    # button = driver.find_element(By.XPATH, "//button[contains(@class, 'css-yg1ktq')]")
                    # ActionChains(driver).move_to_element(button).click(button).perform()
                    button = driver.find_element(By.XPATH, "//button[contains(@class, 'css-yg1ktq')]")
                    driver.execute_script("arguments[0].click();", button)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-1ipix51')))
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                strSoup = soup.get_text()
                expired = "서비스 중입니다"

            if export_to_google_sheet:
                if result is "":
                    regex_formula = regex_extract(strSoup)
                    planUrl = str(url)
                    data = [planUrl] + regex_formula + [expired]
                else:
                    planUrl = str(url)
                    data = [ planUrl,"-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-"]
                    data.append(f"{result}")
            # Put the processed data into the data queue
            data_queue.put(data)
            url_queue.task_done()
    except Exception as e:
        # Log the exception or handle it as needed
        st.write(f"An error occurred when fetching data of {url}: {e}")
    finally:
        driver.quit()

PER_MINUTE_LIMIT = 300
@sleep_and_retry
@limits(calls=PER_MINUTE_LIMIT, period=60)
def update_sheet(data_queue, sheet_update_lock, sheet_id):
    while True:
        processed_data = data_queue.get()
        if processed_data is None:  # Sentinel value to indicate completion
            break
        with sheet_update_lock:
            # Update Google Sheet with processed_data
            pushToSheet(processed_data, sheet_id, range='Sheet1!A:B')
            # time.sleep(1)
        data_queue.task_done()


def moyocrawling(url1, url2, sheet_id):
    part1 = url1.split('/')
    part2 = url2.split('/')
    try:
        number1 = int(part1[-1])
        number2 = int(part2[-1])
    except ValueError:
        return None

    url_queue = Queue()
    data_queue = Queue()
    sheet_update_lock = threading.Lock()

    # Populate the URL queue
    for i in range(number1, number2 + 1):
        current_url = '/'.join(part1[:-1] + [str(i)])
        url_queue.put(current_url)

    def setup_driver():
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')

        CHROMEDRIVER = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        service = fs.Service(CHROMEDRIVER)
        driver = webdriver.Chrome(
                                options=options,
                                service=service
                                )
        return driver

    # Start data fetching threads
    fetch_threads = []
    for _ in range(6):
        driver = setup_driver()  # Each thread gets its own driver instance
        t = threading.Thread(target=fetch_data, args=(driver, url_queue, data_queue))
        t.start()
        fetch_threads.append(t)

    # Start sheet updating threads
    update_threads = []
    for _ in range(20):
        t = threading.Thread(target=update_sheet, args=(data_queue, sheet_update_lock, sheet_id))
        t.start()
        update_threads.append(t)

    # Wait for data fetching threads to finish and signal update threads to finish
    for thread in fetch_threads:
        thread.join()
    for _ in range(20):
        data_queue.put(None)  # Sentinel value for each update thread

    # Wait for update threads to finish
    for thread in update_threads:
        thread.join()
    st.session_state['moyocrawling_completed'] = True


    
# def moyocrawling(url1, url2, export_to_google_sheet, sheet_id):
#     part1 = url1.split('/')
#     part2 = url2.split('/')
#     try:
#         number1 = int(part1[-1])
#         number2 = int(part2[-1])
#     except ValueError:
#         return None
#     options = ChromeOptions()

#     # option設定を追加（設定する理由はメモリの削減）
#     options.add_argument("--headless")
#     options.add_argument('--disable-gpu')
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')
#     options.add_argument('--disable-extensions')


#     # webdriver_managerによりドライバーをインストール
#     # chromiumを使用したいのでchrome_type引数でchromiumを指定しておく
#     CHROMEDRIVER = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
#     service = fs.Service(CHROMEDRIVER)
#     driver = webdriver.Chrome(
#                               options=options,
#                               service=service
#                              )

#     # driver.set_window_size(1920, driver.execute_script("return document.body.parentNode.scrollWidth"))



#     if 'download_buttons' not in st.session_state:
#         st.session_state['download_buttons'] = []

#     threads = []
#     for start_num in range(number1, number2 + 1, 50):
#         end_num = min(start_num + 49, number2)

#         for i in range(start_num, end_num + 1):
#             current_url = '/'.join(part1[:-1] + [str(i)])
#             driver.get(current_url)

#             try:
#                 WebDriverWait(driver, 1).until(EC.alert_is_present())
#                 driver.switch_to.alert.accept()
#                 alert_present = True
#             except (NoAlertPresentException, TimeoutException):
#                 alert_present = False
#             expired = None
#             result = ""
#             if alert_present:
#                 response = requests.get(current_url)
#                 if response.status_code == 200:
#                     soup = BeautifulSoup(response.text, 'html.parser')
#                     strSoup = soup.get_text()
#                     expired = "종료 되었습니다"

#             else: 
#                 try:
#                     html = driver.page_source
#                     soup = BeautifulSoup(html, 'html.parser')
#                     strSoup = soup.get_text()
#                     pattern = r"서버에 문제가 생겼어요"
#                     # Searching for the pattern in the text
#                     match = re.search(pattern, strSoup)
#                     result = match.group() if match else ""
#                 except Exception as e:
#                     st.write(f"An Error Occurred: {e}")
#                 driver.refresh()
#                 if result is "":
#                     WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CLASS_NAME, "css-yg1ktq")))
#                     # button = driver.find_element(By.XPATH, "//button[contains(@class, 'css-yg1ktq')]")
#                     # ActionChains(driver).move_to_element(button).click(button).perform()
#                     button = driver.find_element(By.XPATH, "//button[contains(@class, 'css-yg1ktq')]")
#                     driver.execute_script("arguments[0].click();", button)
#                     WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-1ipix51')))
#                 html = driver.page_source
#                 soup = BeautifulSoup(html, 'html.parser')
#                 strSoup = soup.get_text()
#                 expired = "서비스 중입니다"

#             if export_to_google_sheet:
#                 if result is "":
#                     regex_formula = regex_extract(strSoup)
#                     planUrl = str(current_url)
#                     data = [planUrl] + regex_formula + [expired]
#                 else:
#                     planUrl = str(current_url)
#                     data = [ planUrl, "-", "-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-"]
#                     data.append(f"모요 {result}")
#                 # Start a thread for Google Sheets update
#                 thread = threading.Thread(target=update_google_sheet, args=(data, sheet_id))
#                 thread.start()
#                 threads.append(thread)  # Add the thread to the list

#     for thread in threads:
#             thread.join()
#     driver.close()



with st.sidebar:
    base_url = "https://www.moyoplan.com/plans/"
    end_param1 = st.text_input(f"Enter the End Parameter for the Starting URL\n {base_url}", placeholder="15000")
    end_param2 = st.text_input(f"Enter the End Parameter for the Starting URL\n {base_url}", placeholder="15100")

    # Default case: both parameters are provided
    if end_param1 and end_param2:
        url1 = base_url + end_param1
        url2 = base_url + end_param2
    # Handle the case where only one parameter is provided
    elif end_param1 or end_param2:
        common_param = end_param1 if end_param1 else end_param2
        url1 = url2 = base_url + common_param
    else:
        url1 = url2 = None

    if st.button("Start Crawling"):
        if url1 and url2:
            st.session_state['show_download_buttons'] = True
            st.session_state['url1'] = url1
            st.session_state['url2'] = url2
            st.write("Starting URL: ", url1)
            st.write("Last URL: ", url2)
        else:
            st.warning("Please enter at least one end parameter.")

def moyocrawling_wrapper(url1, url2, sheet_id):
    try:
        moyocrawling(url1, url2, sheet_id)
        st.session_state['moyocrawling_completed'] = True
        st.session_state['moyocrawling_error'] = None
    except Exception as e:
        error_message = f"An error occurred in moyocrawling: {e}\n{traceback.format_exc()}"
        st.session_state['moyocrawling_completed'] = True
        st.session_state['moyocrawling_error'] = error_message

if 'show_download_buttons' in st.session_state and st.session_state['show_download_buttons']:
    url1 = st.session_state.get('url1')
    url2 = st.session_state.get('url2')
    col1, col2 = st.columns(2)

    gs_button_pressed = st.button("Google Sheet", key="gs_button", use_container_width=True)
    if gs_button_pressed:
        st.session_state['moyocrawling_completed'] = False
        st.session_state['moyocrawling_error'] = None
        try:
            export_to_google_sheet = True
            sheet_id, webviewlink = create_new_google_sheet(url1, url2)
            headers = {
                'values': ["url", "MVNO", "요금제명", "월 요금", "월 데이터", "일 데이터", "데이터 속도", "통화(분)", "문자(건)", "통신사", "망종류", "할인정보", "통신사 약정", "번호이동 수수료", "일반 유심 배송", "NFC 유심 배송", "eSim", "지원", "미지원", "종료 여부"]
            }
            pushToSheet(headers, sheet_id, 'Sheet1!A1:L1')
            formatHeaderTrim(sheet_id, 0)
            sheetUrl = str(webviewlink)
            st.link_button("Go to see", sheetUrl)
            threading.Thread(target=moyocrawling_wrapper, args=(url1, url2, sheet_id)).start()
            autoResizeColumns(sheet_id, 0)
            with st.spinner("Processing for Google Sheet..."):
                while not st.session_state.get('moyocrawling_completed', False):
                    time.sleep(0.1)

            if st.session_state.get('moyocrawling_error'):
                st.error(st.session_state['moyocrawling_error'])
            else:
                st.success("Process Completed")

        except Exception as e:
            st.error(f"An Error Occurred: {e}")



# Outside the sidebar, render download buttons
for button in st.session_state.get('download_buttons', []):
    st.download_button(
        label=button['label'],
        data=button['data'],
        file_name=button['file_name'],
        mime="text/plain",
    )



# @st.cache_data(show_spinner="Getting Screenshot")
def start_chromium(url):
    # ドライバのオプション
    options = ChromeOptions()

    # option設定を追加（設定する理由はメモリの削減）
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # webdriver_managerによりドライバーをインストール
    # chromiumを使用したいのでchrome_type引数でchromiumを指定しておく
    CHROMEDRIVER = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
    service = fs.Service(CHROMEDRIVER)
    driver = webdriver.Chrome(
                              options=options,
                              service=service
                             )

    # URLで指定したwebページを開く
    driver.get(url)
    driver.refresh()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')

    # Find all clickable elements (links and buttons)
    clickable_elements = soup.find_all(['a', 'button'])
    clickable_elements_content = []
    # Process the elements
    for element in clickable_elements:
        tag_name = element.name
        text = element.get_text()
        href = element.get('href') if tag_name == 'a' else "Not an anchor tag"
        clickable_elements_content.append((tag_name, text, href))
        # Do something with the information

    button_locator = (By.CSS_SELECTOR, "button.tw-w-40.tw-h-40.tw-inline-flex.tw-justify-center.tw-items-center.tw-text-gray-500.tw-font-medium.tw-rounded-8.hover\\:tw-bg-gray-100")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button_locator))

    # Click the button
    button = driver.find_element(*button_locator)
    button.click()

    # Retrieve the updated HTML
    html2 = driver.page_source


    driver.close()
    return html, clickable_elements_content, html2


import pandas as pd

def convert_html_to_csv(html):
    # This function should convert HTML table data to CSV. 
    df = pd.read_html(html)[0]  # Adjust this to fit the HTML structure
    return df.to_csv(index=False)



url = ''
if url:
    if ".xml" not in url:
        result, clickable_elements_content, html2 = start_chromium(url)
        document = Document(page_content=result)
        transformed = Html2TextTransformer().transform_documents([document])


        
        add_vertical_space(1)        
        st.markdown("#### Raw HTML")
        links_row = row(2, vertical_align="left")
        links_row.download_button(
            label="Text File",
            data=result,
            file_name="raw_html.txt",
            mime="text/plain",
            use_container_width=True
        )
        links_row.link_button("Google Sheet","",use_container_width=True,)
        # if links_row.link_button("Google Sheet", "", use_container_width=True):
        #     googleDriveConnect()  # Trigger the function when button is clicked


        with st.expander("Click to see"):
            st.text_area("", result, height=300)
        
        # Adding a gap
        st.divider()

        st.markdown("#### Text Content")
        st.download_button(
            label="Text File",
            data=str(transformed),
            file_name="html_text.txt",
            mime="text/plain"
        )
        with st.expander("Click to see"):
            st.text_area("", transformed, height=300)
        
        st.divider()

        st.markdown("#### Clickable Elements")
        with st.expander("Click to see"):
            st.text_area("", clickable_elements_content, height=300)

        st.divider()

        st.markdown("#### Second page clicked")
        with st.expander("Click to see"):
            st.text_area("", html2, height=300)

        # st.divider()

        # st.markdown("#### XPath")
        # st.download_button(
        #     label="XPath",
        #     data=str(transformed),
        #     file_name="html_text.txt",
        #     mime="text/plain"
        # )
        # with st.expander("Click to see"):
        #     st.text_area("", transformed, height=300)
            
        # st.divider()
        # if os.path.exists(screenshot_path):
        #     st.image(screenshot_path)
        # else:
        #     st.error("Screenshot not found.")


    else:
        retriever = load_sitemap(url)
        query = st.text_input("Ask a question to the website.")
        if query:
            chain = (
                {
                    "docs": retriever,
                    "question": RunnablePassthrough(),
                }
                | RunnableLambda(get_answers)
                | RunnableLambda(choose_answer)
            )
            result = chain.invoke(query)
            st.markdown(result.content.replace("$", "\$"))
