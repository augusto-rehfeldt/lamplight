"""Build the bundled public-domain catalog: python game_catalog.py.

Uses Project Gutenberg's official bulk RDF feed, with explicit per-book rights.
Retain the USA jurisdiction explicitly; editions can differ elsewhere.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import tarfile
from xml.etree import ElementTree as ET

import requests

ROOT = pathlib.Path(__file__).resolve().parent
CATALOG = ROOT / "game" / "books.json"
CATEGORIES = {
    "Philosophy": ("philosophy", "ethics", "logic", "metaphysics"),
    "Science": ("science", "biology", "physics", "astronomy", "natural history", "mathematics", "medicine", "evolution"),
    "Politics": ("politic", "government", "economics", "socialism", "sociology"),
    "Religion": ("religio", "theology", "bible", "buddhis", "hindu", "mythology"),
    "History": ("history", "civilization", "biography", "travel"),
    "Literature": ("fiction", "poetry", "drama", "literature", "essays"),
}


def simplify(book: dict) -> dict | None:
    urls = [v for k, v in book.get("formats", {}).items()
            if k.startswith("text/plain") and not v.endswith(".zip")]
    if book.get("copyright") is not False or not urls or book.get("media_type") != "Text":
        return None
    subjects = " ".join(book.get("subjects", []) + book.get("bookshelves", [])).lower()
    categories = [cat for cat, words in CATEGORIES.items() if any(w in subjects for w in words)]
    return dict(id=book["id"], title=book["title"],
                authors=[a["name"] for a in book.get("authors", [])],
                categories=categories or ["Literature"], languages=book["languages"],
                subjects=book.get("subjects", []),
                summary=" ".join(book.get("summaries", [])),
                url=f"https://www.gutenberg.org/ebooks/{book['id']}",
                text_url=next((v for v in urls if "utf-8" in v), urls[0]),
                rights="Public domain in the USA", copyright=False)


NS = {"d": "http://purl.org/dc/terms/", "p": "http://www.gutenberg.org/2009/pgterms/",
      "r": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}


def from_rdf(raw: bytes) -> dict | None:
    ebook = ET.fromstring(raw).find("p:ebook", NS)
    if ebook is None or ebook.findtext("d:rights", "", NS).strip().rstrip(".") != "Public domain in the USA":
        return None
    languages = [e.text for e in ebook.findall("d:language//r:value", NS)]
    if "en" not in languages:
        return None
    formats = {}
    for f in ebook.findall("d:hasFormat/p:file", NS):
        types = [e.text or "" for e in f.findall("d:format//r:value", NS)]
        url = f.get("{" + NS["r"] + "}about", "").replace("http://", "https://", 1)
        if "text/plain" in " ".join(types) and not url.endswith(".zip"):
            formats["text/plain; " + "; ".join(types)] = url
    book = simplify(dict(id=int(ebook.get("{" + NS["r"] + "}about").split("/")[-1]),
        title=ebook.findtext("d:title", "", NS), languages=languages, copyright=False,
        media_type=ebook.findtext("d:type//r:value", "", NS), formats=formats,
        authors=[{"name": e.text} for e in ebook.findall("d:creator/p:agent/p:name", NS)],
        subjects=[e.text for e in ebook.findall("d:subject//r:value", NS)],
        bookshelves=[e.text for e in ebook.findall("p:bookshelf//r:value", NS)],
        summaries=[ebook.findtext("p:marc520", "", NS)]))
    if book:
        book["downloads"] = int(ebook.findtext("p:downloads", "0", NS))
        book["rights_source"] = f"https://www.gutenberg.org/cache/epub/{book['id']}/pg{book['id']}.rdf"
    return book


def build(minimum: int = 1200) -> None:
    archive = ROOT / "output" / "lamplight" / "catalog-rdf.tar.bz2"
    if not archive.exists():
        archive.parent.mkdir(parents=True, exist_ok=True)
        temp = archive.with_suffix(".download")
        with requests.get("https://www.gutenberg.org/cache/epub/feeds/rdf-files.tar.bz2",
                          stream=True, timeout=(15, 120)) as response:
            response.raise_for_status()
            with temp.open("wb") as out:
                for chunk in response.iter_content(1024 * 1024):
                    out.write(chunk)
        temp.replace(archive)
    eligible = []
    # Read members directly: never extract paths from an external archive.
    with tarfile.open(archive, "r|bz2") as tar:
        for i, member in enumerate(tar):
            if member.isfile() and member.name.endswith(".rdf"):
                book = from_rdf(tar.extractfile(member).read())
                if book:
                    eligible.append(book)
            if i % 10000 == 0:
                print(f"Read {i:,} records; {len(eligible):,} eligible", flush=True)
    eligible.sort(key=lambda b: -b["downloads"])
    collected = {}
    for category in CATEGORIES:
        for book in [b for b in eligible if category in b["categories"]][:150]:
            collected[book["id"]] = book
    for book in eligible:
        if len(collected) >= minimum:
            break
        collected[book["id"]] = book
    if len(collected) < minimum:
        raise RuntimeError(f"Only {len(collected)} books; existing catalog left intact")
    CATALOG.parent.mkdir(exist_ok=True)
    temp = CATALOG.with_suffix(".tmp")
    temp.write_text(json.dumps(sorted(collected.values(), key=lambda b: -b["downloads"]), ensure_ascii=False), encoding="utf-8")
    temp.replace(CATALOG)
    print(f"Saved {len(collected)} verified catalog records to {CATALOG}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minimum", type=int, default=1200)
    build(max(1000, parser.parse_args().minimum))
