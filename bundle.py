#!/usr/bin/env python3
"""
bundle.py — makes pdf-diff-viewer.html fully self-contained (no internet required).

Usage:
    python bundle.py

What it does:
    1. Downloads pdf.min.js and pdf.worker.min.js from cdnjs (one-time only)
    2. Inlines pdf.min.js directly into the HTML <script> block
    3. Inlines pdf.worker.min.js as a Blob URL so the Web Worker works
       without a server (this is the key trick that makes file:// work)
    4. Writes the result to pdf-diff-viewer-offline.html

Run this script ONCE on a machine with internet access, then copy
pdf-diff-viewer-offline.html anywhere — it works with no internet,
no server, just double-click in any browser.
"""

import urllib.request
import re
import sys
import os

PDFJS_VERSION  = "3.11.174"
PDFJS_URL      = f"https://cdnjs.cloudflare.com/ajax/libs/pdf.js/{PDFJS_VERSION}/pdf.min.js"
WORKER_URL     = f"https://cdnjs.cloudflare.com/ajax/libs/pdf.js/{PDFJS_VERSION}/pdf.worker.min.js"

INPUT_HTML     = "pdf-diff-viewer-latest.html"
OUTPUT_HTML    = "pdf-diff-viewer-offline.html"

PDFJS_MARKER_START = "/* ===== PDF.JS INLINE - DO NOT EDIT THIS LINE (used by bundle.py) ===== */"
PDFJS_MARKER_END   = "/* ===== END PDF.JS INLINE ===== */"
WORKER_PLACEHOLDER = "'/* WORKER_BLOB_URL */'"


def download(url, label):
    print(f"  Downloading {label}...", end=" ", flush=True)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read().decode("utf-8")
        print(f"OK ({len(data):,} chars)")
        return data
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)


def main():
    # ── Check input file exists ───────────────────────────────────────────────
    if not os.path.exists(INPUT_HTML):
        print(f"ERROR: {INPUT_HTML} not found in current directory.")
        print(f"       Run this script from the same folder as {INPUT_HTML}.")
        sys.exit(1)

    print(f"\nPDF Diff Viewer — Offline Bundler")
    print(f"==================================")

    # ── Download PDF.js files ─────────────────────────────────────────────────
    pdfjs_src  = download(PDFJS_URL,  "pdf.min.js")
    worker_src = download(WORKER_URL, "pdf.worker.min.js")

    # ── Read HTML template ────────────────────────────────────────────────────
    with open(INPUT_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    # ── Inline pdf.min.js between the marker comments ────────────────────────
    if PDFJS_MARKER_START not in html:
        print(f"\nERROR: Could not find PDF.js placeholder in {INPUT_HTML}.")
        print(f"       Make sure you're using the correct template file.")
        sys.exit(1)

    # Replace everything between (and including) the two markers.
    # Use a lambda so backslashes in the JS source are never interpreted
    # as regex escape sequences (e.g. \u, \n inside pdf.min.js).
    pattern = re.escape(PDFJS_MARKER_START) + r".*?" + re.escape(PDFJS_MARKER_END)
    inline_block = f"{PDFJS_MARKER_START}\n{pdfjs_src}\n{PDFJS_MARKER_END}"
    html = re.sub(pattern, lambda _: inline_block, html, flags=re.DOTALL)

    # ── Inline pdf.worker.min.js as a Blob URL ────────────────────────────────
    # This is the key trick: instead of loading the worker from a file URL
    # (which browsers block), we encode it as a Blob and create an object URL.
    # The worker JS is stored in a <script type="text/js-worker"> tag and
    # converted to a Blob URL at runtime — works with file:// in all browsers.
    #
    # We inject a small bootstrap snippet that creates the Blob URL and assigns
    # it to pdfjsLib.GlobalWorkerOptions.workerSrc before any PDF is loaded.

    worker_escaped = worker_src.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

    blob_bootstrap = (
        "(function(){\n"
        "  var workerCode = `" + worker_escaped + "`;\n"
        "  var blob = new Blob([workerCode], {type: 'application/javascript'});\n"
        "  var blobUrl = URL.createObjectURL(blob);\n"
        "  // Replace placeholder — pdfjsLib is already defined above this point\n"
        "  pdfjsLib.GlobalWorkerOptions.workerSrc = blobUrl;\n"
        "})()"
    )

    if WORKER_PLACEHOLDER not in html:
        print(f"\nERROR: Could not find worker placeholder in {INPUT_HTML}.")
        sys.exit(1)

    # Replace the entire workerSrc assignment line with the blob bootstrap
    html = html.replace(
        f"pdfjsLib.GlobalWorkerOptions.workerSrc = {WORKER_PLACEHOLDER};",
        blob_bootstrap + ";"
    )

    # ── Write output ──────────────────────────────────────────────────────────
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUTPUT_HTML) / 1024
    print(f"\n  Written: {OUTPUT_HTML} ({size_kb:,.0f} KB)")
    print(f"\n✓ Done! Open {OUTPUT_HTML} directly in any browser.")
    print(f"  No internet connection or server required.\n")


if __name__ == "__main__":
    main()
