#!/usr/bin/env python3
"""Build the static catalog pages for the Fresh-Teacher/exams collection.

Every class folder in the exams repository becomes its own documents page, so a
class hub can link straight to it. Records are written into the same shard files
the rest of the catalog uses, keyed by a stable id derived from the file path,
and registered in the document index so each file also opens on its own page.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = ROOT / "src" / "data" / "catalog" / "documents"
PAGES = ROOT / "src" / "data" / "catalog" / "pages" / "repositories"
INDEX = ROOT / "src" / "data" / "catalog" / "document-index"
MANIFEST = ROOT / "src" / "data" / "catalog" / "repositories.json"
SUMMARY = ROOT / "src" / "data" / "catalog" / "summary.json"

OWNER = "Fresh-Teacher"
REPO = "exams"
TREE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/main?recursive=1"
CACHE = Path("/tmp/exams/tree.json")

# Repository folder -> (class key, catalog label, page label)
CLASSES: dict[str, tuple[str, str, str]] = {
    "Baby": ("baby", "Baby Class", "Baby Class Examinations"),
    "Middle": ("middle", "Middle Class", "Middle Class Examinations"),
    "Top": ("top", "Top Class", "Top Class Examinations"),
    "P1": ("p1", "Primary One", "Primary One Examinations"),
    "P2": ("p2", "Primary Two", "Primary Two Examinations"),
    "P3": ("p3", "Primary Three", "Primary Three Examinations"),
    "P4": ("p4", "Primary Four", "Primary Four Examinations"),
    "P5": ("p5", "Primary Five", "Primary Five Examinations"),
    "P6": ("p6", "Primary Six", "Primary Six Examinations"),
    "P7": ("p7", "Primary Seven", "Primary Seven Examinations"),
    "S1": ("s1", "Senior One", "Senior One Examinations"),
    "S2": ("s2", "Senior Two", "Senior Two Examinations"),
    "S3": ("s3", "Senior Three", "Senior Three Examinations"),
    "S4": ("s4", "Senior Four", "Senior Four Examinations"),
    "S5": ("s5", "Senior Five", "Senior Five Examinations"),
    "S6": ("s6", "Senior Six", "Senior Six Examinations"),
}

PRIMARY_FOLDERS = {"Baby", "Middle", "Top", "P1", "P2", "P3", "P4", "P5", "P6"}
# Root PDFs named after a class are that class's holiday package.
PACKAGE_FILES = {"Baby": "Baby.PDF", "Middle": "Middle Class.PDF", "Top": "Top.PDF", **{f"P{n}": f"P{n}.PDF" for n in range(1, 7)}}
# (repo path, display title) shown on every Baby-P6 page.
SHARED_EXAMS = [("All Class Exams.pdf", "All Exams"), ("All Holiday Packages.pdf", "All Holiday Packages")]
SHARED_PACKAGES = [("All Holiday Packages.pdf", "All Holiday Packages"), ("All Holiday Packages.zip", "All Holiday Packages (ZIP)")]


def by_path(blobs: list[dict], path: str) -> dict | None:
    return next((entry for entry in blobs if entry["path"] == path), None)


def shared(blobs: list[dict], items: list[tuple[str, str]]) -> list[tuple[dict, str, str]]:
    found = []
    for path, title in items:
        entry = by_path(blobs, path)
        if entry is not None:
            found.append((entry, title, "Baby Class to Primary Six"))
    return found


DOCUMENT_SUFFIXES = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".zip", ".rar", ".7z"}


def load_tree() -> list[dict]:
    if CACHE.is_file():
        payload = json.loads(CACHE.read_text(encoding="utf-8"))
    else:
        with urllib.request.urlopen(TREE_URL, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(payload), encoding="utf-8")
    if payload.get("truncated"):
        raise SystemExit("GitHub returned a truncated tree; refusing to write a partial catalog.")
    return payload["tree"]


def file_url(path: str) -> str:
    encoded = "/".join(urllib.parse.quote(segment) for segment in path.split("/"))
    return f"https://raw.githubusercontent.com/{OWNER}/{REPO}/HEAD/{encoded}"


def document_id(path: str) -> str:
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:16]


def document_key(url: str) -> str:
    """Mirror lib/document-metadata.ts: two independent 32-bit hashes of the URL."""
    a, b = 2166136261, 5381
    for char in url:
        code = ord(char)
        a = ((a ^ code) * 16777619) & 0xFFFFFFFF
        b = (((b * 33) & 0xFFFFFFFF) ^ code) & 0xFFFFFFFF
    return f"{a:08x}{b:08x}"


def title_for(path: str) -> str:
    name = Path(path).name
    for suffix in DOCUMENT_SUFFIXES:
        if name.lower().endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name.replace("-compressed", "").replace("_", " ").replace("  ", " ").strip()


def compact(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def merge(target: Path, entries: dict[str, dict]) -> None:
    """Add records to an existing shard, reading each shard exactly once."""
    prefixes = {identifier[:2] for identifier in entries}
    for prefix in prefixes:
        path = target / f"{prefix}.json"
        records = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        for identifier, record in entries.items():
            if identifier.startswith(prefix):
                records[identifier] = record
        path.write_text(compact(records) + "\n", encoding="utf-8")


def main() -> int:
    tree = load_tree()
    blobs = [entry for entry in tree if entry["type"] == "blob"]

    records: dict[str, dict[str, object]] = {}
    index_entries: dict[str, dict[str, object]] = {}
    pages: dict[str, dict[str, object]] = {}

    for folder, (key, label, page_label) in CLASSES.items():
        archive = f"{folder}.zip"
        archive_blob = next((entry for entry in blobs if entry["path"] == archive), None)
        files = sorted(
            (entry for entry in blobs
             if entry["path"].startswith(f"{folder}/")
             and Path(entry["path"]).suffix.lower() in DOCUMENT_SUFFIXES),
            key=lambda entry: entry["path"].lower(),
        )
        ordered: list[dict] = []
        if archive_blob is not None:
            ordered.append(archive_blob)
        ordered.extend(files)

        primary = folder in PRIMARY_FOLDERS
        exam_titles: list[tuple[dict, str, str]] = []
        if archive_blob is not None:
            exam_titles.append((archive_blob, "All Examinations", label))
        exam_titles.extend((entry, title_for(entry["path"]), label) for entry in files)
        if primary:
            exam_titles.extend(shared(blobs, SHARED_EXAMS))

        package_titles: list[tuple[dict, str, str]] = []
        if primary:
            package = by_path(blobs, PACKAGE_FILES[folder])
            if package is not None:
                package_titles.append((package, f"{label} Holiday Package", label))
            package_titles.extend(shared(blobs, SHARED_PACKAGES))

        for repo_key, title, entries in (
            (f"exams-{key}", page_label, exam_titles),
            (f"packages-{key}", f"{label} Holiday Packages", package_titles),
        ):
            document_ids: list[str] = []
            for entry, doc_title, description in entries:
                # Shared files appear on several pages; give each page its own record.
                identifier = document_id(f"{repo_key}:{entry['path']}")
                url = file_url(entry["path"])
                records[identifier] = {"title": doc_title, "description": description, "price": "", "pdfUrl": url}
                index_entries.setdefault(document_key(url), {
                    "id": identifier,
                    "path": f"more/{repo_key}",
                    "kind": "repositories",
                    "data": f"{repo_key}.json",
                })
                document_ids.append(identifier)
            pages[repo_key] = {"title": title, "documentIds": document_ids}

    if not pages:
        raise SystemExit("No exam files found in the repository.")

    merge(DOCUMENTS, records)
    merge(INDEX, index_entries)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    commit = hashlib.sha1(json.dumps(sorted(records), sort_keys=True).encode()).hexdigest()
    for repo_key, page in pages.items():
        (PAGES / f"{repo_key}.json").write_text(compact(page) + "\n", encoding="utf-8")
        manifest["repositories"][repo_key] = {
            "label": page["title"],
            "data": f"{repo_key}.json",
            "count": len(page["documentIds"]),
            "commit": commit,
        }
    MANIFEST.write_text(compact(manifest) + "\n", encoding="utf-8")

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary["repositoryPages"] = len(manifest["repositories"])
    summary["repositoryReferences"] = sum(page["count"] for page in manifest["repositories"].values())
    # uniqueRecords is the size of the whole record store, so count it instead of guessing the delta.
    summary["uniqueRecords"] = sum(
        len(json.loads(path.read_text(encoding="utf-8"))) for path in sorted(DOCUMENTS.glob("*.json"))
    )
    SUMMARY.write_text(compact(summary) + "\n", encoding="utf-8")

    for repo_key, page in sorted(pages.items()):
        print(f"{repo_key}: {len(page['documentIds'])} files")
    print(f"records: {len(records)} | index entries: {len(index_entries)}")
    print(f"summary: repositoryPages={summary['repositoryPages']} repositoryReferences={summary['repositoryReferences']} uniqueRecords={summary['uniqueRecords']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
