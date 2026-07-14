#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

TARGET = 100_000
MAX_EVIDENCE = 1800
MIN_EVIDENCE = 45
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
SPACE_RE = re.compile(r"\s+")


def clean(text: str | None) -> str:
    if not text:
        return ""
    return SPACE_RE.sub(" ", text.replace("\u0000", " ")).strip()


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", clean(text)).lower()
    text = re.sub(r"[^a-z0-9%+\-\s]", " ", text)
    return SPACE_RE.sub(" ", text).strip()


def sentence_chunks(answer: str) -> list[str]:
    parts = [clean(x) for x in SENTENCE_RE.split(answer)]
    parts = [x for x in parts if len(x) >= MIN_EVIDENCE]
    out: list[str] = []
    out.extend(parts)
    for i in range(len(parts) - 1):
        pair = clean(parts[i] + " " + parts[i + 1])
        if len(pair) <= MAX_EVIDENCE:
            out.append(pair)
    return out


def qa_records(repo: Path) -> Iterable[dict[str, str]]:
    for xml_path in sorted(repo.rglob("*.xml")):
        try:
            root = ET.parse(xml_path).getroot()
        except Exception:
            continue
        source = clean(root.attrib.get("source", ""))
        url = clean(root.attrib.get("url", ""))
        focus = clean(root.findtext("Focus"))
        collection = xml_path.parent.name
        pairs = root.find("QAPairs")
        if pairs is None:
            continue
        for pair in pairs.findall("QAPair"):
            qnode = pair.find("Question")
            anode = pair.find("Answer")
            question = clean("".join(qnode.itertext()) if qnode is not None else "")
            answer = clean("".join(anode.itertext()) if anode is not None else "")
            if not question or len(answer) < MIN_EVIDENCE:
                continue
            qtype = clean(qnode.attrib.get("qtype", "") if qnode is not None else "")
            yield {
                "question": question,
                "answer": answer,
                "source": source,
                "url": url,
                "collection": collection,
                "qtype": qtype,
                "focus": focus,
            }


def make_candidates(qa: dict[str, str]) -> Iterable[tuple[str, str, str]]:
    q, answer, focus, qtype = qa["question"], qa["answer"], qa["focus"], qa["qtype"]
    # Full answer: canonical QA unit.
    yield q, answer[:MAX_EVIDENCE], "qa"
    chunks = sentence_chunks(answer)
    for idx, evidence in enumerate(chunks):
        yield q, evidence[:MAX_EVIDENCE], "evidence"
        # Contextual retrieval aliases point to the exact same source evidence.
        if focus:
            yield f"{focus} {qtype}".strip(), evidence[:MAX_EVIDENCE], "focus_type"
        if qtype:
            yield f"{qtype}: {q}", evidence[:MAX_EVIDENCE], "type_question"
        if idx < 2 and focus:
            yield f"medical information about {focus}", evidence[:MAX_EVIDENCE], "focus_info"


def build(repo: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    db = sqlite3.connect(output)
    db.execute("PRAGMA journal_mode=OFF")
    db.execute("PRAGMA synchronous=OFF")
    db.execute("PRAGMA temp_store=MEMORY")
    db.execute("PRAGMA page_size=4096")
    db.executescript(
        """
        CREATE TABLE knowledge(
          id INTEGER PRIMARY KEY,
          question TEXT NOT NULL,
          evidence TEXT NOT NULL,
          source TEXT NOT NULL,
          source_url TEXT NOT NULL,
          collection TEXT NOT NULL,
          qtype TEXT NOT NULL,
          focus TEXT NOT NULL,
          unit_kind TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE knowledge_fts USING fts4(
          question, evidence, focus, qtype, content='knowledge', tokenize=unicode61
        );
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """
    )
    insert_k = "INSERT INTO knowledge(question,evidence,source,source_url,collection,qtype,focus,unit_kind) VALUES(?,?,?,?,?,?,?,?)"
    insert_f = "INSERT INTO knowledge_fts(docid,question,evidence,focus,qtype) VALUES(?,?,?,?,?)"
    seen: set[bytes] = set()
    source_qa_count = 0
    answer_chars = 0
    units = 0
    batch_k: list[tuple[str, ...]] = []

    for qa in qa_records(repo):
        source_qa_count += 1
        answer_chars += len(qa["answer"])
        for question, evidence, kind in make_candidates(qa):
            question = clean(question)
            evidence = clean(evidence)
            if len(evidence) < MIN_EVIDENCE:
                continue
            digest = hashlib.blake2b((norm(question) + "\n" + norm(evidence)).encode("utf-8"), digest_size=16).digest()
            if digest in seen:
                continue
            seen.add(digest)
            batch_k.append((question, evidence, qa["source"], qa["url"], qa["collection"], qa["qtype"], qa["focus"], kind))
            if len(batch_k) >= 1000 or units + len(batch_k) >= TARGET:
                for row in batch_k:
                    cur = db.execute(insert_k, row)
                    docid = cur.lastrowid
                    db.execute(insert_f, (docid, row[0], row[1], row[6], row[5]))
                units += len(batch_k)
                batch_k.clear()
                db.commit()
            if units >= TARGET:
                break
        if units >= TARGET:
            break

    if batch_k and units < TARGET:
        for row in batch_k[: TARGET - units]:
            cur = db.execute(insert_k, row)
            docid = cur.lastrowid
            db.execute(insert_f, (docid, row[0], row[1], row[6], row[5]))
            units += 1
        db.commit()

    if units != TARGET:
        raise SystemExit(f"expected exactly {TARGET} units, built {units}")

    metadata = {
        "knowledge_count": str(units),
        "source_qa_with_answers_seen": str(source_qa_count),
        "source_answer_characters_seen": str(answer_chars),
        "dataset": "MedQuAD",
        "dataset_repository": "abachaa/MedQuAD",
        "dataset_license": "CC BY 4.0",
        "build_method": "canonical QA plus source-grounded sentence and adjacent-sentence evidence units; no synthetic medical claims",
        "schema_version": "1",
    }
    db.executemany("INSERT INTO metadata(key,value) VALUES(?,?)", metadata.items())
    db.execute("ANALYZE")
    db.execute("VACUUM")
    db.close()

    sha = hashlib.sha256(output.read_bytes()).hexdigest()
    report = {**metadata, "db_bytes": output.stat().st_size, "sha256": sha}
    output.with_suffix(output.suffix + ".metadata.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_medical_knowledge.py MEDQUAD_REPO OUTPUT_DB")
    build(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
