# coding:utf-8
from email.mime import base
from operator import call
from os import eventfd
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
from threading import Thread, Event
import streamlit as st
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome import service as fs
from selenium.webdriver import ChromeOptions
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager, ChromeType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.row import row
from Google import Create_Service
from queue import Queue
import time
from ratelimit import limits, sleep_and_retry
import traceback
from datetime import datetime
import pytz



st.set_page_config(
    page_title="CrawlingAI_for_Moyo",
    page_icon="🖥️",
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

def create_new_google_sheet_just_moyos():
    serviceInstance = googleDriveConnect()
    kst = pytz.timezone('Asia/Seoul')
    current_date = datetime.now(kst).strftime("%Y-%m-%d")
    name = f'모요 요금제 {current_date}'
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
    try:
        serviceInstance = googleSheetConnect()
        body = {'values': data}
        result = serviceInstance.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range,
            valueInputOption='USER_ENTERED',  # or 'RAW'
            body=body
        ).execute()
        return result
    except Exception as e:
        # Re-raise the exception to be caught in the calling function
        raise Exception(f"Failed to push data to sheet: {e}")


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


st.markdown(
    """
    # CrawlingAI for Moyo
            
    ### Extract Moyo's Mobile Phone Plans!

    Enter plan numbers at the sidebar and export data to text files or google sheet! 
"""
)

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

    사은품_pattern = {
        "사은품 및 이벤트": r"사은품 및 이벤트\s*([^\n]+?)(?=대상:)",  # Adjusted to ensure full capture up to "대상:"
        "대상": r"대상:\s*([^지급시기]+)",  # Ensure capturing stops correctly before "지급시기"
        "지급시기": r"지급시기:\s*([^\n]+?)(?=요금제 개통 절차)"  # Ensure capturing stops correctly before "요금제 개통 절차"
    }

    def extract_and_format_info(text, patterns):
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if key == "사은품 및 이벤트" and not match:
                return "없음"  # Return "없음" immediately if "사은품 및 이벤트" is not found
            if match and match.group(1).strip():
                value = match.group(1).strip()
                return f"{key}: {value}"  # Return the key and its value if found, then exit the loop

        # If the loop completes without finding "사은품 및 이벤트", it implies other keys were not processed
        return "없음"  

    formatted_사은품_info = extract_and_format_info(strSoup, 사은품_pattern)


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
        formatted_text_no_support if formatted_text_no_support else "제공안함",
        formatted_사은품_info
    ]

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

error_queue = Queue()
thread_completed = Event()
stop_signal = Event()


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
                    error_message = f"An error occurred when fetching data of: {e}"
                    error_queue.put(error_message)
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
            driver.delete_all_cookies()
            url_queue.task_done()
            if stop_signal.is_set():
                break
    except Exception as e:
        # Log the exception or handle it as needed
        error_message = f"An error occurred when fetching data of {url}: {e}"
        error_queue.put(error_message)
    finally:
        driver.quit()

PER_MINUTE_LIMIT = 60
@sleep_and_retry
@limits(calls=PER_MINUTE_LIMIT, period=60)
def update_sheet(data_queue, sheet_update_lock, sheet_id):
    while True:
        batch_data = []  # Accumulate data here
        while len(batch_data) < 10:  # Wait until we have 10 records
            processed_data = data_queue.get()
            if processed_data is None:  # Sentinel value to indicate completion
                if len(batch_data) > 0:  # Push any remaining records
                    with sheet_update_lock:
                        try:
                            # Assuming pushToSheet can handle a list of data
                            pushToSheet(batch_data, sheet_id, range='Sheet1!A:B')
                        except Exception as e:
                            error_message = f"An error occurred while updating the sheet: {e}"
                            error_queue.put(error_message)
                return  # Exit after processing all data
            batch_data.append(processed_data)  # Add data to the batch

        # Push batch_data to Google Sheet
        with sheet_update_lock:
            try:
                # Ensure pushToSheet is adjusted to handle batch updates if necessary
                pushToSheet(batch_data, sheet_id, range='Sheet1!A:B')
            except Exception as e:
                error_message = f"An error occurred while updating the sheet: {e}"
                error_queue.put(error_message)
            finally:
                for _ in batch_data:  # Acknowledge each item in the batch
                    data_queue.task_done()
        if stop_signal.is_set():
                break





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
        # options.add_argument("window-size=800x2000")
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

        CHROMEDRIVER = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        service = fs.Service(CHROMEDRIVER)
        driver = webdriver.Chrome(
                                options=options,
                                service=service
                                )
        return driver

     # Start data fetching threads
    fetch_threads = []
    for _ in range(3):
        driver = setup_driver()  # Each thread gets its own driver instance
        t = threading.Thread(target=fetch_data, args=(driver, url_queue, data_queue))
        t.start()
        fetch_threads.append(t)

    # Start sheet updating threads
    update_threads = []
    for _ in range(1):
        t = threading.Thread(target=update_sheet, args=(data_queue, sheet_update_lock, sheet_id))
        t.start()
        update_threads.append(t)

    # Wait for data fetching threads to finish and signal update threads to finish
    for thread in fetch_threads:
        thread.join()
    for _ in range(2):
        data_queue.put(None)  # Sentinel value for each update thread

    # Wait for update threads to finish
    for thread in update_threads:
        thread.join()
    autoResizeColumns(sheet_id, 0)
    thread_completed.set()
    if stop_signal.is_set():
        return

def fetch_url_Just_Moyos(url_fetch_queue):
    end_of_list = False
    i = 1
    base_url = "https://www.moyoplan.com"
    while not end_of_list:
        BaseUrl = "https://www.moyoplan.com/plans"  # Remove any trailing slash
        planListUrl = f"{BaseUrl}?page={i}"  
        response = requests.get(planListUrl)
        soup = BeautifulSoup(response.text, 'html.parser')
        a_tags = soup.find_all('a', class_='e3509g015')
        if not a_tags:  # If no a_tags found, possibly end of list
            end_of_list = True
        for a_tag in a_tags:
            link = a_tag['href']
            plan_detail_url = f"{base_url}{link}"
            url_fetch_queue.put(plan_detail_url)  # Put each link into the queue individually
        i += 1  # Increment page number
        if stop_signal.is_set():
            break  




def fetch_data_Just_Moyos(driver, url_fetch_queue, data_queue):
    try:
        base_url = "https://www.moyoplan.com/plans"
        driver.get(base_url)
        while not url_fetch_queue.empty():
            url = url_fetch_queue.get()
            # Fetch and process data from the URL
            attempts = 0
            fetch_success = False
            
            while attempts < 5 and not fetch_success:
                try: 
                    driver.get(url)
                    driver.refresh()
                    WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME, "css-yg1ktq")))
                    button = driver.find_element(By.XPATH, "//button[contains(@class, 'css-yg1ktq')]")
                    driver.execute_script("arguments[0].click();", button)
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-1ipix51')))
                    # div_css_selector = ".css-1b8xqgi"
                    # div_element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, div_css_selector)))

                    svg_element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/main/div/section[4]/div/div/div/div/div/div[1]/div[1]/div")))
                    # hover = ActionChains(driver).move_to_element(svg_element)
                    # hover.perform()
                    # tooltip = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'span[role="tooltip"]')))
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    strSoup = soup.get_text()
                    expired = "서비스 중입니다"
                    tooltip_text = 'no pass'
                    if svg_element is '':
                        tooltip_text = 'pass'
                    regex_formula = regex_extract(strSoup)
                    planUrl = str(url)
                    # data = [planUrl] + regex_formula + [tooltip_text] + [expired]
                    # data = [planUrl] + regex_formula + [expired]
                    data = [planUrl] + regex_formula + [tooltip_text]
                    # Put the processed data into the data queue
                    data_queue.put(data)
                    fetch_success = True
                except TimeoutException as e:
                    attempts += 1
                    error_queue.put(f"Timeout occurred for {url}, attempt {attempts}. Retrying...")
                    if attempts == 5:
                        error_message = f"Failed to fetch data after 5 attempts for URL: {url}"
                        error_queue.put(error_message)
            if stop_signal.is_set():
                break  

            driver.delete_all_cookies()
            url_fetch_queue.task_done()
    except Exception as e:
        # Log the exception or handle it as needed
        error_message = f"An error occurred when fetching data of {url}: {e}"
        error_queue.put(error_message)
    finally:
        driver.quit()

def moyocrawling_Just_Moyos(sheet_id, sheetUrl):
    def setup_driver():
            options = ChromeOptions()
            options.add_argument("--headless")
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('window-size=800x2000')  # Adjust as needed
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)

            CHROMEDRIVER = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
            service = fs.Service(CHROMEDRIVER)
            driver = webdriver.Chrome(
                                    options=options,
                                    service=service
                                    )
            return driver
    url_fetch_queue = Queue()
    data_queue = Queue()
    sheet_update_lock = threading.Lock()

    fetch_url_threads = []
    for _ in range(1):
        t = threading.Thread(target=fetch_url_Just_Moyos, args=(url_fetch_queue,))
        t.start()
        fetch_url_threads.append(t)

    # Start data fetching threads
    fetch_threads = []
    for _ in range(3):
        driver = setup_driver()  # Each thread gets its own driver instance
        t = threading.Thread(target=fetch_data_Just_Moyos, args=(driver, url_fetch_queue, data_queue))
        t.start()
        fetch_threads.append(t)

    # Start sheet updating threads
    update_threads = []
    for _ in range(1):
        t = threading.Thread(target=update_sheet, args=(data_queue, sheet_update_lock, sheet_id))
        t.start()
        update_threads.append(t)

    # Wait for data url fetching threads to finish and signal fetch threads to finish
    for thread in fetch_url_threads:
        thread.join()
    for _ in range(1):
        url_fetch_queue.put(None)

    # Wait for data fetching threads to finish and signal update threads to finish
    for thread in fetch_threads:
        thread.join()
    for _ in range(5):
        data_queue.put(None)  # Sentinel value for each update thread

    # Wait for update threads to finish
    for thread in update_threads:
        thread.join()
    autoResizeColumns(sheet_id, 0)
    thread_completed.set()
    if stop_signal.is_set():
        return
    



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
            st.session_state['Just_Moyos'] = False
            st.write("Starting URL: ", url1)
            st.write("Last URL: ", url2)
        else:
            st.warning("Please enter at least one end parameter.")

    if st.button("Just Moyos"):
        st.session_state['show_download_buttons'] = True
        st.session_state['BaseUrl'] = base_url
        st.session_state['Just_Moyos'] = True



def moyocrawling_wrapper(url1, url2, sheet_id):
    try:
        moyocrawling(url1, url2, sheet_id)
    except Exception as e:
        error_message = f"An error occurred in moyocrawling: {e}\n{traceback.format_exc()}"
        error_queue.put(error_message)

def moyocrawling_just_moyos_wrapper(sheet_id, sheetUrl):
    try:
        moyocrawling_Just_Moyos(sheet_id, sheetUrl)
    except Exception as e:
        error_message = f"An error occurred in moyocrawling: {e}\n{traceback.format_exc()}"
        error_queue.put(error_message)

if 'show_download_buttons' in st.session_state and st.session_state['show_download_buttons']:
    url1 = st.session_state.get('url1')
    url2 = st.session_state.get('url2')
    col1, col2 = st.columns(2)

    with col1:
        gs_button_pressed = st.button("Google Sheet", key="gs_button", use_container_width=True)
    with col2:
        stop_button_pressed = st.button("Stop Processing", key="stop_button")
    if gs_button_pressed:
        if st.session_state['Just_Moyos'] is False:
            try:
                export_to_google_sheet = True
                headers = {
                    'values': ["url", "MVNO", "요금제명", "월 요금", "월 데이터", "일 데이터", "데이터 속도", "통화(분)", "문자(건)", "통신사", "망종류", "할인정보", "통신사 약정", "번호이동 수수료", "일반 유심 배송", "NFC 유심 배송", "eSim", "지원", "미지원", "이벤트"]
                }
                with st.spinner("Processing for Google Sheet..."):
                    # Create new Google Sheet and push headers
                    sheet_id, webviewlink = create_new_google_sheet(url1, url2)
                    pushToSheet(headers, sheet_id, 'Sheet1!A1:L1')
                    formatHeaderTrim(sheet_id, 0)
                    sheetUrl = str(webviewlink)
                    st.link_button("Go to see", sheetUrl)

                    # Start the moyocrawling process in a separate thread
                    threading.Thread(target=moyocrawling_wrapper, args=(url1, url2, sheet_id)).start()

                    # Wait for the completion of the moyocrawling process
                    while not thread_completed.is_set():
                        if not error_queue.empty():
                            error_message = error_queue.get()
                            st.error(error_message)
                        time.sleep(0.1)


                if not error_queue.empty():
                # If there are any remaining errors in the queue, display them
                    while not error_queue.empty():
                        st.error(error_queue.get())
                else:
                    st.success("Process Completed")

            except Exception as e:
                st.error(f"An Error Occurred: {e}")
        
        else:
            try:
                headers = {
                    'values': ["url", "MVNO", "요금제명", "월 요금", "월 데이터", "일 데이터", "데이터 속도", "통화(분)", "문자(건)", "통신사", "망종류", "할인정보", "통신사 약정", "번호이동 수수료", "일반 유심 배송", "NFC 유심 배송", "eSim", "지원", "미지원", "이벤트"]
                }
                with st.spinner("Processing for Google Sheet..."):
                    # Create new Google Sheet and push headers
                    sheet_id, webviewlink = create_new_google_sheet_just_moyos()
                    pushToSheet(headers, sheet_id, 'Sheet1!A1:L1')
                    formatHeaderTrim(sheet_id, 0)
                    sheetUrl = str(webviewlink)
                    st.link_button("Go to see", sheetUrl)
                    # while not end_of_list:
                    #     BaseUrl = st.session_state.get('BaseUrl').rstrip('/')  # Remove any trailing slash
                    #     planListUrl = f"{BaseUrl}?page={i}"  
                    #     response = requests.get(planListUrl)
                    #     soup = BeautifulSoup(response.text, 'html.parser')
                    #     a_tags = soup.find_all('a', class_='e3509g015')
                    #     if not a_tags:  # If no a_tags found, possibly end of list
                    #         end_of_list = True
                    #     for a_tag in a_tags:
                    #         link = a_tag['href']
                    #         url_queue.put(link)  # Put each link into the queue individually
                    #     i += 1  # Increment page number

                    # url_list = []
                    # while not url_queue.empty():
                    #     url = url_queue.get()
                    #     url_list.append(str(url))
                    threading.Thread(target=moyocrawling_just_moyos_wrapper, args=(sheet_id, sheetUrl)).start()
                    while not thread_completed.is_set():
                            if not error_queue.empty():
                                error_message = error_queue.get()
                                st.error(error_message)
                            time.sleep(0.1)


                    if not error_queue.empty():
                    # If there are any remaining errors in the queue, display them
                        while not error_queue.empty():
                            st.error(error_queue.get())
                    else:
                        st.success("Process Completed")

            except Exception as e:
                st.error(f"An Error Occurred: {e}")

    if stop_button_pressed:
        stop_signal.set()  # Signal threads to stop
        st.write("Stopped all processes...")


