#!/usr/bin/env python3
"""Print the full kitcheck report for one kit: verdict line, an
errors/warnings x mechanical/partial/manual breakdown, and a findings
table. Replaces kitcheck_verdict.py (a per-kit row for a multi-kit
aggregate table) and kitcheck_findings_detail.py (tiered collapsible
bullets) -- consolidated into one direct report now that kitcheck
targets one kit per PR, not several, so there's no separate
"aggregate across kits" step to build a row for, and no assumed need to
hide findings behind a <details> toggle.

Usage: kitcheck_render_report.py <kit-name> <result.json>
"""
import json
import sys

from kitcheck_fixer_tiers import classify, severity_tier_counts

kit_name = sys.argv[1]
result_path = sys.argv[2]

with open(result_path, encoding="utf-8") as f:
    result = json.load(f)

kit = result["kit"]
s = result["summary"]
mark = "✅ PASSES" if s["passes"] else "❌ NEEDS ATTENTION"

print(f"## kitcheck: {kit.get('name') or kit_name} — {mark}")
print()
print(f"`{kit.get('id')}` · {s['errors']} error(s) · {s['warnings']} warning(s)")
print()

if not result["findings"]:
    print("No findings.")
    sys.exit(0)

counts = severity_tier_counts(result["findings"])
print("| | Total | 🔧 Mechanical | 🟡 Partial | 🔴 Manual |")
print("|---|---|---|---|---|")
print(f"| Errors | {s['errors']} | {counts['error']['mechanical']} | "
      f"{counts['error']['partial']} | {counts['error']['manual']} |")
print(f"| Warnings | {s['warnings']} | {counts['warning']['mechanical']} | "
      f"{counts['warning']['partial']} | {counts['warning']['manual']} |")
print()

_TIER_ICON = {"mechanical": "🔧", "partial": "🟡", "manual": "🔴"}
_TIER_ORDER = {"mechanical": 0, "partial": 1, "manual": 2}
_SEVERITY_ORDER = {"error": 0, "warning": 1}


def _sort_key(f):
    tier, _ = classify(f)
    return (_SEVERITY_ORDER[f["severity"]], _TIER_ORDER[tier], f["check"])


print("| Severity | Content | Message | Check | Fixer |")
print("|---|---|---|---|---|")
for f in sorted(result["findings"], key=_sort_key):
    tier, fixer = classify(f)
    sev = "**ERROR**" if f["severity"] == "error" else "warn"
    fixer_cell = f"{_TIER_ICON[tier]} `{fixer}`" if fixer else f"{_TIER_ICON[tier]} manual"
    print(f"| {sev} | `{f['content']}` | {f['message']} | `{f['check']}` | {fixer_cell} |")
