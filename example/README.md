# FilesConnection Example

A simple example app for using FilesConnection.

## Setup

### Install dependencies

Create a python environment using your favorite environment manager, like virtualenv.

```sh
pip install -r requirements.txt
```

### Set up a bucket(s) and credentials

The local files connection works out of the box. The S3 and GCS connections require your own bucket
and some kind of secrets or credential setup. You can run the app and follow the instructions
to get it working.

### Run the app

```sh
streamlit run streamlit_app.py
```

That's it!
