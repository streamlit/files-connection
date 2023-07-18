from json import JSONDecodeError
import streamlit as st
from st_files_connection import FilesConnection
from pathlib import Path
from utils import get_files

st.set_page_config(
    page_title='HuggingFace Dataset Explorer',
    page_icon='🤗'
)

"# 🤗 HuggingFace Dataset Explorer"

"""
This app is a quick prototype of using st.experimental_connection
with HfFileSystem to access HF DataSet data from Streamlit.

View the full app code [here](https://github.com/streamlit/files-connection/tree/main/hf-example).
There's probably some cool stuff to do with
[data editor](https://data-editor.streamlit.app/) here too!
"""

conn = st.experimental_connection('hf', type=FilesConnection)

with st.expander('Find dataset examples'):
    if 'dataset' not in st.session_state:
        st.session_state.dataset = "EleutherAI/lambada_openai"

    def set_dataset():
        st.session_state.dataset = st.session_state._dataset
    
    dataset_examples = [
        "EleutherAI/lambada_openai",
        "argilla/news-summary",
        "stanfordnlp/SHP",
        "HuggingFaceM4/tmp-pmd-synthetic-testing",
        "google/MusicCaps"
    ]
    st.selectbox("Examples", dataset_examples, key="_dataset", on_change=set_dataset)

    """
    You can also search for datasets on [HuggingFace Hub](https://huggingface.co/datasets).
    This repo supports datasets with data stored in json, jsonl, csv or parquet format.
    """

# Enter a dataset and retrieve a list of data files
dataset_name = st.text_input("Enter your dataset of interest", key='dataset')
dataset = Path('datasets', dataset_name)
file_names = get_files(conn, dataset)
if not file_names:
    st.warning("No compatible data files found. This app only supports datasets stored in csv, json[l] or parquet format.")
    st.stop()

# Select a data file and row count to retrieve
file_selection = st.selectbox("Pick a data file", file_names)
datafile = Path(dataset, file_selection)
nrows = st.slider("Rows to retrieve", value=50)

"## Dataset Preview"
kwargs = dict(nrows=nrows, ttl=3600)

# parquet doesn't neatly support nrows
# could be fixed with something like this:
# https://stackoverflow.com/a/69888274/20530083
if datafile.suffix in ('.parquet', '.json'):
    del(kwargs['nrows'])

try:
    df = conn.read(datafile, **kwargs)
except JSONDecodeError as e:
    # often times because a .json file is really .jsonl
    try:
        df = conn.read(datafile, input_format='jsonl', nrows=nrows, **kwargs)
    except:
        raise e

st.dataframe(df.head(nrows), use_container_width=True)
