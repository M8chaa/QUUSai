import streamlit as st

st.set_page_config(
    page_title="NokcciAI",
    page_icon="💼",
    layout="wide"
)

# Add custom CSS to adjust spacing and iframe size
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 0rem;
        padding-left: 0rem;
        padding-right: 0rem;
        padding-bottom: 0rem;
    }
    .full-height-iframe {
        height: calc(100vh - 4rem); /* Adjust height to fit viewport minus header */
        width: 100%;
        border: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    # NokcciAI

    ### Extract any speech from audio files.
    
    Upload your audio files then it will transcribe them for you.
    """,
    unsafe_allow_html=True
)

# Embed the website in the main screen
st.markdown(
    """
    <iframe src="https://www.nokcci.com/" class="full-height-iframe"></iframe>
    """,
    unsafe_allow_html=True
)
