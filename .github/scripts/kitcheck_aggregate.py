#!/usr/bin/env python3
"""Print "pass" if every given kitcheck.py JSON result has
summary.passes == true (zero errors AND zero warnings), else
"needs-attention". Used by kitcheck-report.yml to decide which PR label
to apply — split out for the same reason as kitcheck_render_report.py:
avoid embedding multi-line Python inside a bash command inside a YAML
block scalar.

Usage: kitcheck_aggregate.py <result.json> [<result.json> ...]
"""
import json
import sys

results = sys.argv[1:]
if not results:
    print("needs-attention")
    sys.exit(0)

all_pass = True
for path in results:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not data["summary"]["passes"]:
            all_pass = False
    except Exception:
        all_pass = False  # couldn't evaluate one of them — don't claim pass

print("pass" if all_pass else "needs-attention")
