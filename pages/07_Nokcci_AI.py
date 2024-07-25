import streamlit as st

st.set_page_config(
    page_title="NokcciAI",
    page_icon="💼",
    layout="wide"
)

st.markdown(
    """
    # NokcciAI
            
    ###Extract any speech from audio files.
            
    Upload your audio files then it will transcribe them for you.
"""
)

# Embed the website in the main screen
st.markdown(
    """
    <iframe src="https://www.nokcci.com/" width="100%" height="1000px" style="border:none;"></iframe>
    """,
    unsafe_allow_html=True
)
