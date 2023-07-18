import streamlit as st
from pathlib import Path

@st.cache_data(ttl=3600)
def get_files(_conn, dataset):
    relevant_exts = ('**.csv', '**.jsonl', '**.parquet', '**.json')
    relevant_files = []
    for ext in relevant_exts:
        relevant_files.extend(_conn.fs.glob(str(Path(dataset, ext))))
    return [f.replace(str(dataset) + '/', '') for f in relevant_files]
