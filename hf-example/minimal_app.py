import streamlit as st
from st_files_connection import FilesConnection

conn = st.experimental_connection('hf', type=FilesConnection)
df = conn.read('datasets/EleutherAI/lambada_openai/data/lambada_test_en.jsonl', nrows=50, ttl=3600)
st.dataframe(df, use_container_width=True)
