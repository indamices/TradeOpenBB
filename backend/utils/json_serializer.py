"""
Utility functions for JSON serialization with NaN/Infinity handling
"""
import math
import numpy as np
from typing import Any, Union, Dict, List


def sanitize_float(val: Any) -> Any:
    """
    Sanitize float values to be JSON-compliant.
    Replaces NaN, Infinity, and -Infinity with None.
    """
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    return val


def sanitize_for_json(data: Any) -> Any:
    """
    Recursively sanitize data structure for JSON serialization.
    Handles dicts, lists, and nested structures.
    """
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, (float, np.floating)):
        return sanitize_float(data)
    elif hasattr(data, '__dict__'):
        # Handle objects with __dict__ (like Pydantic models)
        return sanitize_for_json(data.__dict__)
    else:
        return data
