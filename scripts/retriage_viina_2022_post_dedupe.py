#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

WORD = r"A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9_"

def bounded(terms: list[str]) -> re.Pattern[str]:
    body = "|".join(terms)
    return re.compile(rf"(?<![{WORD}])(?:{body})(?![{WORD}])", re.I | re.U)

# Deliberately word/phrase bounded. This prevents e.g. 'твер' matching 'утверждается'.
RUSSIA_EXPLICIT = bounded([
    r"in russia", r"inside russia", r"within russia", r"russian federation", r"on russian territory",
   