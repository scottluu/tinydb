import json
from pathlib import Path

import orjson
import pytest
from unittest import mock
from tinydb import TinyDB
from tinydb.storages import JSONStorage

@pytest.fixture
def db_path(tmp_path) -> Path:
    return tmp_path / 'test.json'

def test_orjson_fallback_on_error(db_path):
    data = {'_default': {'1': {'foo': 'bar'}}}
    
    # orjson.dumps doesn't support 'indent' keyword argument
    storage = JSONStorage(str(db_path), indent=4)
    
    # We want to verify it falls back to json.dumps
    # Note: we patch tinydb.storages.json.dumps because that's what's called in the fallback
    with mock.patch('tinydb.storages.json.dumps', side_effect=json.dumps) as mock_json_dumps:
        storage.write(data)
        mock_json_dumps.assert_called()
    
    # Verify the output is indeed indented (proving json.dumps was used)
    content = db_path.read_text()
    assert '\n    ' in content
        
    storage.close()

def test_orjson_read_fallback(db_path):
    data = {'_default': {'1': {'foo': 'bar'}}}
    db_path.write_bytes(orjson.dumps(data))

    storage = JSONStorage(str(db_path))
    
    # Force orjson.loads to fail
    with mock.patch('tinydb.storages.orjson.loads', side_effect=ValueError("Custom error")):
        with mock.patch('tinydb.storages.json.load', side_effect=json.load) as mock_json_load:
            assert storage.read() == data
            mock_json_load.assert_called()
            
    storage.close()

def test_orjson_not_installed(db_path):
    # Simulate orjson not being installed by mocking the module-level 'orjson' variable in tinydb.storages
    with mock.patch('tinydb.storages.orjson', None):
        data = {'_default': {'1': {'foo': 'bar'}}}
        storage = JSONStorage(str(db_path))
        
        with mock.patch('tinydb.storages.json.dumps', side_effect=json.dumps) as mock_json_dumps:
            storage.write(data)
            mock_json_dumps.assert_called()
            
        with mock.patch('tinydb.storages.json.load', side_effect=json.load) as mock_json_load:
            assert storage.read() == data
            mock_json_load.assert_called()
        
        storage.close()

def test_orjson_with_tinydb(db_path):
    # Test integration with the main TinyDB class
    db = TinyDB(str(db_path))
    db.insert({'foo': 'bar'})
    
    # Verify it was written using orjson (by checking if we can read it back)
    assert db.all() == [{'foo': 'bar'}]
    
    db.close()
