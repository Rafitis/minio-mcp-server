#!/usr/bin/env python3
import json
import sys

import requests

URL = "https://jsonplaceholder.typicode.com/posts/1"

try:
    resp = requests.get(URL, timeout=5)
    resp.raise_for_status()
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
except Exception as e:
    print("Error:", e, file=sys.stderr)
    sys.exit(1)
