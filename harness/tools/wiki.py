# Maintains the repo wiki in docs/wiki (spec 34), an Open Knowledge Format (OKF) v0.2 bundle. The skill repo-wiki drives it.
# Run from the repo root:
#   uv run python harness/tools/wiki.py index        write every index.md
#   uv run python harness/tools/wiki.py check        validate pages, links, indexes and log.md
#   uv run python harness/tools/wiki.py stale [--since <rev>]
#   uv run python harness/tools/wiki.py stamp [--command init|update]
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

WIKI_DIR = "docs/wiki"
INDEX_NAME = "index.md"
LOG_NAME = "log.md"
RESERVED_NAMES = (INDEX_NAME, LOG_NAME)
LAST_UPDATE_NAME = ".last-update.json"
QUICKSTART_NAME = "quickstart.md"
OKF_VERSION = "0.2"
REPO_SCHEME = "repo://"
URL_PREFIXES = ("http://", "https://")
REQUIRED_TEXT_KEYS = ("type", "title", "description")
STATUS_VALUES = ("draft", "stable", "deprecated")
ROOT_INDEX_FRONT_MATTER = f'---\nokf_version: "{OKF_VERSION}"\n---\n'

ACTOR_PATTERN = re.compile(r"^(human:|process:)\S+$|^[^\s/:]+/\S+$")
LOG_DATE_PATTERN = re.compile(r"^## (.+?)\s*$")
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_PATTERN = re.compile(r"`[^`]*`")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:")


class WikiError(Exception):
    """A page or index breaks the wiki format. The message says where and why."""


# ---------- front matter ----------

def split_front_matter(text, page_name):
    """Return (front matter text, body). Fail when the page has no front matter."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise WikiError(f"{page_name}: the page must start with '---' front matter")
    for number in range(1, len(lines)):
        if lines[number].strip() == "---":
            return "\n".join(lines[1:number]), "\n".join(lines[number + 1:])
    raise WikiError(f"{page_name}: the front matter has no closing '---'")


def parse_front_matter(text, page_name):
    """Parse the YAML front matter into a dict. OKF allows any YAML keys, so only invalid YAML fails."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise WikiError(f"{page_name}: front matter is not valid YAML: {error}") from error
    if not isinstance(data, dict):
        raise WikiError(f"{page_name}: front matter must be a YAML mapping")
    return data


def read_page(path, page_name):
    """Return (front matter dict, body) of one wiki page."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    front_matter, body = split_front_matter(text, page_name)
    return parse_front_matter(front_matter, page_name), body


def source_resources(meta):
    """The resource strings of the `sources` entries, skipping malformed ones (check reports those)."""
    sources = meta.get("sources")
    if not isinstance(sources, list):
        return []
    return [s["resource"] for s in sources if isinstance(s, dict) and isinstance(s.get("resource"), str)]


def repo_paths(meta):
    """Repo-relative paths of the `repo://` sources of one page."""
    return [r[len(REPO_SCHEME):] for r in source_resources(meta) if r.startswith(REPO_SCHEME)]


# ---------- wiki layout ----------

def wiki_root(repo_root):
    root = repo_root / WIKI_DIR
    if not root.is_dir():
        raise WikiError(f"no wiki folder at {root}; create {WIKI_DIR}/{QUICKSTART_NAME} first")
    return root


def page_paths(wiki):
    """All concept pages (not the reserved index.md and log.md), sorted, as paths."""
    return sorted(p for p in wiki.rglob("*.md") if p.name not in RESERVED_NAMES)


def wiki_folders(wiki):
    """The wiki root and every folder that holds a page, sorted."""
    folders = {wiki}
    for page in page_paths(wiki):
        folder = page.parent
        while folder != wiki:
            folders.add(folder)
            folder = folder.parent
    return sorted(folders)


def relative_name(path, repo_root):
    return path.relative_to(repo_root).as_posix()


# ---------- index ----------

def page_sort_key(path):
    # The quickstart is the entry page, so it goes first in the root index.
    return (path.name != QUICKSTART_NAME, path.name)


def folder_pages(folder):
    return sorted((p for p in folder.glob("*.md") if p.name not in RESERVED_NAMES), key=page_sort_key)


def folder_description(folder, repo_root):
    # OKF entries SHOULD carry a description; a folder has no front matter, so its page titles describe it.
    titles = [read_page(p, relative_name(p, repo_root))[0].get("title", p.stem) for p in folder_pages(folder)]
    return "Pages: " + ", ".join(titles) + "." if titles else "Subfolders only."


def index_text(folder, wiki, repo_root):
    """The full generated index.md for one folder (OKF section 8)."""
    pages = folder_pages(folder)
    subfolders = sorted(f for f in wiki_folders(wiki) if f.parent == folder and f != folder)
    parts = [ROOT_INDEX_FRONT_MATTER] if folder == wiki else []
    if pages:
        parts += ["# Pages", ""]
        for page in pages:
            meta, _ = read_page(page, relative_name(page, repo_root))
            parts.append(f"* [{meta.get('title', page.stem)}]({page.name}) - {meta.get('description', '')}")
        parts.append("")
    if subfolders:
        parts += ["# Folders", ""]
        parts += [f"* [{sub.name}]({sub.name}/) - {folder_description(sub, repo_root)}" for sub in subfolders]
        parts.append("")
    return "\n".join(parts)


def write_text_atomic(path, text):
    temp = path.with_name(path.name + ".tmp")
    with open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)


def write_indexes(repo_root):
    """Write every index.md and remove indexes of folders with no pages. Return the written paths."""
    wiki = wiki_root(repo_root)
    folders = wiki_folders(wiki)
    for stale_index in wiki.rglob(INDEX_NAME):
        if stale_index.parent not in folders:
            stale_index.unlink()
    written = []
    for folder in folders:
        target = folder / INDEX_NAME
        write_text_atomic(target, index_text(folder, wiki, repo_root))
        written.append(relative_name(target, repo_root))
    return written


# ---------- check: front matter ----------

def is_datetime_with_offset(value):
    """OKF timestamps are ISO 8601 datetimes with an explicit UTC offset."""
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value)
        except ValueError:
            return False
    return isinstance(value, datetime.datetime) and value.tzinfo is not None


def check_event(event, key, page_name):
    """Check one `{by, at}` mapping of `generated` or `verified`."""
    if not isinstance(event, dict):
        return [f"{page_name}: '{key}' must be a mapping {{ by, at }}"]
    errors = []
    if not isinstance(event.get("by"), str) or not ACTOR_PATTERN.match(event["by"]):
        errors.append(f"{page_name}: '{key}.by' must be an actor: <producer>/<version>, human:<id> or process:<id>")
    if not is_datetime_with_offset(event.get("at")):
        errors.append(f"{page_name}: '{key}.at' must be an ISO 8601 datetime with a UTC offset, for example 2026-10-18T15:00:00Z")
    return errors


def check_trust(meta, page_name):
    errors = check_event(meta.get("generated"), "generated", page_name)
    if "verified" in meta:
        verified = meta["verified"]
        # OKF: a bare mapping counts as a one-element list.
        for event in verified if isinstance(verified, list) else [verified]:
            errors += check_event(event, "verified", page_name)
    if "status" in meta and meta["status"] not in STATUS_VALUES:
        errors.append(f"{page_name}: 'status' must be one of {', '.join(STATUS_VALUES)}")
    if "stale_after" in meta and not is_datetime_with_offset(meta["stale_after"]):
        errors.append(f"{page_name}: 'stale_after' must be an ISO 8601 datetime with a UTC offset")
    return errors


def check_source_resource(resource, page_name, repo_root):
    if resource.startswith(URL_PREFIXES):
        return []
    if not resource.startswith(REPO_SCHEME):
        return [f"{page_name}: source '{resource}' must start with {REPO_SCHEME} (or be an http(s) URL)"]
    path = resource[len(REPO_SCHEME):]
    if not path or path.startswith("/") or ".." in Path(path).parts or "\\" in path:
        return [f"{page_name}: source '{resource}' must be {REPO_SCHEME}<repo-relative path with forward slashes>"]
    target = repo_root / path
    if path.endswith("/") and not target.is_dir():
        return [f"{page_name}: source folder '{resource}' does not exist"]
    if not path.endswith("/") and not target.is_file():
        return [f"{page_name}: source file '{resource}' does not exist (end a folder with '/')"]
    return []


def check_sources(meta, page_name, repo_root):
    sources = meta.get("sources")
    if not isinstance(sources, list) or not sources:
        return [f"{page_name}: 'sources' must be a non-empty list of {{ resource: ... }} entries"]
    errors = []
    for number, entry in enumerate(sources, start=1):
        if not isinstance(entry, dict) or not isinstance(entry.get("resource"), str):
            errors.append(f"{page_name}: sources entry {number} must be a mapping with a 'resource' text")
            continue
        errors += check_source_resource(entry["resource"], page_name, repo_root)
    return errors


def check_front_matter(meta, page_name, repo_root):
    errors = []
    for key in REQUIRED_TEXT_KEYS:
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            errors.append(f"{page_name}: front matter '{key}' must be a non-empty text")
    tags = meta.get("tags")
    if not isinstance(tags, list) or not tags or not all(isinstance(t, str) for t in tags):
        errors.append(f"{page_name}: front matter 'tags' must be a non-empty list of texts")
    errors += check_sources(meta, page_name, repo_root)
    errors += check_trust(meta, page_name)
    return errors


# ---------- check: links, indexes, log ----------

def heading_slug(heading):
    """GitHub-style anchor for a heading text."""
    text = INLINE_CODE_PATTERN.sub(lambda m: m.group(0)[1:-1], heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def outside_code(lines):
    """Yield (line number, line) for lines outside fenced code, with inline code removed."""
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if FENCE_PATTERN.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield number, INLINE_CODE_PATTERN.sub("", line)


def heading_anchors(text):
    anchors = set()
    counts = {}
    for _, line in outside_code(text.split("\n")):
        match = HEADING_PATTERN.match(line)
        if not match:
            continue
        slug = heading_slug(match.group(2))
        seen = counts.get(slug, 0)
        anchors.add(slug if seen == 0 else f"{slug}-{seen}")
        counts[slug] = seen + 1
    return anchors


def check_link(href, page, page_name, repo_root, anchors_of):
    """Return the errors of one link href on one page."""
    if href.startswith(EXTERNAL_PREFIXES):
        return []
    if href.startswith("/"):
        # OKF allows bundle-relative links, but GitHub resolves '/' from the repo root, so the wiki uses relative links.
        return [f"{page_name}: link '{href}' is root-absolute; make it relative to the page"]
    path_part, _, anchor = href.partition("#")
    target = page if path_part == "" else (page.parent / path_part).resolve()
    if not target.exists():
        return [f"{page_name}: link '{href}' points to a missing file"]
    if repo_root.resolve() not in target.resolve().parents and target.resolve() != repo_root.resolve():
        return [f"{page_name}: link '{href}' points outside the repo"]
    if anchor and target.suffix == ".md" and anchor not in anchors_of(target):
        return [f"{page_name}: link '{href}' has no heading '#{anchor}' in the target"]
    return []


def check_links(page, body, page_name, repo_root, anchors_of):
    errors = []
    for number, line in outside_code(body.split("\n")):
        for href in LINK_PATTERN.findall(line):
            errors += [f"{error} (body line {number})" for error in check_link(href, page, page_name, repo_root, anchors_of)]
    return errors


def check_indexes(wiki, repo_root):
    errors = []
    for folder in wiki_folders(wiki):
        target = folder / INDEX_NAME
        name = relative_name(target, repo_root)
        if not target.is_file():
            errors.append(f"{name}: missing; run 'wiki.py index'")
        elif target.read_text(encoding="utf-8").replace("\r\n", "\n") != index_text(folder, wiki, repo_root):
            errors.append(f"{name}: out of date or edited by hand; run 'wiki.py index'")
    return errors


def check_log(path, repo_root):
    """OKF section 9: date headings in YYYY-MM-DD form, newest first."""
    name = relative_name(path, repo_root)
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if text.startswith("---\n"):
        return [f"{name}: a log file has no front matter"]
    errors = []
    dates = []
    for number, line in outside_code(text.split("\n")):
        match = LOG_DATE_PATTERN.match(line)
        if not match:
            continue
        try:
            dates.append(datetime.date.fromisoformat(match.group(1)))
        except ValueError:
            errors.append(f"{name}: line {number}: date heading must be '## YYYY-MM-DD'")
    if dates != sorted(dates, reverse=True):
        errors.append(f"{name}: date headings must be newest first")
    return errors


def anchor_reader():
    cache = {}

    def anchors_of(path):
        if path not in cache:
            cache[path] = heading_anchors(path.read_text(encoding="utf-8").replace("\r\n", "\n"))
        return cache[path]
    return anchors_of


def check_wiki(repo_root):
    """Return a list of error texts. An empty list means the wiki is valid."""
    wiki = wiki_root(repo_root)
    errors = []
    if not (wiki / QUICKSTART_NAME).is_file():
        errors.append(f"{WIKI_DIR}/{QUICKSTART_NAME}: missing; the wiki needs an entry page")
    anchors_of = anchor_reader()
    unreadable_pages = 0
    for page in page_paths(wiki):
        page_name = relative_name(page, repo_root)
        try:
            meta, body = read_page(page, page_name)
        except WikiError as error:
            errors.append(str(error))
            unreadable_pages += 1
            continue
        errors += check_front_matter(meta, page_name, repo_root)
        errors += check_links(page, body, page_name, repo_root, anchors_of)
    for log in sorted(wiki.rglob(LOG_NAME)):
        errors += check_log(log, repo_root)
    # An unreadable page makes index generation fail, so compare indexes only when all pages parse.
    if unreadable_pages == 0:
        errors += check_indexes(wiki, repo_root)
    return errors


# ---------- stale and stamp ----------

def git(repo_root, *args):
    result = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise WikiError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def last_update(repo_root):
    path = wiki_root(repo_root) / LAST_UPDATE_NAME
    if not path.is_file():
        raise WikiError(f"{WIKI_DIR}/{LAST_UPDATE_NAME} is missing; run 'wiki.py stamp' after an init")
    return json.loads(path.read_text(encoding="utf-8"))


def changed_paths(repo_root, since):
    """Paths changed after commit `since`: committed, staged, unstaged and untracked. Wiki files are left out."""
    committed = git(repo_root, "diff", "--name-only", f"{since}..HEAD").split("\n")
    uncommitted = git(repo_root, "diff", "--name-only", "HEAD").split("\n")
    untracked = git(repo_root, "ls-files", "--others", "--exclude-standard").split("\n")
    paths = {p.strip() for p in committed + uncommitted + untracked if p.strip()}
    return sorted(p for p in paths if not p.startswith(WIKI_DIR + "/"))


def source_covers(source, path):
    return path.startswith(source) if source.endswith("/") else path == source


def stale_report(repo_root, since=None):
    """Which pages have changed sources, and which changed paths no page covers."""
    wiki = wiki_root(repo_root)
    base = since or last_update(repo_root)["gitHead"]
    changed = changed_paths(repo_root, base)
    stale = {}
    covered = set()
    for page in page_paths(wiki):
        meta, _ = read_page(page, relative_name(page, repo_root))
        sources = repo_paths(meta)
        hits = [p for p in changed if any(source_covers(s, p) for s in sources)]
        missing = [REPO_SCHEME + s for s in sources if not (repo_root / s).exists()]
        if hits or missing:
            stale[relative_name(page, repo_root)] = {"changed": hits, "missing_sources": missing}
        covered.update(hits)
    return {"base": base, "changed": changed, "stale": stale,
            "uncovered": [p for p in changed if p not in covered]}


def stamp(repo_root, command):
    wiki = wiki_root(repo_root)
    record = {"updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "command": command,
              "gitHead": git(repo_root, "rev-parse", "HEAD").strip(),
              "pages": len(page_paths(wiki))}
    write_text_atomic(wiki / LAST_UPDATE_NAME, json.dumps(record, indent=2) + "\n")
    return record


# ---------- command line ----------

def repo_root_from(start):
    return Path(git(start, "rev-parse", "--show-toplevel").strip())


def build_parser():
    parser = argparse.ArgumentParser(description="Maintain the repo wiki in docs/wiki (spec 34, OKF v0.2).")
    parser.add_argument("--repo", default=".", help="a path inside the repo (default: current folder)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("index", help="write every index.md from the page front matter")
    commands.add_parser("check", help="validate pages, sources, links, indexes and log.md")
    stale = commands.add_parser("stale", help="list pages whose sources changed")
    stale.add_argument("--since", help="commit to compare with (default: gitHead in .last-update.json)")
    stamp_parser = commands.add_parser("stamp", help="record the current commit in .last-update.json")
    stamp_parser.add_argument("--command", dest="run_command", default="update", choices=["init", "update"])
    return parser


def run(args):
    repo_root = repo_root_from(Path(args.repo))
    if args.command == "index":
        print("\n".join(write_indexes(repo_root)))
        return 0
    if args.command == "check":
        errors = check_wiki(repo_root)
        print("\n".join(errors) if errors else "wiki check: ok")
        return 1 if errors else 0
    if args.command == "stale":
        print(json.dumps(stale_report(repo_root, args.since), indent=2))
        return 0
    print(json.dumps(stamp(repo_root, args.run_command), indent=2))
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except WikiError as error:
        print(f"wiki error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
