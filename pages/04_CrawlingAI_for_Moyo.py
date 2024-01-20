# coding:utf-8
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
# import platform
import os, sys
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
import streamlit_extras
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.row import row
from streamlit_gsheets import GSheetsConnection
from Google import Create_Service


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
    # print (dir(serviceInstance))
    # st.write(dir(serviceInstance))  # Changed from print to st.write
    return serviceInstance

def googleSheetConnect():
    CLIENT_SECRETS = st.secrets["GoogleDriveAPISecrets"]
    # CLIENT_SECRETS = "QUUSai_clientID_desktop.json"
    API_NAME = 'sheets'
    API_VERSION = 'v4'
    SCOPES = ['https://www.googleapis.com/auth/drive']
    serviceInstance = Create_Service(CLIENT_SECRETS, API_NAME, API_VERSION, SCOPES)
    # print (dir(serviceInstance))
    # st.write(dir(serviceInstance))  # Changed from print to st.write
    return serviceInstance

def create_new_google_sheet():
    serviceInstance = googleDriveConnect()
    file_metadata = {
        'name': '모요 요금제',
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
    range = 'Sheet1!A:A'
    result = serviceInstance.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range,
        valueInputOption='USER_ENTERED',  # or 'RAW'
        body=body
    ).execute()

    return result

def get_answers(inputs):
    docs = inputs["docs"]
    question = inputs["question"]
    answers_chain = answers_prompt | llm
    # answers = []
    # for doc in docs:
    #     result = answers_chain.invoke(
    #         {"question": question, "context": doc.page_content}
    #     )
    #     answers.append(result.content)
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
            
    Extract data of any website!

    Enter url at the sidebar and retrieve the data without html tag! 
"""
)

def moyocrawling(url1, url2, export_to_google_sheet, sheet_id):
    part1 = url1.split('/')
    part2 = url2.split('/')
    try:
        number1 = int(part1[-1])
        number2 = int(part2[-1])
    except ValueError:
        return None
    
    if 'download_buttons' not in st.session_state:
        st.session_state['download_buttons'] = []

    for start_num in range(number1, number2 + 1, 50):
        end_num = min(start_num + 49, number2)
        crawledText = ""  # Initialize for each batch of requests
        
        for i in range(start_num, end_num + 1):
            # Construct the URL by replacing the last part with the current number
            current_url = '/'.join(part1[:-1] + [str(i)])
            
            # Make an HTTP request to the current URL
            response = requests.get(current_url)
            
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the HTML content with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser').get_text()
                if export_to_google_sheet:
                    regex = '\[(.*?)\]\s*(.*?)\s*\|\s*([\d,]+원)\s*\|\s*.*?월\s*(\d+)GB(?:\s*\+\s*매일\s*(\d+)GB)?.*?\((\d+mbps)\).*?(\d+분|무제한).*?(\d+건|무제한).*?(LG U\+|SKT|KT).*?(LTE|3G|4G|5G)(?:.*?(\d+개월\s*이후\s*[\d,]+원))?'
                    strSoup = str(soup)
                    sheetValue = f"=REGEXEXTRACT(\"{strSoup}\", \"{regex}\")"
                    planUrl = str(current_url)
                    data = [planUrl, sheetValue]
                    pushToSheet(data, sheet_id, range='Sheet1!A:B')
                crawledText += str(soup) + '\n\n'  # Append data with two newlines
            else:
                crawledText += current_url + " failed" + '\n\n'  # Append failure message with two newlines
        
        if not export_to_google_sheet:
            button_data = {
                'label': f"Text File ~ {end_num}",
                'data': crawledText.encode('utf-8'),
                'file_name': f"Text_File_{end_num}.txt"
            }
            st.session_state['download_buttons'].append(button_data)


# with st.sidebar:
#     url = st.text_input(
#         "Write down a Starting URL",
#         placeholder="https://example.com",
#     )

with st.sidebar:
    url1 = st.text_input("Write down a Starting URL", placeholder="https://example.com")
    url2 = st.text_input("Write down the Last URL", placeholder="https://example.com")

    if st.button("Start Crawling"):
        if url1 and url2:
            st.session_state['show_download_buttons'] = True
        else:
            st.warning("Please enter both URLs.")

if 'show_download_buttons' in st.session_state and st.session_state['show_download_buttons']:
    if st.button("TXT"):
        export_to_google_sheet = False
        moyocrawling(url1, url2, export_to_google_sheet)
    if st.button("Google Sheet"):
        export_to_google_sheet = True
        sheet_id, webviewlink = create_new_google_sheet()
        headers = {
        'values': ["url", "MVNO", "요금제명", "월요금", "월 데이터(GB)", "일 데이터", "데이터 속도", "통화(분)", "문자(건)", "통신사", "망종류", "할인정보"]
        }
        pushToSheet(headers, sheet_id, 'Sheet1!A1:L1')
        sheetUrl = str(webviewlink)
        st.link_button("Go to see", sheetUrl)
        moyocrawling(url1, url2, export_to_google_sheet, sheet_id)


# Outside the sidebar, render download buttons
for button in st.session_state.get('download_buttons', []):
    st.download_button(
        label=button['label'],
        data=button['data'],
        file_name=button['file_name'],
        mime="text/plain",
    )





# def generate_xpath(element):
#     """
#     Generates a simple XPath for a given element.
#     """
#     components = []
#     child = element
#     while child is not None:
#         parent = child.find_element(By.XPATH, '..')
#         siblings = parent.find_elements(By.XPATH, child.tag_name)
#         count = 0
#         index = 0
#         for i, sibling in enumerate(siblings, start=1):
#             if sibling == child:
#                 index = i
#             count += 1
#         if count > 1:
#             components.append(f'{child.tag_name}[{index}]')
#         else:
#             components.append(child.tag_name)
#         child = parent if parent.tag_name != 'html' else None

#     components.reverse()
#     return '/' + '/'.join(components)



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
    # wait = WebDriverWait(driver, 60)  # Timeout after 10 seconds
    # # locator = (By.CSS_SELECTOR, "a[href='/plans/16353']")
    # locator = (By.CSS_SELECTOR, "a.ekz2e6k13.css-1kmf8ij")
    # wait.until(EC.visibility_of_element_located(locator))

    # clickable_elements = driver.find_elements(By.XPATH, "//*[self::a or self::button or (self::input and @type='button')]")
    # clickable_elements_xpath = []
    # for element in clickable_elements:
    #     tag_name = element.tag_name
    #     text = element.text
    #     href = element.get_attribute('href') if tag_name == 'a' else "Not an anchor tag"

    #     # Append a tuple of tag name, text, and the 'btn' attribute value to the list
    #     clickable_elements_xpath.append((tag_name, text, href))

    html = driver.page_source
    # elements = driver.find_elements(By.XPATH, '//*')
    # element_xpaths = [generate_xpath(element) for element in elements]
    # file_dir = f"./.cache/screenshots"
    # os.makedirs(file_dir, exist_ok=True)
    # screenshot_path = os.path.join(file_dir, "screenshot.png")
    # driver.get_screenshot_as_file(screenshot_path)

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

    # Wait for the page to update after the click, if necessary
    # WebDriverWait(driver, 10).until(EC.some_condition)  # Replace 'some_condition' with an appropriate condition

    # Retrieve the updated HTML
    html2 = driver.page_source


    driver.close()
    return html, clickable_elements_content, html2


# def load_website(url):
#     try:
#         # response = requests.get(url)
#         # response.raise_for_status()

#         # # Use BeautifulSoup to extract text
#         # soup = BeautifulSoup(response.text, 'html.parser')
#         # text = soup.get_text()
#         # return text
        
#         # Assuming Html2TextTransformer is correctly defined/imported
#         try:
#             rawData = start_chromium(url)
#             # transformed = Html2TextTransformer().transform_documents([rawData])
#             return rawData
#         except Exception as e:
#             # Handle exceptions from Html2TextTransformer
#             print(f"Error during HTML to text transformation: {e}")
#             return e


#     except requests.HTTPError as e:
#         # Handle HTTP errors
#         return f"An HTTP error occurred: {e}"

# if url:
#     if ".xml" not in url:
#         retriever = load_website(url)
#         st.write(retriever)
import pandas as pd


# conn = st.connection("gsheets", type=GSheetsConnection)

# df = conn.read()

# # Print results.
# for row in df.itertuples():
#     st.write(f"{row.name} has a :{row.pet}:")


def convert_html_to_csv(html):
    # This function should convert HTML table data to CSV. 
    # This is a placeholder and needs to be adjusted based on the actual HTML structure.
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
