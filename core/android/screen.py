"""
This module provides functionality to extract virtual display information.

There are two kinds of display IDs on Android:

1. Logical Display ID, which is:
    * self incrementing from 0
    * used by high-level APIs like ActivityManager
2. Stable Display ID, which is:
    * calculated based on hardware properties
    * used by low-level APIs

.. NOTE:
    On Android 10 and above, screencap accepts stable display IDs. 
    On Android versions below 10, screencap accepts logical display IDs.
"""

import re
from typing import NamedTuple

class DisplayInfo(NamedTuple):
    logical_id: str
    stable_id: str

def extract_virtual_displays(dump_content: str):
    """
    Extract virtual display information from the given dumpsys SurfaceFlinger log content.
    """
    # Target：Display 11529... (virtual, "<name>") ... layerStack=25
    pattern = re.compile(
        r'^Display\s+(\d+)\s+\(virtual,\s+"([^"]+)"\)'
        r'(?:.|\n)*?'
        r'layerStack=(\d+)',
        re.MULTILINE
    )

    for match in pattern.finditer(dump_content):
        sf_id = match.group(1)
        # name = match.group(2)
        layer_stack = match.group(3)
        return DisplayInfo(logical_id=layer_stack, stable_id=sf_id)

    return None