import streamlit as st
from langchain.chat_models import ChatOllama
from langchain.callbacks.base import BaseCallbackHandler
from langserve import RemoteRunnable
from langchain_core.runnables.schema import StreamEvent

st.set_page_config(
    page_title="쿠스AI",
    page_icon="🔒",
)

openaikey = st.secrets["OPENAI_API_KEY"]
#log openaikey
st.write(openaikey)
# ip = st.secrets["Langserve_endpoint"]
# LANGSERVE_ENDPOINT = f"http://{ip}/chat/c/N4XyA"
LANGSERVE_ENDPOINT = "https://4936-121-170-69-151.ngrok-free.app/chat/c/N4XyA"
class ChatCallbackHandler(BaseCallbackHandler):
    # message = ""

    # def on_llm_start(self, *args, **kwargs):
    #     self.message_box = st.empty()

    # def on_llm_end(self, *args, **kwargs):
    #     save_message(self.message, "ai")

    # def on_llm_new_token(self, token, *args, **kwargs):
    #     self.message += token
    #     self.message_box.markdown(self.message)
    def __init__(self):
        self.message = ""
        self.message_box = None

    def on_llm_start(self, *args, **kwargs):
        self.message_box = st.empty()
        self.message = ""

    def on_llm_new_token(self, token, *args, **kwargs):
        self.message += token
        self.message_box.markdown(self.message)

    def on_llm_end(self, *args, **kwargs):
        save_message(self.message, "ai")
        self.message_box = None  # Clear the reference once done


llm = RemoteRunnable(LANGSERVE_ENDPOINT)

def save_message(message, role):
    st.session_state["messages"].append({"message": message, "role": role})

def send_message(message, role, save=True):
    with st.chat_message(role):
        st.markdown(message)
    if save:
        save_message(message, role)

def paint_history():
    for message in st.session_state["messages"]:
        send_message(
            message["message"],
            message["role"],
            save=False,
        )

st.title("쿠스AI")

st.markdown(
    """
Welcome!
            
Use this chatbot to ask questions to an AI!

"""
)

send_message("I'm ready! Ask away!", "ai", save=False)
if "messages" not in st.session_state:
    st.session_state["messages"] = []
paint_history()
message = st.chat_input("Ask anything...")
if message:
    send_message(message, "human")
    with st.chat_message("ai"):
        llm.invoke(message, callback_handler=ChatCallbackHandler())

else:
    st.session_state["messages"] = []