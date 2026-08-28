"""Classify a kitcheck finding by kit-utilities fixer coverage.

Vendored snapshot of `kit-utilities`' `bin/list-fixers` output, synced
2026-08-25, spot-checked current as of 2026-08-27 -- not a live query.
`kit-utilities` is a local, unhosted lab tool, not reachable from
`gravwell/kits`' CI runner, so this has to be a periodically-refreshed
copy rather than computed at run time. Re-sync by re-running
`bin/list-fixers` in kit-utilities and updating FIXER_TIERS below
whenever fixer coverage changes there.

A stale copy here fails safe only for *coverage existence* -- a finding
just falls through to "manual" (no fixer known), never a false claim
that a fixer exists at all. It does NOT guarantee *resolution*:
"partial" means a fixer exists that sometimes resolves this check's
findings, not that any specific finding will. Confirmed real,
2026-08-27: `check_detection_labels` -> `bin/attcklabels` resolved 0 of
58 findings on one real kit, because every referenced searchlibrary
query already lacked its own ATT&CK label to mirror -- every one of
those 58 was still correctly tagged "partial," just none of them
actually resolved.

Fixed 2026-08-27 (tracked in kit-management's DECISIONS.md): the old
single `("check_content_labels", None)` entry applied uniformly across
`dashboard`/`pivot`/`macro`/`template`, but `labelsuggest` only covers
`dashboard`/`pivot` -- `macro`/`template` findings were tagged "partial"
with zero real coverage. `check_content_labels` now emits a
directory-specific `section` (kitcheck.py's own change), so this file
can key `dashboard`/`pivot` as "partial" and let `macro`/`template`
fall through to "manual" via the default, same split
`check_naming_consistency` already had.

Deliberately does NOT try to annotate *which* manual findings are known
non-issues (e.g. a kit's intentional Duration tuning) -- that's a
developer judgment call informed by their own context, not something
this tool asserts. "Manual" means "no fixer exists," not "definitely
needs fixing."

Renamed from `check_resource_labels` (2026-08-27, same pass as the
directory split above): "Resource" is a distinct Gravwell object type,
not a generic term for everything a kit contains -- this check was
never about literal Resources at all, just dashboard/pivot/macro/
template `Labels`. `kit-utilities`' `labels.py`/`cli_labelsuggest.py`
renamed in lockstep, since both key on this exact string.
"""

# Keyed on (check, section). A section of None matches any section for
# that check -- used by every check except check_naming_consistency and
# check_content_labels, which each emit more than one genuinely
# different finding type under one check id (see kitcheck.py's own
# finding() docstring, and check_content_labels' own comment) and need
# the section to tell them apart, since fixer coverage differs within
# the same check.
FIXER_TIERS = {
    ("check_macros_no_leading_pipe", None): ("mechanical", "bin/macrofix"),
    ("check_playbooks", None): ("mechanical", "bin/playbookgen --readme"),
    ("check_hashes_zeroed", None): ("mechanical", "bin/zerohash"),
    ("check_naming_consistency", "naming hygiene"): ("mechanical", "bin/namingfix --fix-whitespace"),
    ("check_detection_labels", None): ("partial", "bin/attcklabels"),
    ("check_content_labels", "Standards §7 (dashboard)"): ("partial", "bin/labelsuggest"),
    ("check_content_labels", "Standards §7 (pivot)"): ("partial", "bin/labelsuggest"),
    ("check_naming_consistency", "Standards §6"): ("partial", "bin/namingfix --fix-naming-prefix"),
    ("check_images", None): ("partial", "bin/artlink"),
}


def classify(finding):
    """Return (tier, fixer) for a single finding dict. tier is one of
    "mechanical", "partial", "manual". fixer is the bin/<tool> command,
    or None for "manual"."""
    key = (finding["check"], finding["section"])
    if key in FIXER_TIERS:
        return FIXER_TIERS[key]
    key = (finding["check"], None)
    if key in FIXER_TIERS:
        return FIXER_TIERS[key]
    return ("manual", None)


def severity_tier_counts(findings):
    """Return {"error": {"mechanical": n, "partial": n, "manual": n},
    "warning": {...}} for a list of finding dicts -- errors and warnings
    cross-tabbed against fixer tier separately, since "3 mechanical"
    means something different depending on whether those are errors or
    warnings."""
    counts = {
        "error": {"mechanical": 0, "partial": 0, "manual": 0},
        "warning": {"mechanical": 0, "partial": 0, "manual": 0},
    }
    for f in findings:
        tier, _ = classify(f)
        counts[f["severity"]][tier] += 1
    return counts
