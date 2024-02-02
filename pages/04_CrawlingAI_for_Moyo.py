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
    except Exception as e:
        # Log the exception or handle it as needed
        error_message = f"An error occurred when fetching data of {url}: {e}"
        error_queue.put(error_message)
    finally:
        driver.quit()

# PER_MINUTE_LIMIT = 10
# @sleep_and_retry
# @limits(calls=PER_MINUTE_LIMIT, period=10)
# def update_sheet(data_queue, sheet_update_lock, sheet_id):
#     while True:
#         processed_data = data_queue.get()
#         if processed_data is None:  # Sentinel value to indicate completion
#             break
#         with sheet_update_lock:
#             try:
#                 pushToSheet(processed_data, sheet_id, range='Sheet1!A:B')
#             except Exception as e:
#                 error_message = f"An error occurred while updating the sheet: {e}"
#                 # Handle the error as needed (e.g., retry, log, notify)
#                 error_queue.put(error_message)

#             finally:
#                 data_queue.task_done()

PER_MINUTE_LIMIT = 60
@sleep_and_retry
@limits(calls=PER_MINUTE_LIMIT, period=60)
def update_sheet(data_queue, sheet_update_lock, sheet_id, fetching_completed):
    while not fetching_completed.is_set() or not data_queue.empty():
        try:
            data = data_queue.get(timeout=1)
            if data is None: continue  # Ignore sentinel if used
            with sheet_update_lock:
                # Adjust this call according to how your pushToSheet handles data
                pushToSheet([data], sheet_id, range='Sheet1!A:B')
            data_queue.task_done()
        except queue.Empty:
            continue
# def update_sheet(data_queue, sheet_update_lock, sheet_id, fetching_completed):
#     while not fetching_completed.is_set() or not data_queue.empty():
#         batch_data = []
#         try:
#             while len(batch_data) < 10:
#                 processed_data = data_queue.get(timeout=1)  # Adjust timeout as needed
#                 if processed_data is None:
#                     continue  # Ignore sentinel values
#                 batch_data.append(processed_data)
#                 data_queue.task_done()
#         except data_queue.empty:
#             pass  # Handle timeout by attempting to process collected batch data

#         if batch_data:
#             with sheet_update_lock:
#                 try:
#                     pushToSheet(batch_data, sheet_id, range='Sheet1!A:B')
#                 except Exception as e:
#                     error_message = f"An error occurred while updating the sheet in batch: {e}"
#                     error_queue.put(error_message)

# def update_sheet(data_queue, sheet_update_lock, sheet_id):
#     while True:
#         batch_data = []  # Initialize the batch
#         while len(batch_data) < 10:
#             processed_data = data_queue.get()
#             if processed_data is None:  # Check for sentinel value indicating completion
#                 break  # Exit the loop to process what's left in the batch
#             batch_data.append(processed_data)
#             data_queue.task_done()

#         if not batch_data:  # If the batch is empty, exit the loop
#             break

#         # Lock the sheet update to ensure thread-safe operations
#         with sheet_update_lock:
#             try:
#                 # Assuming pushToSheet can accept a list of lists (batch update)
#                 # Adjust the 'range' parameter as needed based on how pushToSheet is implemented
#                 pushToSheet(batch_data, sheet_id, range='Sheet1!A:B')
#             except Exception as e:
#                 error_message = f"An error occurred while updating the sheet in batch: {e}"
#                 # Handle the error as needed (e.g., retry, log, notify)
#                 error_queue.put(error_message)

#             finally:
#                 data_queue.task_done()



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
    for _ in range(6):
        driver = setup_driver()  # Each thread gets its own driver instance
        t = threading.Thread(target=fetch_data, args=(driver, url_queue, data_queue))
        t.start()
        fetch_threads.append(t)

    for thread in fetch_threads:
        thread.join()
    fetching_completed = threading.Event()

    # Start sheet updating threads
    update_threads = []
    for _ in range(1):
        t = threading.Thread(target=update_sheet, args=(data_queue, sheet_update_lock, sheet_id, fetching_completed))
        t.start()
        update_threads.append(t)

    fetching_completed.set()

    for _ in update_threads:
        data_queue.put(None)

    # Wait for update threads to finish
    for thread in update_threads:
        thread.join()


    autoResizeColumns(sheet_id, 0)
    thread_completed.set()


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
    except Exception as e:
        error_message = f"An error occurred in moyocrawling: {e}\n{traceback.format_exc()}"
        error_queue.put(error_message)


if 'show_download_buttons' in st.session_state and st.session_state['show_download_buttons']:
    url1 = st.session_state.get('url1')
    url2 = st.session_state.get('url2')
    col1, col2 = st.columns(2)

    gs_button_pressed = st.button("Google Sheet", key="gs_button", use_container_width=True)
    if gs_button_pressed:
        try:
            export_to_google_sheet = True
            headers = {
                'values': ["url", "MVNO", "요금제명", "월 요금", "월 데이터", "일 데이터", "데이터 속도", "통화(분)", "문자(건)", "통신사", "망종류", "할인정보", "통신사 약정", "번호이동 수수료", "일반 유심 배송", "NFC 유심 배송", "eSim", "지원", "미지원", "종료 여부"]
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

