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
# import requests
# from bs4 import BeautifulSoup
# import platform
# import os, sys
import streamlit as st
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome import service as fs
from selenium.webdriver import ChromeOptions
# from webdriver_manager.core.utils import ChromeType
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
import streamlit_extras
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.row import row
from streamlit_gsheets import GSheetsConnection


st.set_page_config(
    page_title="CrawlingAI_Plus",
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
    # CrawlingAI Plus
            
    Extract data of any website!

    Enter url at the sidebar and retrieve the data without html tag! 
"""
)


with st.sidebar:
    url = st.text_input(
        "Write down a URL",
        placeholder="https://example.com",
    )


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
    html = driver.page_source
    driver.close()
    return html


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



if url:
    if ".xml" not in url:
        result = start_chromium(url)
        html_content = start_chromium(url)
        document = Document(page_content=html_content)
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
