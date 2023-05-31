# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from datetime import timedelta
from io import TextIOWrapper
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union, overload
from typing_extensions import Literal

import pandas as pd

from streamlit.connections import ExperimentalBaseConnection
from streamlit.runtime.caching import cache_data

if TYPE_CHECKING:
    from fsspec import AbstractFileSystem, filesystem
    from fsspec.spec import AbstractBufferedFile


class FilesConnection(ExperimentalBaseConnection["AbstractFileSystem"]):
    """Connects a streamlit app to arbitrary file storage

    FilesConnection uses fsspec to set up connections to cloud, remote, local and
    other file stores such as S3, GCS, HDFS, sftp, and many more.
    """

    def __init__(
        self, connection_name: str = "default", protocol: str | None = None, **kwargs
    ) -> None:
        self.protocol = protocol
        super().__init__(connection_name, **kwargs)

    def _connect(self, **kwargs) -> "AbstractFileSystem":
        """
        Pass a protocol such as "s3", "gcs", or "file"
        """
        from fsspec import AbstractFileSystem, filesystem, available_protocols
        from fsspec.spec import AbstractBufferedFile

        secrets = self._secrets.to_dict()
        protocol = secrets.pop("protocol", self.protocol)
        if 'protocol' in kwargs:
            protocol = kwargs.pop('protocol')

        if protocol is None:
            # Check if name maps to a protocol known by fsspec
            # (allows developers to use name == protocol for shorthand)
            if self._connection_name in available_protocols():
                protocol = self._connection_name
            else:
                protocol = "file"

        if protocol == "gcs" and secrets:
            secrets = {"token": secrets}

        if self.protocol is None:
            self.protocol = protocol
        
        secrets.update(kwargs)

        fs = filesystem(protocol, **secrets)

        return fs
    
    @property
    def fs(self) -> "AbstractFileSystem":
        """Access the underlying AbstractFileSystem for full API operations."""
        return self._instance

    def open(
        self, path: str | Path, mode: str = "rb", *args, **kwargs
    ) -> Iterator[TextIOWrapper | AbstractBufferedFile]:
        """Open the specified path as a file-like object."""
        # Connection name is only passed to make sure that the cache is
        # connection-specific
        if "connection_name" in kwargs:
            kwargs.pop("connection_name")

        return self.fs.open(path, mode, *args, **kwargs)

    @overload
    def read(
        self,
        path: str | Path,
        input_format: Literal["text"],
        ttl: Optional[Union[float, int, timedelta]] = None,
        **kwargs,
    ) -> str:
        pass

    @overload
    def read(
        self,
        path: str | Path,
        input_format: Literal["json"],
        ttl: Optional[Union[float, int, timedelta]] = None,
        **kwargs,
    ) -> Any:
        pass

    @overload
    def read(
        self,
        path: str | Path,
        input_format: Literal["csv", "parquet", "jsonl"],
        ttl: Optional[Union[float, int, timedelta]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        pass

    def read(
        self,
        path: str | Path,
        input_format: str = None,
        ttl: Optional[Union[float, int, timedelta]] = None,
        **kwargs,
    ):
        """Read the file at the specified path, cache the result and return as a pandas DataFrame.

        input_format may be specified - valid values are `text`, `csv`, `parquet`, `json`, `jsonl`.
        If not specified, input_format will be inferred optimistically from path file extension.
        Result is cached indefinitely by default, set `ttl = 0` to disable caching.
        """
        @cache_data(ttl=ttl, show_spinner="Running `files.read(...)`.")
        def _read_text(path: str | Path, **kwargs) -> str:
            if "connection_name" in kwargs:
                kwargs.pop("connection_name")

            with self.open(path, "rt", **kwargs) as f:
                return f.read()

        @cache_data(ttl=ttl, show_spinner="Running `files.read(...)`.")
        def _read_csv(path: str | Path, **kwargs) -> pd.DataFrame:
            if "connection_name" in kwargs:
                kwargs.pop("connection_name")

            with self.open(path, "rt") as f:
                return pd.read_csv(f, **kwargs)

        @cache_data(ttl=ttl, show_spinner="Running `files.read(...)`.")
        def _read_parquet(path: str | Path, **kwargs) -> pd.DataFrame:
            # TODO: for general read() user may commonly pass `nrows` which isn't supported by read_parquet
            # Can we add something like this as a workaround? https://stackoverflow.com/a/69888274/20530083
            if "connection_name" in kwargs:
                kwargs.pop("connection_name")

            with self.open(path, "rb") as f:
                return pd.read_parquet(f, **kwargs)

        @cache_data(ttl=ttl, show_spinner="Running `files.read(...)`.")
        def _read_json(path: str | Path, **kwargs) -> Any:
            if "connection_name" in kwargs:
                kwargs.pop("connection_name")

            with self.open(path, "rt") as f:
                return json.load(f, **kwargs)

        @cache_data(ttl=ttl, show_spinner="Running `files.read(...)`.")
        def _read_jsonl(path: str | Path, **kwargs) -> pd.DataFrame:
            if "connection_name" in kwargs:
                kwargs.pop("connection_name")

            kwargs['lines'] = True
            with self.open(path, "rt") as f:
                return pd.read_json(f, **kwargs)

        # Try to infer input_format from file extension if missing
        if input_format is None:
            # You can construct a Path from a Path so this should work regardless
            input_format = Path(path).suffix.replace('.', '', 1)
            if input_format == 'txt':
                input_format = 'text'

        if input_format == 'text':
            return _read_text(path, connection_name=self._connection_name, **kwargs)
        elif input_format == 'csv':
            return _read_csv(path, connection_name=self._connection_name, **kwargs)
        elif input_format == 'parquet':
            return _read_parquet(path, connection_name=self._connection_name, **kwargs)
        elif input_format == 'json':
            return _read_json(path, connection_name=self._connection_name, **kwargs)
        elif input_format == 'jsonl':
            return _read_jsonl(path, connection_name=self._connection_name, **kwargs)
        raise ValueError(f"{input_format} is not a valid value for `input_format=`.")

    def _repr_html_(self) -> str:
        """Return a human-friendly markdown string describing this connection.
        This is the string that will be written to the app if a user calls
        ``st.write(this_connection)``. Subclasses of ExperimentalBaseConnection can freely
        overwrite this method if desired.
        Returns
        -------
        str
        """
        module_name = getattr(self, "__module__", None)
        class_name = type(self).__name__

        cfg = (
            f"- Configured from `[connections.{self._connection_name}]`"
            if len(self._secrets)
            else ""
        )

        return f"""
---
**st.connection {self._connection_name} built from `{module_name}.{class_name}`**
{cfg}
- Protocol: `{self.protocol}`
- Learn more using `st.help()`
---
"""