# Streamlit FilesConnection

Connect to cloud (or local) file storage from your Streamlit app. Powered by `st.experimental_connection()` and [fsspec](https://filesystem-spec.readthedocs.io/en/latest/). Works with Streamlit >= 1.22.

Any fsspec compatible protocol should work, it just needs to be installed. Read more about Streamlit Connections in the
[official docs](https://docs.streamlit.io/library/api-reference/connections).

## Quickstart

See the example directory for a fuller example using S3 and/or GCS.

```sh
pip install streamlit
pip install git+https://github.com/streamlit/files-connection
```

**Note:** Install from pypi coming soon

```python
import streamlit as st
from st_files_connection import FilesConnection

"# Minimal FilesConnection example"
with st.echo():
    conn = st.experimental_connection('my_connection', type=FilesConnection)

# Write a file to local directory if it doesn't exist
test_file = "test.txt"
try:
    _ = conn.read(test_file, input_format='text')
except FileNotFoundError:
    with conn.open(test_file, "wt") as f:
        f.write("Hello, world!")

with st.echo():
    # Read back the contents of the file
    st.write(conn.read(test_file, input_format='text'))
```

## Using for cloud file storage

You can pass the protocol name into `st.experimental_connection()` as the first argument, for any known fsspec protocol:

```python
# Create an S3 connection
conn = st.experimental_connection('s3', type=FilesConnection)

# Create a GCS connection
conn = st.experimental_connection('gcs', type=FilesConnection)

# Create a Weights & Biases connection
conn = st.experimental_connection('wandb', type=FilesConnection)
```

For cloud file storage tools (or anything that needs config / credentials) you can specify it in two ways:

- Using the native configuration / credential approach of the underlying library (e.g. config file or environment variables)
- Using [Streamlit secrets](https://docs.streamlit.io/library/advanced-features/secrets-management).

For Streamlit secrets, create a section called `[connections.<name>]` in your `.streamlit/secrets.toml` file, and add parameters
there. You can pass in anything you would pass to an fsspec file system constructor. Additionally:

- For GCS, the contents of secrets are assumed to be the keys to a token file (e.g. it is passed as a `{"token":{<secrets>}}` dict)

## Main methods

### read()

`conn.read("path/to/file", input_format="text|csv|parquet|json|jsonl" or None, ttl=None) -> pd.DataFrame`

Specify a path to file and input format. Optionally specify a TTL for caching.

Valid values for `input_format=`:

- `text` returns a string
- `json` returns a dict or list (depending on the JSON object) - only one object per file is supported
- `csv`, `parquet`, `jsonl` return a pandas DataFrame
- `None` will attempt to infer the input format from file extension of `path`
- Anything else (or unrecognized inferred type) raises a `ValueError`

```python
conn = st.experimental_connection("s3", type=FilesConnection)
df = conn.read(f"my-s3-bucket/path/to/file.parquet", input_format='parquet')
st.dataframe(df)
```

**Note:** We want to add a `format=` argument to specify output format with more options, contributions welcome!

### open()

`conn.open("path/to/file", mode="rb", *args, **kwargs) -> Iterator[TextIOWrapper | AbstractBufferedFile]`

Works just like fsspec [AbstractFileSystem.open()](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem.open).

### fs

Use `conn.fs` to access the [underlying FileSystem object API](https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.spec.AbstractFileSystem).

## Contributing

Contributions to this repo are welcome. We are still figuring it out and expect it may get some usage over time. We want to keep the API pretty simple
and not increase the maintenance surface area too much. If you are interested in helping to maintain it, reach out to us. Thanks for your patience if
it takes a few days to respond.

The best way to submit ideas you might want to work on is to open an issue and tag `@sfc-gh-jcarroll` and/or any other listed contributors.
Please don't spend a bunch of time working on a PR without checking with us first, since it risks the work being wasted and leaving you frustrated.

Also note, the Streamlit `experimental_connection()` interface is open for 3rd party packages and we look forward to promoting high quality ones in
the ecosystem. If you have an idea that differs from our direction here, we would love for you to fork / clone, build it, and share it with us and
the wider community. Thank you!
