# coding:utf-8
from curses import raw
from email.mime import base
# from operator import call
# from tkinter import N
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
from selenium.common.exceptions import NoAlertPresentException, TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from Google import Create_Service
from queue import Queue
import time
from ratelimit import limits, sleep_and_retry
import traceback
from datetime import datetime
import pytz
from multiprocessing import Process, Manager
import psutil
import pandas as pd
from string import ascii_uppercase



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

def backup_and_refresh(sheet_id, sheet_name='Sheet3', start_row=2, serviceInstance=None):
    if not serviceInstance:
        serviceInstance = googleSheetConnect()
    try:
        # Create a new backup spreadsheet
        kst = pytz.timezone('Asia/Seoul')  # Ensure pytz is imported
        current_datetime = datetime.now(kst).strftime("%Y/%m/%d - %H:%M:%S")
        backup_file_name = f"Backup 모요 요금제 {current_datetime}"
        new_spreadsheet = serviceInstance.spreadsheets().create(body={
            'properties': {'title': backup_file_name}
        }, fields='spreadsheetId').execute()
        new_spreadsheet_id = new_spreadsheet.get('spreadsheetId')

        # Get the ID of "Sheet3", "planDataSheet" from the original spreadsheet
        sheet_metadata = serviceInstance.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        sheet_id_to_copy = None
        sheet_id_to_delete = None
        for sheet in sheets:
            if sheet.get("properties", {}).get("title", "") == sheet_name:
                sheet_id_to_copy = sheet.get("properties", {}).get("sheetId", "")
            elif sheet.get("properties", {}).get("title", "") == "planDataSheet":
                sheet_id_to_delete = sheet.get("properties", {}).get("sheetId", "")
            if sheet_id_to_copy and sheet_id_to_delete:
                break

        # Get the value of last row in "Sheet3" of the original spreadsheet
        sheet3_last_row_value = serviceInstance.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A1:A"
        ).execute().get('values', [])
        last_row_value = sheet3_last_row_value[-1][0] if sheet3_last_row_value else None

        fetch_completed = False
        if last_row_value == "Fetch data ended successfully":
            fetch_completed = True

        if sheet_id_to_copy is not None and sheet_id_to_delete is not None and fetch_completed:
            try:
                # Delete the existing sheet
                delete_request = {
                    "deleteSheet": {
                        "sheetId": sheet_id_to_delete
                    }
                }
                serviceInstance.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={"requests": [delete_request]}
                ).execute()

                # Duplicate "Sheet3" with the name of the deleted sheet
                duplicate_request = {
                    "duplicateSheet": {
                        "sourceSheetId": sheet_id_to_copy,
                        "insertSheetIndex": 0,  # Adjust as needed
                        "newSheetName": "planDataSheet"  # Replace with your desired name
                    }
                }
                serviceInstance.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={"requests": [duplicate_request]}
                ).execute()
            except Exception as e:
                st.write(f"Failed to replace sheet: {e}")
        
        # Copy the data from "Sheet3" of the original spreadsheet to the new spreadsheet
        if sheet_id_to_copy is not None:
            try:
                # Copy "Sheet3" to the new spreadsheet
                serviceInstance.spreadsheets().sheets().copyTo(
                    spreadsheetId=sheet_id_to_delete,
                    sheetId=sheet_id_to_copy,
                    body={'destinationSpreadsheetId': new_spreadsheet_id}
                ).execute()
            except Exception as e:
                st.write(f"Failed to copy sheet: {e}")
        else:
            st.write(f"Sheet '{sheet_name}' not found in the original spreadsheet.")

        # Optionally, clear the data in "Sheet3" of the original spreadsheet
        sheet_metadata = serviceInstance.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        sheet_properties = None
        for sheet in sheets:
            if sheet.get("properties", {}).get("title", "") == sheet_name:
                sheet_properties = sheet.get("properties", {})
                break

        if sheet_properties is not None:
            sheet_grid_properties = sheet_properties.get("gridProperties", {})
            sheet_row_count = sheet_grid_properties.get("rowCount", 0)
            sheet_column_count = sheet_grid_properties.get("columnCount", 0)
            def column_number_to_letter(n):
                string = ""
                while n > 0:
                    n, remainder = divmod(n - 1, 26)
                    string = chr(65 + remainder) + string
                return string
            last_column_letter = column_number_to_letter(sheet_column_count)

            range = f'{sheet_name}!A2:{last_column_letter}{sheet_row_count}'
            serviceInstance.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range=range,
                body={}
            ).execute()
        else:
            st.write(f"Sheet '{sheet_name}' not found in the spreadsheet.")

    except Exception as e:
        st.write(f"Failed to backup and refresh sheet: {e}")

def pushToSheet(data, spreadsheet_id, range='Sheet3!A', serviceInstance=None):

    try:
        serviceInstance = serviceInstance if serviceInstance else googleSheetConnect()
        body = {'values': data}
        result = serviceInstance.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueInputOption='USER_ENTERED',  # or 'RAW'
            body=body
        ).execute()

        


        # CPU usage
        cpu_percent = psutil.cpu_percent()

        # Virtual (Physical) Memory
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent  # Memory usage in percent
        # Correct calculation for used and total memory in MB
        memory_used_mb = memory_info.used / (1024 ** 2)  # Convert from bytes to MB
        memory_total_mb = memory_info.total / (1024 ** 2)  # Convert from bytes to MB

        # Swap Memory
        swap_info = psutil.swap_memory()
        # Correct calculation for used and total swap in MB
        swap_used_mb = swap_info.used / (1024 ** 2)  # Convert from bytes to MB
        swap_total_mb = swap_info.total / (1024 ** 2)  # Convert from bytes to MB

        print(f"CPU: {cpu_percent}%, Physical Memory: {memory_percent}%")
        print(f"Physical Memory Used: {memory_used_mb:.2f} MB, Total: {memory_total_mb:.2f} MB")
        print(f"Swap Used: {swap_used_mb:.2f} MB, Total: {swap_total_mb:.2f} MB")
        return result, serviceInstance
    except Exception as e:
        # Re-raise the exception to be caught in the calling function
        # print(f"Failed to push data to sheet: {e}")
        raise Exception(f"Failed to push data to sheet: {e}")


def formatHeaderTrim(sheet_id, sheet_name='Sheet3', sheet_index=2, serviceInstance=None):
    # Retrieve sheet metadata
    sheet_metadata = serviceInstance.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    
    # Find the sheet with the specified name
    sheet = None
    for s in sheets:
        if s.get('properties', {}).get('title') == sheet_name:
            sheet = s
            break

    if sheet is None:
        print(f"No sheet named '{sheet_name}' found in the spreadsheet.")
        return

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
                "endColumnIndex": 21
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
    if totalColumns > 21:
        trim_columns_request = {
            "deleteDimension": {
                "range": {
                    "sheetId": sheetId,
                    "dimension": "COLUMNS",
                    "startIndex": 21,
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


def autoResizeColumns(sheet_id, sheet_index=2, serviceInstance=None):
    serviceInstance = serviceInstance if serviceInstance else googleSheetConnect(sheet_id)
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
        formatted_results = []
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match and match.group(1).strip():
                value = match.group(1).strip()
            else:
                formatted_results.append("제공안함")
                break
            formatted_results.append(f"{key}: {value}")
        return ', '.join(formatted_results)


    formatted_사은품_info = extract_and_format_info(strSoup, 사은품_pattern)

    카드_할인 = r"카드 결합 할인\s*(.*?)할인"
    카드_할인_정보 = re.search(카드_할인, strSoup)


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
        formatted_사은품_info,
        카드_할인_정보.group(1) + "할인" if 카드_할인_정보 else "제공안함", 
    ]

def convert_data_to_numeric(data):
    if isinstance(data, int) or isinstance(data, float):
        return data
    elif data == '무제한':
        return 100000  
    elif data == '제공안함':
        return 0  
    elif 'GB' in data:
        return float(data.replace('GB', ''))  
    elif 'MB' in data:
        return float(data.replace('MB', '')) / 1000  
    else:
        return 0

# Define the function to convert call and text data to numeric values
def convert_calls_texts_to_numeric(data):
    if isinstance(data, int) or isinstance(data, float):
        return data
    elif data == '무제한':
        return 100000
    elif data == '제공안함':
        return 0
    elif isinstance(data, str):
        return int(data.replace('분', '').replace('건', ''))
    else:
        return 0

# Define the scoring function
def calculate_score(row):
    weights = {
        '월 요금': -1,
        '월 데이터': 2,
        '일 데이터': 1,
        '데이터 속도': 1,
        '통화(분)': 1,
        '문자(건)': 1,
    }
    score = (weights['월 요금'] * row['월 요금'] +
             weights['월 데이터'] * row['월 데이터'] +
             weights['일 데이터'] * row['일 데이터'] +
             weights['데이터 속도'] * row['데이터 속도'] +
             weights['통화(분)'] * row['통화(분)'] +
             weights['문자(건)'] * row['문자(건)'])
    return score


def update_google_sheet(data, sheet_id, serviceInstance=None):
    pushToSheet(data, sheet_id, range='Sheet3!A', serviceInstance=serviceInstance)

error_queue = Queue()
log_queue = Queue()
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
                try:
                    사은품_링크 = driver.find_element(By.CSS_SELECTOR, 'a.css-1hdj7cf.e17wbb0s4')
                    사은품_링크 = 사은품_링크.get_attribute('href') if 사은품_링크 else None
                except NoSuchElementException:
                    사은품_링크 = None


                try:
                    카드할인_링크 = driver.find_element(By.CSS_SELECTOR, 'a.css-pnutty.ema3yz60')
                    카드할인_링크 = 카드할인_링크.get_attribute('href') if 카드할인_링크 else None
                except NoSuchElementException:
                    카드할인_링크 = None
                
                strSoup = soup.get_text()
                expired = "서비스 중입니다"

            # if export_to_google_sheet:
            if result is "":
                regex_formula = regex_extract(strSoup)
                planUrl = str(url)
                if regex_formula[18] is not "제공안함" and 사은품_링크 is not None:
                    regex_formula[18] += (f", link:{사은품_링크}")
                if regex_formula[19] is not "제공안함" and 카드할인_링크 is not None:
                    regex_formula[19] += (f", link:{카드할인_링크}")
                data = [planUrl] + regex_formula + [expired]
            else:
                planUrl = str(url)
                data = [ planUrl,"-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-"]
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
def rate_limited_pushToSheet(data, sheet_id, range, serviceInstance=None):
    return pushToSheet(data, sheet_id, range, serviceInstance)

def update_sheet(data_queue, sheet_update_lock, sheet_id, serviceInstance=None):
    while True:
        batch_data = []  # Accumulate data here
        while len(batch_data) < 10:  # Wait until we have 10 records
            processed_data = data_queue.get()
            if processed_data is None:  # Sentinel value to indicate completion
                batch_data.append(["Fetch data ended successfully"])  # Add a row indicating fetch data ended
                if len(batch_data) > 0:  # Push any remaining records
                    with sheet_update_lock:
                        retry_push_to_sheet(batch_data, sheet_id, 'Sheet3!A2', serviceInstance)
                return  # Exit after processing all data
            batch_data.append(processed_data)  # Add data to the batch

        # Push batch_data to Google Sheet with retries
        with sheet_update_lock:
            retry_push_to_sheet(batch_data, sheet_id, 'Sheet3!A2', serviceInstance)

            def find_column_index_by_header(spreadsheet_id, sheet_title, header_name, serviceInstance):
                # Fetch the header row. Assume it's the first row.
                range_name = f"{sheet_title}!1:1"  # Adjust the range if your headers are not in the first row.
                result = serviceInstance.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()
                headers = result.get('values', [[]])[0]  # Get the first row (header row)
                
                # Find the index of the header_name
                try:
                    column_index = headers.index(header_name)
                    return column_index
                except ValueError:
                    print(f"Header '{header_name}' not found.")
                    return None
                
            column_index = find_column_index_by_header(sheet_id, 'Sheet3', '점수', serviceInstance)
            def get_sheet_id(spreadsheet_id, sheet_title, serviceInstance):
                # Fetch the spreadsheet's metadata
                result = serviceInstance.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                sheets = result.get('sheets', [])
                
                # Find the sheet with the given title and return its ID
                for sheet in sheets:
                    if sheet.get('properties', {}).get('title') == sheet_title:
                        return sheet.get('properties', {}).get('sheetId')
                
                print(f"Sheet '{sheet_title}' not found.")
                return None

            # Use the function to get the sheet_id
            sheet3_id = get_sheet_id(sheet_id, 'Sheet3', serviceInstance)

            def sort_sheet_by_column(sheet_id_to_sort, column_index=0, serviceInstance=None):
                request_body = {
                    "requests": [
                        {
                            "sortRange": {
                                "range": {
                                    "sheetId": sheet_id_to_sort,
                                    "startRowIndex": 1,  # Exclude header row
                                },
                                "sortSpecs": [
                                    {
                                        "dimensionIndex": column_index,
                                        "sortOrder": "DESCENDING"
                                    }
                                ]
                            }
                        }
                    ]
                }
                serviceInstance.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=request_body).execute()
            sort_sheet_by_column(sheet3_id, column_index, serviceInstance)
        if stop_signal.is_set():
            break

def retry_push_to_sheet(data, sheet_id, range, serviceInstance, backoff_factor=1):
    """Attempt to push data to the sheet indefinitely until successful, with exponential backoff."""
    while True:
        try:
            print("Attempting to push data to sheet")
            rate_limited_pushToSheet(data, sheet_id, range, serviceInstance)
            print(f"Data successfully pushed to sheet")
            break  # Success! Break out of the loop.
        except Exception as e:
            wait_time = backoff_factor # Exponential backoff
            print(f"Failed to push data to sheet: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)



def moyocrawling(url1, url2, sheet_id, serviceInstance):
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
        t = threading.Thread(target=update_sheet, args=(data_queue, sheet_update_lock, sheet_id, serviceInstance))
        t.start()
        update_threads.append(t)

    # Wait for data fetching threads to finish and signal update threads to finish
    for thread in fetch_threads:
        thread.join()
    for _ in range(1):
        data_queue.put(None)  # Sentinel value for each update thread

    # Wait for update threads to finish
    for thread in update_threads:
        thread.join()
    autoResizeColumns(sheet_id, 0, serviceInstance)
    thread_completed.set()
    if stop_signal.is_set():
        return

def fetch_url_Just_Moyos(url_fetch_queue):
    end_of_list = False
    i = 1
    base_url = "https://www.moyoplan.com"
    while not end_of_list:
        attempts = 0  # Initialize attempts counter
        while attempts < 5:  # Attempt to fetch data up to 5 times
            try:
                BaseUrl = "https://www.moyoplan.com/plans"  # Remove any trailing slash
                planListUrl = f"{BaseUrl}?page={i}"  
                response = requests.get(planListUrl)
                if response.status_code != 200:
                    error_message = f"Failed to fetch data from {planListUrl}. Status code: {response.status_code}"
                    error_queue.put(error_message)
                    attempts += 1
                    if attempts >= 5:
                        error_queue.put(f"Max attempts reached for {planListUrl}. Skipping...")
                        break
                soup = BeautifulSoup(response.text, 'html.parser')
                a_tags = soup.find_all('a', class_='e3509g015')
                if not a_tags:  # If no a_tags found, possibly end of list
                    end_of_list = True
                    break  # Break out of the inner loop
                for a_tag in a_tags:
                    link = a_tag['href']
                    plan_detail_url = f"{base_url}{link}"
                    url_fetch_queue.put(plan_detail_url)  # Put each link into the queue individually
                i += 1  # Increment page number
            except Exception as e:
                error_queue.put(str(e))
                attempts += 1  # Increment attempts counter
            if attempts >= 5:
                break  # Break out of the outer loop if max attempts reached
        if stop_signal.is_set():
            break 
    print(f"URL Fetch Thread Finished at page = {i}//////////////////////////////////////////////////////////////////")

def setup_driver():
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    # options.add_argument('window-size=800x2000')  # Adjust as needed
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    CHROMEDRIVER = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
    service = fs.Service(CHROMEDRIVER)
    driver = webdriver.Chrome(
                            options=options,
                            service=service
                            )
    return driver

def convert_data_to_numeric(data):
    if isinstance(data, int) or isinstance(data, float):
        return data
    elif data == '무제한':
        return 100000  
    elif data == '제공안함':
        return 0  
    elif 'GB' in data:
        return float(data.replace('GB', ''))  
    elif 'MB' in data:
        return float(data.replace('MB', '')) / 1000  
    else:
        return 0

# Define the function to convert call and text data to numeric values
def convert_calls_texts_to_numeric(data):
    if isinstance(data, int) or isinstance(data, float):
        return data
    elif data == '무제한':
        return 100000
    elif data == '제공안함':
        return 0
    elif isinstance(data, str):
        return int(data.replace('분', '').replace('건', ''))
    else:
        return 0

# Define the scoring function
def calculate_score(rawMonthPayment, rawMonthData, rawDailyData, rawDataSpeed, rawCall, rawText):
    weights = {
        '월 요금': -1,
        '월 데이터': 2,
        '일 데이터': 1,
        '데이터 속도': 1,
        '통화(분)': 1,
        '문자(건)': 1,
    }
    score = (weights['월 요금'] * rawMonthPayment +
            weights['월 데이터'] * rawMonthData +
            weights['일 데이터'] * rawDailyData +
            weights['데이터 속도'] * rawDataSpeed +
            weights['통화(분)'] * rawCall +
            weights['문자(건)'] * rawText)
    return score

def fetch_data_Just_Moyos(url_fetch_queue, data_queue):
    try:
        driver = setup_driver()
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
                    # WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'css-1ipix51')))
                    # div_css_selector = ".css-1b8xqgi"
                    # div_element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, div_css_selector)))

                    # svg_element = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div[2]/main/div/section[4]/div/div/div/div/div/div[1]/div[1]/div")))
                    # hover = ActionChains(driver).move_to_element(svg_element)
                    # hover.perform()
                    # tooltip = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'span[role="tooltip"]')))
                    try:
                        사은품_링크 = driver.find_element(By.CSS_SELECTOR, 'a.css-1hdj7cf.e17wbb0s4')
                        사은품_링크 = 사은품_링크.get_attribute('href') if 사은품_링크 else None
                    except NoSuchElementException:
                        사은품_링크 = None


                    try:
                        카드할인_링크 = driver.find_element(By.CSS_SELECTOR, 'a.css-pnutty.ema3yz60')
                        카드할인_링크 = 카드할인_링크.get_attribute('href') if 카드할인_링크 else None
                    except NoSuchElementException:
                        카드할인_링크 = None

                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    strSoup = soup.get_text()
                    regex_formula = regex_extract(strSoup)
                    if regex_formula[18] is not "제공안함" and 사은품_링크 is not None:
                        regex_formula[18] += (f", link:{사은품_링크}")
                    if regex_formula[19] is not "제공안함" and 카드할인_링크 is not None:
                        regex_formula[19] += (f", link:{카드할인_링크}")
                    planUrl = str(url)
                    # data = pd.Series([planUrl] + regex_formula)
                    
                    # rawMonthPayment = int(data[3].replace('원', '').replace(',', ''))
                    # rawMonthData = convert_data_to_numeric(data[4])
                    # rawDailyData = convert_data_to_numeric(data[5])
                    # rawDataSpeed = float(data[6].replace('제공안함', '0mbps').replace('mbps', '')) if isinstance(data[6], str) else data[6]
                    # rawCall = convert_calls_texts_to_numeric(data[7])
                    # rawText = convert_calls_texts_to_numeric(data[8])

                    # score = calculate_score(rawMonthPayment, rawMonthData, rawDailyData, rawDataSpeed, rawCall, rawText)

                    # new_data = pd.Series([rawMonthPayment, rawMonthData, rawDailyData, rawDataSpeed, rawCall, rawText, score])
                    
                    # data_df = data.to_frame().T
                    # new_data_df = new_data.to_frame().T

                    # data = pd.concat([data_df, new_data_df], axis=1)
                    # print ({data})
                    # data_queue.put(data.values.tolist())
                    data = [planUrl] + regex_formula
                    
                    rawMonthPayment = int(data[3].replace('원', '').replace(',', ''))
                    rawMonthData = convert_data_to_numeric(data[4])
                    rawDailyData = convert_data_to_numeric(data[5])
                    rawDataSpeed = float(data[6].replace('제공안함', '0mbps').replace('mbps', '')) if isinstance(data[6], str) else data[6]
                    rawCall = convert_calls_texts_to_numeric(data[7])
                    rawText = convert_calls_texts_to_numeric(data[8])

                    score = calculate_score(rawMonthPayment, rawMonthData, rawDailyData, rawDataSpeed, rawCall, rawText)

                    new_data = [rawMonthPayment, rawMonthData, rawDailyData, rawDataSpeed, rawCall, rawText, score]
                    
                    data = data + new_data
                    print (data)
                    data_queue.put(data)
                    print(f"Data queued for {url}")
                    fetch_success = True
                    attempts = 0
                except (TimeoutException, WebDriverException) as e:
                    attempts += 1
                    if driver:
                        driver.quit()
                    driver = setup_driver()
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
        if driver:
            driver.quit()

def moyocrawling_Just_Moyos(sheet_id, sheetUrl, serviceInstance):
    url_fetch_queue = Queue()
    data_queue = Queue()
    sheet_update_lock = threading.Lock()

    fetch_url_threads = []
    for _ in range(1):
        t = threading.Thread(target=fetch_url_Just_Moyos, args=(url_fetch_queue,))
        t.start()
        fetch_url_threads.append(t)
    print("Fetch URL Thread Started/////////////////////////////////////////////////////////////////")

    # Start data fetching threads
    fetch_threads = []
    for _ in range(4):
        t = threading.Thread(target=fetch_data_Just_Moyos, args=(url_fetch_queue, data_queue))
        t.start()
        fetch_threads.append(t)
    print("Fetch Data Thread Started/////////////////////////////////////////////////////////////////")

    # Start sheet updating threads
    update_threads = []
    for _ in range(1):
        t = threading.Thread(target=update_sheet, args=(data_queue, sheet_update_lock, sheet_id, serviceInstance))
        t.start()
        update_threads.append(t)
    print("Update Thread Started/////////////////////////////////////////////////////////////////")

    # process1 = Process(target=update_sheet, args=(data_queue, sheet_update_lock, sheet_id, serviceInstance))
    # process2 = Process(target=update_sheet, args=(data_queue, sheet_update_lock, sheet_id, serviceInstance))

    # # Start your processes
    # process1.start()
    # process2.start()

    # # Wait for both processes to complete
    # process1.join()
    # process2.join()

    # Wait for data url fetching threads to finish and signal fetch threads to finish
    for thread in fetch_url_threads:
        thread.join()
    for _ in range(1):
        url_fetch_queue.put(None)
    print("URL Fetch Thread Finished/////////////////////////////////////////////////////////////////")

    # Wait for data fetching threads to finish and signal update threads to finish
    for thread in fetch_threads:
        thread.join()
    for _ in range(1):
        data_queue.put(None)  # Sentinel value for each update thread
    print("Data Fetch Thread Finished/////////////////////////////////////////////////////////////////")
    # Wait for update threads to finish
    for thread in update_threads:
        thread.join()
    print("Update Thread Finished/////////////////////////////////////////////////////////////////")
    # autoResizeColumns(sheet_id, 0, serviceInstance)
    print("Auto Resize Column Finished/////////////////////////////////////////////////////////////////")
    thread_completed.set()
    print("All Threads Completed/////////////////////////////////////////////////////////////////")
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



def process_google_sheet(is_just_moyos, url1="", url2=""):
    headers = {
        'values': ["url", "MVNO", "요금제명", "월 요금", "월 데이터", "일 데이터", "데이터 속도", "통화(분)", "문자(건)", "통신사", "망종류", "할인정보", "통신사 약정", "번호이동 수수료", "일반 유심 배송", "NFC 유심 배송", "eSim", "지원", "미지원", "이벤트", "카드 할인", "월 요금 (숫자)", "월 데이터 (숫자)", "일 데이터 (숫자)", "데이터 속도 (숫자)", "통화(분) (숫자)", "문자(건) (숫자)", "점수"]
    }
    with st.spinner("Processing for Google Sheet..."):
        # sheet_id, webviewlink = create_new_google_sheet(is_just_moyos, url1, url2)
        sheet_id = "12s6sKkpWkHdsx_2kxFRim3M7-VTEQBmbG4OPgFrG0n0"
        webviewlink = "https://docs.google.com/spreadsheets/d/12s6sKkpWkHdsx_2kxFRim3M7-VTEQBmbG4OPgFrG0n0/edit?usp=sharing"
        result, googlesheetInstance = pushToSheet(headers, sheet_id, 'Sheet3!A1', serviceInstance=None)
        backup_and_refresh(sheet_id=sheet_id, sheet_name="Sheet3", start_row=2, serviceInstance=googlesheetInstance)
        sheetUrl = str(webviewlink)
        st.link_button("Go to see", sheetUrl)

        # Start the crawling process after formatting the header
        if is_just_moyos:
            moyocrawling_Just_Moyos(sheet_id, sheetUrl, googlesheetInstance)
            print("Just Moyos Crawling Started/////////////////////////////////////////////////////////////////")
        else:
            moyocrawling(url1, url2, sheet_id, googlesheetInstance)
            print("Crawling Started/////////////////////////////////////////////////////////////////")

        # Wait for the completion of the moyocrawling process
        while not thread_completed.is_set():
            if not error_queue.empty():
                error_message = error_queue.get()
                st.error(error_message)
            time.sleep(0.1)

    # If there are any remaining errors in the queue, display them
    if not error_queue.empty():
        while not error_queue.empty():
            st.error(error_queue.get())

    elif not log_queue.empty():
        while not log_queue.empty():
            st.info(log_queue.get())
    else:
        st.success("Process Completed")

if 'show_download_buttons' in st.session_state and st.session_state['show_download_buttons']:
    url1 = st.session_state.get('url1')
    url2 = st.session_state.get('url2')
    col1, col2 = st.columns(2)

    with col1:
        gs_button_pressed = st.button("Google Sheet", key="gs_button", use_container_width=True)
    with col2:
        stop_button_pressed = st.button("Stop Processing", key="stop_button", use_container_width=True)
    if gs_button_pressed:
        try:
            print("Processing Google Sheet.../////////////////////////////////////////////////////////////////")
            process_google_sheet(st.session_state['Just_Moyos'], url1, url2)
        except Exception as e:
            st.error(f"An Error Occurred: {e}")

    if stop_button_pressed:
        stop_signal.set()  # Signal threads to stop
        st.write("Stopped all processes...")