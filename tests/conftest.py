import pytest
import tempfile
import shutil

import pathlib

@pytest.fixture
def tmp_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree