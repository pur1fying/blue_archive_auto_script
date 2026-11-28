"""Keep NumPy-derived test measurements numeric in JSON evidence."""
import sys


def json_default(value):
    numpy = sys.modules.get('numpy')
    if numpy is not None:
        if isinstance(value, numpy.generic):
            return value.item()
        if isinstance(value, numpy.ndarray):
            return value.tolist()
    raise TypeError(f'Object of type {type(value).__name__} is not JSON serializable')
