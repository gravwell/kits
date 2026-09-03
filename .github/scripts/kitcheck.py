#!/usr/bin/env python3
"""
kitcheck.py - lightweight, read-only structural validator for Gravwell kits.

Deliberately narrow scope: structural/mechanical checks only, traced to
specific sections of the canonical kit standards docs (Kit Standards,
Peer Review Process, Kit Build Process — maintained in Google Docs, ask
a team lead for current links) and grounded against real kits before
being written. Nothing here executes a query, installs a kit, or judges detection
quality — that's the separate, deeper "kit audit" skill's job. This is
the "does it pass the basic structural bar" pass, meant to run on every
PR without slowing anyone down.

Design principles (each one exists because of a bug found in a prior
tool used for this purpose):
  - Never writes to the kit directory. Read-only, full stop. No "helpful"
    auto-creation of missing files.
  - --input must point directly at the kit root. No parent-directory
    auto-discovery walk — that class of fallback previously produced a
    silent, empty, exit-0 "all clean" report when pointed at the wrong
    directory. Here, failing to find a MANIFEST is a loud, non-zero exit.
  - JSON output is the primary output, always produced the same way
    regardless of which display flags are passed — no display mode can
    silently suppress it.
  - This is a component, not a gate: findings never affect the exit
    code. Only a genuine "couldn't evaluate this input" condition does.
"""

import argparse
import inspect
import json
import os
import re
import string
import sys
from pathlib import Path

KIT_ID_RE = re.compile(r"^io\.gravwell\.([A-Za-z0-9._-]+)$")
ZERO_HASH_RE = re.compile(r"^0+$")
EXPECTED_MAX_VERSION = {"Major": 5, "Minor": 99, "Point": 99}
EXPECTED_SCHEDULED_DURATION = -3600  # -1h, per Standards §21

# Standards § citation building blocks, named so a doc renumbering is a
# one-line edit here instead of a multi-site find/replace through every
# finding() call site. SEC holds bare section refs (not the "Standards "
# prefix) specifically so multi-section citations compose correctly —
# e.g. f"{STANDARDS} {SEC['7']} / {SEC['22']}" reads "Standards §7 / §22",
# not "Standards §7 / Standards §22". Composed per call site rather than
# one constant per combined string, since call sites mix sections +
# secondary-doc citations in different combinations.
STANDARDS = "Standards"
SEC = {
    "5.1": "§5.1",
    "5.2": "§5.2",
    "5.3": "§5.3",
    "6": "§6",
    "7": "§7",
    "8": "§8",
    "9": "§9",
    "10": "§10",
    "12": "§12",
    "14": "§14",
    "16": "§16",
    "21": "§21",
    "22": "§22",
}
PEER_REVIEW = "Peer Review"
PEER_REVIEW_GITHUB = "Peer Review:GitHub"
PEER_REVIEW_PLATFORM = "Peer Review:In-Platform"
BUILD_PROCESS_15A = "Build Process step 15a"


def finding(findings, severity, section, content, message, check=None):
    # "check" is the calling check_* function's name, captured automatically
    # so every call site gets a stable identifier for free — no risk of it
    # drifting out of sync with a hand-maintained slug at ~30 call sites.
    # Lets a downstream fixer-dispatcher (e.g. kit-utilities) match on
    # finding["check"] instead of pattern-matching free-text `message`.
    # One known caveat: check_naming_consistency emits two conceptually
    # distinct findings (whitespace hygiene vs. dominant-prefix mismatch)
    # under this same id — distinguishable via `section` ("naming hygiene"
    # vs "Standards §6") if a consumer ever needs to dispatch them
    # differently.
    #
    # The optional `check` override exists for the one case where a
    # check_* function delegates to a shared helper that calls finding()
    # on its behalf (_check_image_conventions, called by check_images for
    # cover/banner in turn) — without it, auto-capture would grab the
    # helper's own name instead of the conceptual check it's part of. No
    # existing call site needs to change; this only fires when explicitly
    # passed.
    if check is None:
        check = inspect.stack()[1].function
    findings.append(
        {"severity": severity, "section": section, "content": content,
         "message": message, "check": check}
    )


def load_manifest(root: Path):
    manifest_path = root / "MANIFEST"
    if not manifest_path.exists():
        return None, f"No MANIFEST found at {manifest_path}"
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"MANIFEST at {manifest_path} is not valid JSON: {e}"


def load_manifest_file(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as e:
        return None, f"--base-manifest at {path} could not be read as JSON: {e}"


def kitname_from_id(kit_id):
    if not isinstance(kit_id, str):
        return None
    m = KIT_ID_RE.match(kit_id.strip())
    return m.group(1) if m else None


# ---------------------------- MANIFEST checks ----------------------------

def check_manifest_core(manifest, findings):
    kit_id = manifest.get("ID")
    if not kitname_from_id(kit_id):
        finding(findings, "error", f"{STANDARDS} {SEC['5.1']}", "MANIFEST.ID",
                f"expected io.gravwell.<name>, found {kit_id!r}")

    name = manifest.get("Name")
    if not isinstance(name, str) or not name.strip():
        finding(findings, "error", f"{STANDARDS} {SEC['5.1']} / {PEER_REVIEW_GITHUB}", "MANIFEST.Name",
                "Name is missing or empty")

    desc = manifest.get("Desc")
    if not isinstance(desc, str) or not desc.strip():
        finding(findings, "warning", f"{STANDARDS} {SEC['5.1']} / {PEER_REVIEW_GITHUB}", "MANIFEST.Desc",
                "Desc is missing or empty")

    version = manifest.get("Version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        finding(findings, "error", f"{STANDARDS} {SEC['5.1']}", "MANIFEST.Version",
                f"expected a positive integer, found {version!r}")


def check_max_version(manifest, findings):
    mv = manifest.get("MaxVersion")
    if mv != EXPECTED_MAX_VERSION:
        finding(findings, "warning", f"{STANDARDS} {SEC['5.1']}", "MANIFEST.MaxVersion",
                f"expected {EXPECTED_MAX_VERSION} (5.99.99), found {mv!r} — "
                "not universally followed in existing kits, worth a look for new/changed ones")


def check_version_increment(manifest, findings, base_manifest=None, is_new_kit=False):
    # §5.1 "start with 1; iterate" binds two distinct moments: a brand-new
    # kit starts at 1, and an update to an existing kit must move the
    # version. Confirmed via real gravwell/kits mainline history (paloalto,
    # sysmon, juniper): every merge that changes a kit bumps Version by
    # exactly 1; a merge that leaves a kit's content untouched leaves
    # Version untouched too. A same-or-lower Version on a PR that touches
    # an existing kit is therefore a real regression, not a style nit —
    # confirmed via a genuine historical incident (gravwell/kits PR #288,
    # "new_covers") that dropped auditd from Version 2 back to 1 on main.
    # A jump of more than 1 does happen legitimately (okta went 1->3 once)
    # so it's a warning, not an error.
    version = manifest.get("Version")
    if not isinstance(version, int) or isinstance(version, bool):
        return  # malformed Version already flagged by check_manifest_core

    if base_manifest is not None:
        base_version = base_manifest.get("Version")
        if not isinstance(base_version, int) or isinstance(base_version, bool):
            return  # can't compare against a malformed/missing base Version
        if version <= base_version:
            finding(findings, "error", f"{STANDARDS} {SEC['5.1']}", "MANIFEST.Version",
                    f"published version is {base_version}, this PR's version is {version} — "
                    "every kit-content change must iterate the version")
        elif version > base_version + 1:
            finding(findings, "warning", f"{STANDARDS} {SEC['5.1']}", "MANIFEST.Version",
                    f"version jumped from {base_version} to {version} (more than +1) — "
                    "confirm this skip is intentional")
    elif is_new_kit and version != 1:
        finding(findings, "warning", f"{STANDARDS} {SEC['5.1']}", "MANIFEST.Version",
                f"new kits should start at Version 1, found {version}")


def check_hashes_zeroed(manifest, findings):
    items = manifest.get("Items") or []
    for i, item in enumerate(items):
        h = item.get("Hash") if isinstance(item, dict) else None
        if h and not ZERO_HASH_RE.match(h):
            name = item.get("Name", f"Items[{i}]") if isinstance(item, dict) else f"Items[{i}]"
            finding(findings, "error", f"{BUILD_PROCESS_15A} / {PEER_REVIEW_GITHUB}",
                    f"MANIFEST.Items[{i}] ({name})",
                    "Hash is not zeroed — run `kitctl -zero-hash unpack` before committing")


def check_config_macro_tags(manifest, findings):
    for cm in (manifest.get("ConfigMacros") or []):
        if not isinstance(cm, dict):
            continue
        desc = (cm.get("Description") or "")
        if "tag" in desc.lower() and cm.get("Type") != "TAG":
            finding(findings, "error", f"{STANDARDS} {SEC['16']} / {PEER_REVIEW_GITHUB}",
                    f"MANIFEST.ConfigMacros ({cm.get('MacroName')})",
                    f"description mentions a tag but Type is {cm.get('Type')!r}, expected 'TAG'")


# ---------------------------- Filesystem checks ----------------------------

def check_build_assets(root, kitname, findings):
    if not (root / "BUILD").exists():
        finding(findings, "error", f"{STANDARDS} {SEC['16']} / {PEER_REVIEW_GITHUB}", "BUILD",
                "missing at kit root")
    if not (root / "README.md").exists():
        finding(findings, "error", f"{STANDARDS} {SEC['16']} / {SEC['5.3']} / {PEER_REVIEW_GITHUB}", "README.md",
                "missing at kit root")
    # The {kit}.metadata filename tracks the kit's directory/package name, not
    # necessarily MANIFEST.ID's suffix — confirmed via aws_guardduty, whose ID
    # is "io.gravwell.guardduty" but whose metadata file is
    # "aws_guardduty.metadata" (matching the directory, not the ID).
    meta_file = root / f"{root.name}.metadata"
    if not meta_file.exists():
        finding(findings, "error", f"{STANDARDS} {SEC['16']} / {PEER_REVIEW_GITHUB}",
                f"{root.name}.metadata", "missing at kit root")
    if kitname and kitname != root.name:
        finding(findings, "warning", f"{STANDARDS} {SEC['5.1']}", "MANIFEST.ID",
                f"ID suffix ({kitname!r}) differs from the directory name "
                f"({root.name!r}) — not necessarily wrong, but worth a second look")


def _find_image(root, stem):
    for ext in (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"):
        for candidate in (stem, stem.capitalize(), stem.upper(), stem.lower()):
            p = root / f"{candidate}{ext}"
            if p.exists():
                return p
    return None


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"


def _sniff_image_format(path):
    # Sniffs actual bytes, never trusts the .png/.jpg filename -- confirmed
    # necessary against real fleet data (2026-08-25): 27 of 98 sampled real
    # Cover/Banner/Icon file/*.contents entries are actually JPEG despite
    # the filename convention, including juniper's. Returns None if the
    # file can't be read (e.g. a broken symlink) rather than raising --
    # that's its own, separately-reported finding.
    try:
        with path.open("rb") as f:
            head = f.read(8)
    except OSError:
        return None
    if head.startswith(_PNG_MAGIC):
        return "PNG"
    if head.startswith(_JPEG_MAGIC):
        return "JPEG"
    return "unknown"


def _check_image_conventions(path, label, findings):
    # New §16 (2026-08-25 standards revision): cover/banner/icon must be
    # symlinks into file/*.contents, not raw duplicate bytes, so the repo
    # copy and the packed kit can't drift into divergent images. Warning,
    # not error -- brand-new requirement, the existing fleet predates it
    # almost entirely.
    if not path.is_symlink():
        finding(findings, "warning", f"{STANDARDS} {SEC['16']}", f"{label} image",
                f"{path.name} is a raw file, not a symlink into file/*.contents -- "
                "new convention as of the 2026-08-25 standards revision, not required yet",
                check="check_images")
    else:
        target = os.readlink(path)
        if "file/" not in target or not target.endswith(".contents"):
            finding(findings, "warning", f"{STANDARDS} {SEC['16']}", f"{label} image",
                    f"{path.name} is a symlink but doesn't point into file/*.contents "
                    f"(points to {target!r})", check="check_images")

    # New: images should be PNG specifically (size optimization). Warning,
    # not error -- confirmed real, current fleet non-compliance (27 of 98
    # sampled Cover/Banner/Icon entries are JPEG), so this can't be a hard
    # error without breaking a large fraction of existing kits immediately.
    fmt = _sniff_image_format(path)
    if fmt is None:
        finding(findings, "warning", f"{STANDARDS} {SEC['16']}", f"{label} image",
                f"{path.name} couldn't be read to verify its format (broken symlink?)",
                check="check_images")
    elif fmt != "PNG":
        finding(findings, "warning", f"{STANDARDS} {SEC['5.2']}", f"{label} image",
                f"{path.name} is {fmt}, not PNG -- new convention, not required yet",
                check="check_images")


def check_images(root, findings):
    cover = _find_image(root, "cover")
    if not cover:
        finding(findings, "error", f"{STANDARDS} {SEC['5.2']} / {SEC['16']}", "cover image",
                "no cover.{png,jpg} found at kit root — note: must be a plain filename, "
                "not <kitname>-cover.*")
    else:
        _check_image_conventions(cover, "cover", findings)

    banner = _find_image(root, "banner")
    if not banner:
        finding(findings, "error", f"{STANDARDS} {SEC['5.2']} / {SEC['16']}", "banner image",
                "no banner.{png,jpg} found at kit root")
    else:
        _check_image_conventions(banner, "banner", findings)

    # Icon deliberately not checked -- removed rather than left as a
    # never-passing warning (no confirmed real icon-filename convention).


def check_license(root, findings):
    license_dir = root / "license"
    files = [p for p in license_dir.glob("*") if p.is_file()] if license_dir.exists() else []
    if not files:
        finding(findings, "error", f"{STANDARDS} {SEC['14']} / {PEER_REVIEW}", "license/",
                "no license file found")
        return
    text = ""
    for p in files:
        try:
            text += p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
    if "bsd" not in text.lower() or "redistribution and use in source and binary forms" not in text.lower():
        finding(findings, "warning", f"{STANDARDS} {SEC['14']} / {PEER_REVIEW}", "license/",
                "license file present but doesn't clearly contain BSD 2-Clause boilerplate")


def check_macros_no_leading_pipe(root, findings):
    macro_dir = root / "macro"
    if not macro_dir.exists():
        return
    for p in sorted(macro_dir.glob("*.expansion")):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if text.lstrip().startswith("|"):
            finding(findings, "error", f"{STANDARDS} {SEC['9']}", f"macro/{p.name}",
                    "macro expansion starts with a preceding pipe")


def _load_json_safe(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def check_playbooks(root, findings):
    playbook_dir = root / "playbook"
    if not playbook_dir.exists():
        finding(findings, "warning", f"{STANDARDS} {SEC['12']}", "playbook/",
                "no playbook directory found — 2 required (Kit Overview, Copy of Readme)")
        return
    names = []
    for p in sorted(playbook_dir.glob("*.meta")):
        d = _load_json_safe(p)
        if isinstance(d, dict) and d.get("Name"):
            names.append(str(d["Name"]))
        else:
            names.append(p.stem)
    lowered = [n.lower() for n in names]
    if not any("overview" in n for n in lowered):
        finding(findings, "warning", f"{STANDARDS} {SEC['12']}", "playbook/",
                "no playbook name suggests 'Kit Overview' (heuristic match, not exact-name verified)")
    if not any("readme" in n for n in lowered):
        finding(findings, "warning", f"{STANDARDS} {SEC['12']}", "playbook/",
                "no playbook name suggests 'Copy of Readme' (heuristic match, not exact-name verified)")


# Mirrors "a real Gravwell query starts with tag= (optionally wrapped in a
# single leading paren), a $MACRO that expands to one, or a bare
# resource-dump module that needs no tag at all" -- confirmed against
# every real fenced block AND inline span in a 35-kit fleet, not just the
# 6-kit sample. The leading-paren form is real (aws_cloudtrail:
# "(tag=aws-cloudtrail)"). The bare "dump" form is real and was a
# confirmed false-positive class before being added: "dump -r
# fortinet_evs | table"-shaped one-liners (a resource lookup, not a
# tag-scoped search) appear across fortinet/duo/cisco_asa/cisco_ftd and
# don't and shouldn't start with tag=/$MACRO. Not generalized to other
# bare module names beyond this one confirmed, repeated real pattern --
# same "scope from real fleet evidence, don't build ahead of it"
# discipline as the rest of this file.
_QUERY_LIKE_RE = re.compile(r"^\s*\(?\s*(tag\s*=|\$[A-Z_][A-Z0-9_]*|dump\b)")


def _playbook_fenced_blocks(text):
    # Line-based on purpose, not a single regex matching an opening
    # fence's info string against [a-zA-Z]*\n -- that approach desyncs
    # the instant a fence's info string has anything outside [A-Za-z]
    # (confirmed via a real aws_cloudtrail playbook using MyST-style
    # ```{note} admonition blocks: the regex failed to recognize that
    # fence as an opener, then paired every SUBSEQUENT fence as
    # open/close one slot off -- every reported "code block" was
    # actually the prose BETWEEN fences, and the real fenced content,
    # the thing this check exists to look at, was never inspected at
    # all). A fence line's own info-string content doesn't matter for
    # telling code from prose; only whether the line starts with ```.
    lines = text.splitlines()
    in_block = False
    current = []
    for line in lines:
        if line.strip().startswith("```"):
            if in_block:
                yield "\n".join(current)
                current = []
            in_block = not in_block
            continue
        if in_block:
            current.append(line)
    if in_block and current:
        yield "\n".join(current)


def _strip_fenced_blocks(text):
    # Same fence-tracking as _playbook_fenced_blocks, but returns the
    # text with fenced regions (and their ``` marker lines) removed, so
    # an inline-span scan never re-inspects a fenced block's own content
    # as if it were a separate inline span.
    lines = text.splitlines()
    in_block = False
    kept = []
    for line in lines:
        if line.strip().startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            kept.append(line)
    return "\n".join(kept)


def _first_significant_line(block):
    # Skip blank lines and `//` comment lines before judging whether a
    # block looks query-like -- confirmed real convention across
    # github/okta/thinkst-canary, where a genuine tag=/$MACRO query is
    # routinely preceded by a `// <description>` comment line; checking
    # only the literal first line would false-positive on all three.
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        return stripped
    return ""


def check_playbook_code_spans(root, findings):
    # Gravwell's playbook Markdown has one load-bearing exception to
    # ordinary Markdown (markdownguide.org basic syntax otherwise): a
    # backtick-delimited span -- fenced (```) block *or* inline
    # (`single-backtick`) span -- is not rendered as code, Gravwell
    # attempts to parse its contents as a query. The in-app editor's own
    # docs only mention fenced blocks; the real, current behavior is
    # broader and confirmed directly against a real rendered playbook,
    # not inferred: an ordinary inline span like `` `mgd` `` (a field
    # value, from Juniper's own changelog) rendered as a broken "Launch"
    # button with "Query parsing error: Invalid search module: mgd" in
    # the actual Gravwell UI. Playbooks were originally meant to package
    # a set of actually-runnable queries; real kit content (fenced and
    # inline alike) has drifted from that, using backticks for raw log
    # lines, config snippets, resource/macro names, and ordinary prose
    # code-styling the same way any other Markdown context would.
    #
    # Heuristic, not a real Gravwell query parser -- always a warning,
    # never an error. The Markdown spec also treats 4-space/1-tab
    # indentation as a code block, deliberately not checked here: too
    # easy to false-positive against an ordinarily indented nested list.
    # Known, confirmed-real gap: a fence glued directly to its content
    # with no newline (e.g. "count Flags```") isn't reliably parsed here
    # either -- real malformed fence usage seen in the wild (sysmon's
    # Kit Overview playbook, which also independently has 13 of its 16
    # fenced blocks as prose/headers/an image rather than queries --
    # that playbook's rendering is very likely broken today) -- a human
    # still needs to catch the glued-fence case by eye.
    playbook_dir = root / "playbook"
    if not playbook_dir.exists():
        return
    for meta_path in sorted(playbook_dir.glob("*.meta")):
        body_path = meta_path.with_suffix(".body")
        if not body_path.exists():
            continue
        d = _load_json_safe(meta_path)
        name = d.get("Name", meta_path.stem) if isinstance(d, dict) else meta_path.stem
        try:
            text = body_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for block in _playbook_fenced_blocks(text):
            first_line = _first_significant_line(block)
            if first_line and not _QUERY_LIKE_RE.match(first_line):
                finding(findings, "warning", "playbook Markdown",
                        f"playbook/{body_path.name} ({name})",
                        f"fenced code block doesn't look like a Gravwell query (starts "
                        f"{first_line[:60]!r}) -- Gravwell will still try to parse it as "
                        "one; if this is illustrative/non-query content, use <pre> instead "
                        "of a fenced block")

        # Inline spans are checked against the text with fenced blocks
        # removed first, so a fenced block's own content is never
        # double-counted or misread as a separate inline span.
        text_without_fences = _strip_fenced_blocks(text)
        for span in re.findall(r"`([^`\n]+)`", text_without_fences):
            stripped_span = span.strip()
            if stripped_span and not _QUERY_LIKE_RE.match(stripped_span):
                finding(findings, "warning", "playbook Markdown",
                        f"playbook/{body_path.name} ({name})",
                        f"inline code span doesn't look like a Gravwell query "
                        f"({stripped_span[:60]!r}) -- Gravwell will still try to parse it "
                        "as one; if this is an ordinary code-styled mention (a field, "
                        "macro, or resource name), use plain text or bold instead of "
                        "backticks")


_MULTI_UNDERSCORE_WORD_RE = re.compile(r"[\w]+(?:_[\w]+){2,}")


def check_playbook_underscore_emphasis(root, findings):
    # A second, distinct Gravwell playbook Markdown quirk from the
    # backtick-span one above: Gravwell doesn't apply CommonMark's usual
    # "an underscore inside a word isn't an emphasis delimiter"
    # exception. A self-contained identifier with 2+ underscores (e.g.
    # $JUNIPER_LOGIN_HELPER) gets its middle segment silently
    # italicized -- confirmed live in the Gravwell UI on a real Juniper
    # playbook, independent of whether the identifier also sits inside
    # **bold** wrapping (the wrapping wasn't the cause; the identifier's
    # own internal underscore pair is). Fenced blocks and inline
    # backtick spans are stripped first: neither is run through
    # Gravwell's Markdown emphasis engine at all (a fenced block is fed
    # to the query parser; an inline span renders as a Launch button,
    # per check_playbook_code_spans above), so an underscore inside
    # either isn't a candidate for this specific bug.
    #
    # Deliberately scoped narrower than "any bare underscore" -- that
    # fired 1511 times across 33 of 35 real kits' playbooks, unusably
    # noisy. Scoped instead to words with 2+ underscores forming a
    # self-contained pair fully inside one token -- the exact mechanism
    # confirmed live -- which drops to 284 real candidates fleet-wide,
    # 90% concentrated in 4 identifier-heavy kits (grok, duo, corelight,
    # cisco_ftd), not spread evenly as noise; most kits saw 0-6. A clean
    # __word__-style bold wrapper (double underscore at both edges,
    # standard correct Markdown) is excluded explicitly -- it isn't a
    # bug, and was the only real false-positive class found while
    # verifying this (3 of 287 candidates).
    #
    # Known, disclosed scope gap: words with exactly one underscore
    # (396 candidates fleet-wide) are NOT flagged -- whether a lone
    # underscore can still pair with an unrelated one elsewhere in the
    # same paragraph is unconfirmed, and flagging every one would
    # reintroduce the noise problem above. Real kit content escaped
    # these defensively without individually confirming each one
    # breaks; this check only asserts the confirmed mechanism.
    playbook_dir = root / "playbook"
    if not playbook_dir.exists():
        return
    for meta_path in sorted(playbook_dir.glob("*.meta")):
        body_path = meta_path.with_suffix(".body")
        if not body_path.exists():
            continue
        d = _load_json_safe(meta_path)
        name = d.get("Name", meta_path.stem) if isinstance(d, dict) else meta_path.stem
        try:
            text = body_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        prose = re.sub(r"`[^`\n]+`", "", _strip_fenced_blocks(text))
        seen = set()
        for match in _MULTI_UNDERSCORE_WORD_RE.finditer(prose):
            raw = match.group()
            if raw.startswith("__") and raw.endswith("__"):
                continue  # standard __bold__ wrapper, not a bug -- checked
                          # on the untrimmed match, before the rstrip below
                          # can strip its own closing "__" off
            # Trim a trailing bare underscore before a non-word character
            # (e.g. the literal "<alert_name_or_*>" placeholder syntax in
            # a real duo playbook) -- \w includes "_", so the regex's own
            # [\w]+ can glue an unrelated trailing underscore onto the
            # match; trimming keeps the reported identifier from looking
            # like a typo instead of the real one.
            word = raw.rstrip("_")
            if word.count("_") < 2:
                continue  # trimming dropped it below the 2-underscore threshold
            if word in seen:
                continue  # already reported once for this playbook
            offsets = [match.start() + i for i, c in enumerate(word) if c == "_"]
            if all(prose[o - 1] == "\\" for o in offsets):
                continue  # every underscore already escaped
            seen.add(word)
            finding(findings, "warning", "playbook Markdown",
                    f"playbook/{body_path.name} ({name})",
                    f"{word!r} has an unescaped multi-underscore run -- Gravwell doesn't "
                    "treat an intraword underscore as literal the way ordinary Markdown "
                    "does, so part of it can render silently italicized; escape each "
                    "underscore as \\_ if this is meant to display as plain text")


def check_dashboards(root, findings):
    dashboard_dir = root / "dashboard"
    if not dashboard_dir.exists():
        finding(findings, "error", f"{STANDARDS} {SEC['8']}", "dashboard/",
                "no dashboard directory found — an Overview dashboard is required for every kit")
        return
    names = []
    for p in sorted(dashboard_dir.glob("*.meta")):
        d = _load_json_safe(p)
        names.append(str(d.get("Name", p.stem)) if isinstance(d, dict) else p.stem)
    if not any("overview" in n.lower() for n in names):
        finding(findings, "warning", f"{STANDARDS} {SEC['8']}", "dashboard/",
                "no dashboard name suggests 'Overview' (heuristic match — required for every kit)")


def check_actionables(root, findings):
    # Actionables live on disk as pivot/ — confirmed via real .meta structure:
    # top-level Name follows the general dash-style kit-content convention, but
    # Data.menuLabel and Data.actions[].name are what actually correspond to
    # the Actionable-specific requirements in Standards §10 (proper menu
    # label, descriptive/clear action names) and Peer Review's "Names of
    # actionables are unique to the kit."
    pivot_dir = root / "pivot"
    if not pivot_dir.exists():
        return  # not every kit has actionables

    menu_labels = []  # (label, content, trigger patterns) for the uniqueness pass below
    for p in sorted(pivot_dir.glob("*.meta")):
        d = _load_json_safe(p)
        if not isinstance(d, dict):
            continue
        name = d.get("Name", p.stem)
        data = d.get("Data") or {}
        menu_label = data.get("menuLabel")
        if not isinstance(menu_label, str) or not menu_label.strip():
            finding(findings, "error", f"{STANDARDS} {SEC['10']}", f"pivot/{p.name} ({name})",
                    "Data.menuLabel is missing or empty")
        elif menu_label.strip():
            patterns = [t.get("pattern") for t in (data.get("triggers") or [])
                        if isinstance(t, dict) and t.get("pattern")]
            menu_labels.append((menu_label.strip(), f"pivot/{p.name} ({name})", patterns))
        for i, action in enumerate(data.get("actions") or []):
            if not isinstance(action, dict):
                continue
            action_name = action.get("name")
            if not isinstance(action_name, str) or not action_name.strip():
                finding(findings, "error", f"{STANDARDS} {SEC['10']}", f"pivot/{p.name} ({name})",
                        f"actions[{i}].name is missing or empty")

    # Uniqueness check has caught two real, confirmed instances that resolved
    # in *opposite* directions (a genuine structural ambiguity in one kit;
    # plain oversight, safely renamed, in another) -- telling them apart
    # needs each side's Data.triggers[].pattern, so the finding carries both
    # instead of requiring a human to open both .meta files to compare.
    from collections import Counter
    counts = Counter(label for label, _, _ in menu_labels)
    for label, content, patterns in menu_labels:
        if counts[label] > 1:
            others = ", ".join(
                f"{r} triggers={p!r}" for l, r, p in menu_labels if l == label and r != content
            )
            finding(findings, "warning", PEER_REVIEW_PLATFORM, content,
                    f"menuLabel {label!r} is not unique within this kit — "
                    f"this content's triggers={patterns!r}; also used by {others}")


def check_content_labels(root, findings):
    # Standards §7: dashboards/actionables(pivot)/macros/templates should
    # carry "EVs used" labels; detections need ATT&CK + metadata labels.
    # Confirmed real field: a "Labels" list/null on all four content types.
    # Kept as warning, not error — confirmed inconsistently applied even in
    # otherwise-clean sample kits (aws_cloudtrail's dashboards/pivots/
    # templates all have Labels: null), so this isn't a reliable "must" in
    # current practice despite being documented.
    #
    # section carries the directory (not a blanket "Standards §7") so a
    # fixer-tier dispatcher (kit-utilities' FIXER_TIERS) can tell dashboard/
    # pivot findings -- which `labelsuggest` sometimes resolves -- apart from
    # macro/template findings, which have zero real fixer coverage. Same
    # disambiguation pattern check_naming_consistency already uses below for
    # its own two finding types. Confirmed real gap this closes (2026-08-27,
    # kit-utilities feedback): before this split, macro/template findings
    # were indistinguishable from dashboard/pivot ones and got incorrectly
    # tagged "partial" in kit-utilities' vendored FIXER_TIERS.
    for d in ("dashboard", "pivot", "macro", "template"):
        dir_path = root / d
        if not dir_path.exists():
            continue
        for p in sorted(dir_path.glob("*.meta")):
            data = _load_json_safe(p)
            if not isinstance(data, dict):
                continue
            name = data.get("Name", p.stem)
            labels = data.get("Labels")
            if not labels:
                finding(findings, "warning", f"{STANDARDS} {SEC['7']} ({d})", f"{d}/{p.name} ({name})",
                        "no Labels set (EVs-used labeling convention)")


ATTCK_RE = re.compile(r"^T\d{4}(\.\d{3})?$")


def _scheduled_is_detection(root, d):
    # Standards §21 (via §18.1) and §7/§22's ATT&CK-labeling requirement
    # only bind genuine detection-driven scheduled searches. scheduled/
    # also holds ScheduledType "flow"/"script" aggregation/data-fetch jobs
    # that are legitimately meant to ship enabled — confirmed via
    # barracuda's 6 "flow" aggregates, all Disabled: false by design — and
    # ScheduledType "search" jobs with no real SearchReference, i.e.
    # aggregation work in disguise — confirmed via o365's "Historical User
    # Info" (search type, SearchReference null, 30-day lookback, also
    # Disabled: false). Scope to jobs that are actually a detection: type
    # "search" AND a SearchReference that resolves to a real searchlibrary
    # entry.
    if d.get("ScheduledType") != "search":
        return False
    search_ref = d.get("SearchReference")
    if not isinstance(search_ref, str) or not search_ref:
        return False
    return (root / "searchlibrary" / f"{search_ref}.meta").exists()


def check_detection_labels(root, findings):
    # Standards §7's Detections entry: ATT&CK Techniques + metadata labels.
    # Confirmed real shape via azure's scheduled search .meta: a Labels
    # array mixing categorical tags with literal ATT&CK IDs (e.g. T1562.004).
    scheduled_dir = root / "scheduled"
    if not scheduled_dir.exists():
        return
    for p in sorted(scheduled_dir.glob("*.meta")):
        d = _load_json_safe(p)
        if not isinstance(d, dict):
            continue
        if not _scheduled_is_detection(root, d):
            continue
        name = d.get("Name", p.stem)
        labels = d.get("Labels") or []
        if not any(isinstance(l, str) and ATTCK_RE.match(l) for l in labels):
            finding(findings, "warning", f"{STANDARDS} {SEC['7']} / {SEC['22']}", f"scheduled/{p.name} ({name})",
                    "no label matches an ATT&CK technique ID pattern (T####[.###])")


def check_macro_documentation(root, findings):
    # Standards §9 asks for Purpose/Parameters/Referencing content/
    # Modification safety notes. The real macro .meta shape only exposes a
    # single Description field — no structured Parameters/safety-notes
    # fields exist to check. This is a weak proxy (non-empty description),
    # not real compliance verification of the full §9 documentation ask.
    macro_dir = root / "macro"
    if not macro_dir.exists():
        return
    for p in sorted(macro_dir.glob("*.meta")):
        d = _load_json_safe(p)
        if not isinstance(d, dict):
            continue
        name = d.get("Name", p.stem)
        desc = d.get("Description")
        if not isinstance(desc, str) or not desc.strip():
            finding(findings, "warning", f"{STANDARDS} {SEC['9']}", f"macro/{p.name} ({name})",
                    "Description is missing or empty (weak proxy for the full "
                    "purpose/parameters/safety-notes documentation ask)")


def check_scheduled_searches(root, findings):
    scheduled_dir = root / "scheduled"
    if not scheduled_dir.exists():
        return  # Part III only binds when a kit includes detections

    detections = []  # (path, name, duration) for every genuine detection
    for p in sorted(scheduled_dir.glob("*.meta")):
        d = _load_json_safe(p)
        if not isinstance(d, dict):
            continue
        if not _scheduled_is_detection(root, d):
            continue
        name = d.get("Name", p.stem)
        ddr = d.get("DefaultDeploymentRules") or {}
        if ddr.get("Disabled") is not True:
            finding(findings, "error", f"{STANDARDS} {SEC['21']} / {PEER_REVIEW}", f"scheduled/{p.name} ({name})",
                    "DefaultDeploymentRules.Disabled is not true — scheduled searches must ship disabled")
        detections.append((p, name, d.get("Duration")))

    # Non-default Duration values, counted across this kit's own detections
    # -- a value used by only one detection reads differently from one
    # shared by several. Confirmed real (kit-utilities feedback, 2026-08-27):
    # 3 kits (okta, github, thinkst-canary) each show a clean, kit-wide,
    # gapless per-severity Duration scale, not drift -- e.g. thinkst-canary's
    # 49 non-default findings decompose into exactly 3 shared values (8/8,
    # 8/8, 40/40 detections). Never suppressed or downgraded here -- a
    # shared value can still be a genuine mistake, just a less likely one.
    # This annotates with the evidence a reviewer needs to judge that
    # themselves; it doesn't judge it for them.
    from collections import Counter
    duration_counts = Counter(
        duration for _, _, duration in detections if duration != EXPECTED_SCHEDULED_DURATION
    )
    for p, name, duration in detections:
        if duration == EXPECTED_SCHEDULED_DURATION:
            continue
        shared = duration_counts[duration]
        note = (f" — shared by {shared} scheduled searches in this kit; may be a "
                 "deliberate, consistent choice rather than drift, not evaluated further here"
                 if shared > 1 else "")
        finding(findings, "warning", f"{STANDARDS} {SEC['21']}", f"scheduled/{p.name} ({name})",
                f"Duration is {duration!r}, expected {EXPECTED_SCHEDULED_DURATION} (1h){note}")


def _content_names(root):
    """Collect (path, name) pairs from directories that carry human-readable
    kit-content names, for the naming-consistency check (§6)."""
    out = []
    for d in ("dashboard", "searchlibrary", "scheduled", "pivot"):
        dir_path = root / d
        if not dir_path.exists():
            continue
        for p in sorted(dir_path.glob("*.meta")):
            data = _load_json_safe(p)
            if isinstance(data, dict) and isinstance(data.get("Name"), str) and data["Name"].strip():
                out.append((f"{d}/{p.name}", data["Name"]))
    return out


def _prefix_of(name: str) -> str:
    # Always just the first word, regardless of whether a " - " separator is
    # present. An earlier version branched on dash-presence (full phrase
    # before " - " if present, else first word) and that inconsistency
    # produced false positives within a single kit — e.g. "Auditd Service
    # Reload - Linux" (dash-branch: prefix "Auditd Service Reload") vs
    # "Auditd Command Execution" (no-dash branch: prefix "Auditd") were
    # flagged as mismatched despite both genuinely being Auditd content.
    # Trailing punctuation is stripped too — real kits (syslog, sysmon)
    # mix "Syslog: <thing>" (searchlibrary) with "Syslog <thing>"
    # (dashboard/pivot), both already leading with the kit name; without
    # this the trailing colon alone split one dominant prefix into two.
    return name.strip().split(" ", 1)[0].strip().rstrip(string.punctuation)


def check_naming_consistency(root, findings):
    contents = _content_names(root)

    # whitespace hygiene — cheap, deterministic, found a real example in the wild
    for path, name in contents:
        if name != name.strip():
            finding(findings, "warning", "naming hygiene", path,
                    f"name has leading/trailing whitespace: {name!r}")

    if len(contents) < 3:
        return  # not enough samples to establish a dominant prefix meaningfully

    from collections import Counter
    prefixes = Counter(_prefix_of(name) for _, name in contents)
    dominant, dominant_count = prefixes.most_common(1)[0]
    if dominant_count / len(contents) <= 0.5:
        return  # no clear dominant convention in this kit, don't guess

    for path, name in contents:
        if _prefix_of(name) != dominant:
            finding(findings, "warning", f"{STANDARDS} {SEC['6']}", path,
                    f"name {name!r} doesn't share this kit's dominant naming prefix "
                    f"({dominant!r}) — possible leftover from another kit or inconsistent naming")


def check_readme_content(root, findings):
    readme = root / "README.md"
    if not readme.exists():
        return  # already flagged by check_build_assets
    try:
        text = readme.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return
    if "integration guide" not in text and "docs.gravwell.io" not in text:
        # A real kit shipped an in-kit "<Kit> - Integration Guide" playbook
        # whose existence this substring check can't see -- confirmed via
        # Thinkst Canary, where the guide existed but README said
        # "implementation guides" instead of "integration guide." The
        # underlying check is still correct (Standards §5.3 wants a
        # README-level pointer, not just in-kit content) but the
        # message shouldn't read as "no guide exists anywhere" when one does.
        has_guide_playbook = False
        playbook_dir = root / "playbook"
        if playbook_dir.exists():
            for p in playbook_dir.glob("*.meta"):
                d = _load_json_safe(p)
                pb_name = d.get("Name") if isinstance(d, dict) else None
                if isinstance(pb_name, str) and "integration guide" in pb_name.lower():
                    has_guide_playbook = True
                    break
        if has_guide_playbook:
            finding(findings, "warning", f"{STANDARDS} {SEC['5.3']}", "README.md",
                    "kit has an Integration Guide playbook but README doesn't reference it")
        else:
            finding(findings, "warning", f"{STANDARDS} {SEC['5.3']}", "README.md",
                    "no Integration Guide found anywhere in the kit")
    if "changelog" not in text:
        finding(findings, "warning", f"{STANDARDS} {SEC['5.3']}", "README.md",
                "no Changelog section found")


# ---------------------------- Orchestration ----------------------------

def _verify_all_checks_registered():
    # Catches the exact mistake a standards-doc revision pass is most
    # likely to introduce: adding a new check_* function and forgetting
    # to call it from run_all_checks(). That mistake fails silently
    # otherwise — no crash, no warning, the check just never runs. This
    # is a textual check against run_all_checks()'s own source rather
    # than a separate registry, so there's nothing extra to keep in
    # sync — the call list stays the single source of truth, this just
    # verifies every check_* function is actually mentioned in it.
    module = sys.modules[__name__]
    source = inspect.getsource(run_all_checks)
    all_check_fns = sorted(
        name for name, obj in inspect.getmembers(module, inspect.isfunction)
        if name.startswith("check_")
    )
    missing = [name for name in all_check_fns if name not in source]
    if missing:
        raise RuntimeError(
            "kitcheck.py internal error: check function(s) defined but never "
            f"called from run_all_checks(): {', '.join(missing)}. Add the call, "
            "or remove the function if it's genuinely unused."
        )


def run_all_checks(root: Path, base_manifest=None, is_new_kit=False):
    manifest, err = load_manifest(root)
    if err:
        return None, err

    findings = []
    check_manifest_core(manifest, findings)
    check_max_version(manifest, findings)
    check_version_increment(manifest, findings, base_manifest, is_new_kit)
    check_hashes_zeroed(manifest, findings)
    check_config_macro_tags(manifest, findings)

    kitname = kitname_from_id(manifest.get("ID"))
    check_build_assets(root, kitname, findings)
    check_images(root, findings)
    check_license(root, findings)
    check_macros_no_leading_pipe(root, findings)
    check_macro_documentation(root, findings)
    check_playbooks(root, findings)
    check_playbook_code_spans(root, findings)
    check_playbook_underscore_emphasis(root, findings)
    check_dashboards(root, findings)
    check_actionables(root, findings)
    check_content_labels(root, findings)
    check_detection_labels(root, findings)
    check_scheduled_searches(root, findings)
    check_naming_consistency(root, findings)
    check_readme_content(root, findings)

    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")

    # "Passes" requires zero findings of either severity, not just zero
    # errors -- a warning is real, unresolved work a kit still needs
    # before release, not something the report should wave through as
    # "all clear." (Earlier design deliberately treated errors==0 as
    # passing, calling it "meets_initial_threshold" -- a deliberately low
    # bar for velocity. Reversed 2026-08-25: that bar gave false
    # confidence that a kit with open warnings was ready to merge.)
    result = {
        "kit": {
            "directory": root.name,
            "id": manifest.get("ID"),
            "name": manifest.get("Name"),
            "version": manifest.get("Version"),
        },
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "total": len(findings),
            "passes": errors == 0 and warnings == 0,
        },
        "findings": findings,
    }
    return result, None


def render_text(result) -> str:
    lines = []
    kit = result["kit"]
    verdict = "PASSES" if result["summary"]["passes"] else "NEEDS ATTENTION"
    lines.append(f"kitcheck: {kit.get('name') or kit.get('directory')} ({kit.get('id')}) — {verdict}")
    lines.append(f"  {result['summary']['errors']} error(s), {result['summary']['warnings']} warning(s)")
    if not result["findings"]:
        lines.append("  no findings")
        return "\n".join(lines)
    for f in result["findings"]:
        marker = "ERROR" if f["severity"] == "error" else "warn "
        # `check` included so a copy-pasted summary (no JSON download
        # needed) is still enough to look up fixer coverage via
        # `bin/list-fixers` in kit-utilities -- the human-readable text
        # otherwise carries everything the JSON does except this field.
        lines.append(f"  [{marker}] {f['content']} — {f['message']} "
                      f"({f['section']}) [{f['check']}]")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Lightweight, read-only structural check for a Gravwell kit directory."
    )
    parser.add_argument("--input", "-i", required=True,
                         help="path directly to the kit directory (containing MANIFEST, BUILD, "
                              "content folders) — not a parent directory")
    parser.add_argument("--output", "-o", help="also write the JSON result to this file")
    parser.add_argument("--format", choices=["json", "text", "both"], default="json",
                         help="stdout format (default: json). JSON is always well-formed and "
                              "complete regardless of this choice.")
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument("--base-manifest",
                                help="path to the MANIFEST from the PR base ref, for this same "
                                     "kit directory — enables the version-iteration check "
                                     "(Standards §5.1). Omit when running outside PR context.")
    version_group.add_argument("--new-kit", action="store_true",
                                help="this kit directory is new in the current PR (no MANIFEST "
                                     "existed at the base ref) — checks Version starts at 1 "
                                     "instead of comparing against a base.")
    args = parser.parse_args()

    root = Path(args.input).resolve()
    if not root.exists() or not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    base_manifest = None
    if args.base_manifest:
        base_manifest, base_err = load_manifest_file(Path(args.base_manifest))
        if base_err:
            print(f"warning: {base_err} — skipping the version-iteration check", file=sys.stderr)
            base_manifest = None

    result, err = run_all_checks(root, base_manifest=base_manifest, is_new_kit=args.new_kit)
    if err:
        print(f"error: {err}", file=sys.stderr)
        print(f"error: {root} does not look like a kit directory. Point --input directly "
              "at the kit (the directory containing MANIFEST, BUILD, and content folders), "
              "not a parent directory — this tool does not auto-discover a kit root.",
              file=sys.stderr)
        sys.exit(1)

    if args.format in ("json", "both"):
        print(json.dumps(result, indent=2))
    if args.format in ("text", "both"):
        print(render_text(result))

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    # Findings never affect the exit code — this is a component, not a gate.
    # Only "couldn't evaluate the input at all" (handled above) is a failure.
    sys.exit(0)


_verify_all_checks_registered()  # runs on import, not just direct execution

if __name__ == "__main__":
    main()
