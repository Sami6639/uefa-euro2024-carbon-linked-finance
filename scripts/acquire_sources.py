#!/usr/bin/env python3
"""Acquire the catalogued public sources. Never overwrite archived bytes by default.

Run with --refresh to place newly retrieved bytes in raw/refresh_TIMESTAMP/.
Only Python's standard library is used. Website changes do not alter the reviewed
dataset, which is a versioned transcription of the archived source documents.
"""
from pathlib import Path
import argparse, datetime as dt, hashlib, json, urllib.request, concurrent.futures

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    out = DATA / "raw"
    if args.refresh:
        out /= "refresh_" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((DATA / "source_catalog.json").read_text())
    def acquire(s):
        path = out / (s["source_id"] + "." + s["extension"])
        if path.exists():
            return {"source_id": s["source_id"], "status": "archived_bytes_preserved"}
        req = urllib.request.Request(s["url"], headers={"User-Agent":"EURO2024 reproducible research source acquisition"})
        with urllib.request.urlopen(req, timeout=90) as response:
            blob = response.read()
            if s["extension"] == "pdf" and not blob.startswith(b"%PDF"):
                raise ValueError("The requested PDF did not return PDF bytes: " + s["source_id"])
            path.write_bytes(blob)
            receipt = dict(source_id=s["source_id"], requested_url=s["url"],
                resolved_url=response.url, retrieved_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                status=response.status, mime_type=response.headers.get("Content-Type"),
                bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest(),
                local_path=str(path.relative_to(ROOT)),
                http_last_modified=response.headers.get("Last-Modified", ""))
            (out / (s["source_id"]+".retrieval.json")).write_text(json.dumps(receipt,indent=2))
            return receipt
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(acquire, catalog):
            print(json.dumps(result))

if __name__ == "__main__":
    main()
