import logging
import json
from coc_elt.logging_config import JsonFormatter

def test_json_formatter_standard():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_json",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=10,
        msg="Hello World",
        args=None,
        exc_info=None
    )
    result = formatter.format(record)
    data = json.loads(result)
    
    assert data["severity"] == "INFO"
    assert data["message"] == "Hello World"
    assert "timestamp" in data
    assert data["logger"] == "test_json"

def test_json_formatter_extra_args():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_json_extra",
        level=logging.WARNING,
        pathname="test_file.py",
        lineno=20,
        msg="Warning message",
        args=None,
        exc_info=None
    )
    # Inject extra attributes
    record.__dict__["custom_field"] = "custom_value"
    record.__dict__["another_field"] = 123
    
    result = formatter.format(record)
    data = json.loads(result)
    
    assert data["severity"] == "WARNING"
    assert "extra_args" in data
    assert data["extra_args"]["custom_field"] == "custom_value"
    assert data["extra_args"]["another_field"] == 123
