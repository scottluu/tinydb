import json
import pytest
from unittest import mock
from tinydb import TinyDB
from tinydb.storages import JSONStorage

try:
    import orjson
except ImportError:
    orjson = None

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / 'test.json')

def test_orjson_loads(db_path):
    if orjson is None:
        pytest.skip('orjson not installed')

    data = {'_default': {'1': {'foo': 'bar'}}}
    with open(db_path, 'w') as f:
        json.dump(data, f)

    # Verify orjson.loads is called via the tinydb.storages.orjson reference
    with mock.patch('tinydb.storages.orjson.loads', side_effect=orjson.loads) as mock_loads:
        storage = JSONStorage(db_path)
        assert storage.read() == data
        mock_loads.assert_called()
        storage.close()

def test_orjson_dumps(db_path):
    if orjson is None:
        pytest.skip('orjson not installed')

    data = {'_default': {'1': {'foo': 'bar'}}}
    
    # Verify orjson.dumps is called via the tinydb.storages.orjson reference
    with mock.patch('tinydb.storages.orjson.dumps', side_effect=orjson.dumps) as mock_dumps:
        storage = JSONStorage(db_path)
        storage.write(data)
        mock_dumps.assert_called()
        storage.close()

    with open(db_path, 'r') as f:
        assert json.load(f) == data

def test_orjson_fallback_on_error(db_path):
    if orjson is None:
        pytest.skip('orjson not installed')

    data = {'_default': {'1': {'foo': 'bar'}}}
    
    # orjson.dumps doesn't support 'indent' keyword argument
    storage = JSONStorage(db_path, indent=4)
    
    # We want to verify it falls back to json.dumps
    # Note: we patch tinydb.storages.json.dumps because that's what's called in the fallback
    with mock.patch('tinydb.storages.json.dumps', side_effect=json.dumps) as mock_json_dumps:
        storage.write(data)
        mock_json_dumps.assert_called()
    
    # Verify the output is indeed indented (proving json.dumps was used)
    with open(db_path, 'r') as f:
        content = f.read()
        assert '\n    ' in content
        
    storage.close()

def test_orjson_read_fallback(db_path):
    if orjson is None:
        pytest.skip('orjson not installed')

    data = {'_default': {'1': {'foo': 'bar'}}}
    with open(db_path, 'w') as f:
        json.dump(data, f)

    storage = JSONStorage(db_path)
    
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
        storage = JSONStorage(db_path)
        
        with mock.patch('tinydb.storages.json.dumps', side_effect=json.dumps) as mock_json_dumps:
            storage.write(data)
            mock_json_dumps.assert_called()
            
        with mock.patch('tinydb.storages.json.load', side_effect=json.load) as mock_json_load:
            assert storage.read() == data
            mock_json_load.assert_called()
        
        storage.close()

def test_orjson_with_tinydb(db_path):
    if orjson is None:
        pytest.skip('orjson not installed')

    # Test integration with the main TinyDB class
    db = TinyDB(db_path)
    db.insert({'foo': 'bar'})
    
    # Verify it was written using orjson (by checking if we can read it back)
    assert db.all() == [{'foo': 'bar'}]
    
    db.close()
