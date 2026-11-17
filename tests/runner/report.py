import html
import json
import os
from collections import Counter
from pathlib import Path
from urllib.parse import quote
from tests.support.serialization import json_default

LABELS = {"completed": "Completed", "failed": "Failed", "timeout": "Timed out", "cancelled": "Cancelled",
          "unexecuted": "Not executed", "blocked": "Blocked", "not_run": "Not run", "running": "Running"}
LEGACY_REVIEW = {"待复核": "pending", "通过": "passed", "不通过": "failed"}


def normalize_reviews(data):
    for case in data.get("cases", []):
        value = case.get("review", "pending")
        case["review"] = LEGACY_REVIEW.get(value, value)


def write_report(directory, data):
    normalize_reviews(data)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / "result.json.tmp"
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=json_default), encoding="utf-8")
    os.replace(temporary, directory / "result.json")
    esc = lambda x: html.escape(str(x), quote=True)
    cards = []
    totals = Counter(c["status"] for c in data.get("cases", []))
    summary = " | ".join(f"{LABELS.get(k, k)}: {v}" for k, v in sorted(totals.items()))
    ocr_summaries = [c.get("ocr_evidence", {}) for c in data.get("cases", [])]
    ocr_totals = {"calls": sum(o.get("calls", 0) for o in ocr_summaries),
                  "frames": sum(len(o.get("groups", [])) for o in ocr_summaries),
                  "missing": sum(o.get("missing", 0) for o in ocr_summaries)}
    startup = '<a href="startup.jsonl">Service initialization log</a>' if data.get("startup_log") else ""
    inventory_link = '<a href="ocr-inventory.html">Project-wide OCR call sites, coordinate variants and coverage</a>' if data.get("ocr_inventory") else ""
    changed = data.get("source_changed")
    changed = "Unknown" if changed is None else str(changed)
    for case in data.get("cases", []):
        links = []
        for event in case.get("evidence", []):
            path = event.get("image")
            if path:
                links.append(f'<a href="{quote(path, safe="/")}"><img loading="lazy" src="{quote(path, safe="/")}" alt="Screenshot">{esc(event.get("label", ""))}</a>')
        log = case.get("log")
        log_link = f'<a href="{quote(log, safe="/")}">View complete log</a>' if log else ""
        trace = case.get("nemu_trace")
        trace_link = f'<a href="{quote(trace, safe="/")}">Nemu capture and input diagnostics</a>' if trace else ""
        ocr = case.get("ocr_evidence", {})
        ocr_cards = []
        for group in ocr.get("groups", []):
            calls = group.get("calls", [])
            details = "\n".join(f"{c.get('label', '')}: {c.get('result', c.get('error', ''))} | region={c.get('requested_region') or c.get('source_region')}" for c in calls)
            image_path = quote(group["annotated"], safe="/")
            original_path = quote(group["original"], safe="/")
            resized = " (resized from source for 720p display)" if group.get("resized_for_display") else ""
            ocr_cards.append(f'<div><a href="{image_path}"><img loading="lazy" src="{image_path}" alt="OCR regions on a full 720p frame"></a><p><a href="{original_path}">Original screenshot</a>{resized}</p><pre>{esc(details)}</pre></div>')
        ocr_log = f'<a href="{quote(ocr["log"], safe="/")}">All OCR calls and source locations</a>' if ocr.get("log") else ""
        cards.append(f'''<section><h2>{esc(case['config_id'])} · {esc(case['task_id'])}</h2>
<p>Execution: <strong>{esc(LABELS.get(case['status'], case['status']))}</strong>　Functional review: {esc(case.get('review', 'pending'))}</p>
<p>{esc(case.get('reason', ''))}</p><p>{esc(case.get('started_at', ''))} → {esc(case.get('ended_at', ''))}</p>
<p>Missing evidence: {case.get('evidence_dropped', 0)}　{log_link}</p>
<p>Review note: {esc(case.get('review_note', ''))}</p>
<p>Observer note: {esc(case.get('operator_observation', ''))}</p>
<p>{trace_link} {esc(json.dumps(case.get('nemu_summary', {}))) if trace else ''}</p>
<details><summary>OCR regions: {esc(ocr.get('status', 'not_recorded'))}; calls: {ocr.get('calls', 0)}; missing: {ocr.get('missing', 0)}</summary>
<p>Regions used on the same source image are combined. These are observed calls, not a claim that every possible screen was tested. {ocr_log}</p>
<p>{esc('; '.join(ocr.get('issues', [])))}</p><div class="ocr-images">{''.join(ocr_cards)}</div></details>
<details><summary>Config changes during execution</summary><pre>{esc(json.dumps(case.get('config_changes', {}), ensure_ascii=False, indent=2, default=json_default))}</pre></details>
<div class="images">{''.join(links)}</div></section>''')
    body = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>BAAS Test Report</title>
<style>body{{font:16px system-ui;max-width:1120px;margin:32px auto;padding:0 20px;background:#f4f6fa;color:#202b3b}}section{{background:white;padding:20px;margin:18px 0;border-radius:12px}}h2{{font-size:20px}}.images{{display:flex;gap:12px;flex-wrap:wrap}}.images a{{width:240px;font-size:13px}}img{{width:100%;display:block}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}a{{color:#2259af}}</style>
<style>.ocr-images{{display:grid;gap:18px}}.ocr-images img{{max-width:1280px;width:100%}}.ocr-images>div{{border:1px solid #ccd4de;padding:10px;border-radius:8px}}</style>
<h1>BAAS Live Test Report</h1><p>{esc(data.get('run_id', ''))} · {esc(data.get('state', ''))}</p>
<p>{esc(summary)}</p>
<p>OCR region evidence: {ocr_totals['calls']} calls; {ocr_totals['frames']} source images; {ocr_totals['missing']} missing records. Open each task's OCR regions panel to compare annotations and original images.</p>
<p>{inventory_link}</p>
<p><strong>Completion does not imply functional correctness. Results remain pending until manually reviewed.</strong></p>
<p>Code version: {esc(data.get('source', {}).get('commit', 'unknown'))}; Uncommitted changes: {esc(data.get('source', {}).get('dirty', 'unknown'))}</p>
<p>{esc(data.get('error', ''))}</p><p><a href="host.log">Test host output and tracebacks</a>　{startup}　Source changed during execution: {esc(changed)}</p>
<details><summary>Original config snapshots (credentials redacted)</summary><pre>{esc(json.dumps(data.get('configs_before', {}), ensure_ascii=False, indent=2, default=json_default))}</pre></details>
{''.join(cards)}</html>'''
    temporary = directory / "report.html.tmp"
    temporary.write_text(body, encoding="utf-8")
    os.replace(temporary, directory / "report.html")


def review(directory):
    directory = Path(directory)
    data = json.loads((directory / "result.json").read_text(encoding="utf-8"))
    normalize_reviews(data)
    if data.get("state") == "running":
        raise ValueError("The batch is still running; review results cannot be edited")
    for case in data["cases"]:
        print(f"\n{case['case_id']} {case['config_id']} / {case['task_id']}: {LABELS.get(case['status'])}")
        if case["status"] != "completed":
            print("Only completed tasks can be marked as passed during manual review.")
            continue
        answer = input("Functional review: 1 pass, 2 fail, Enter keep the existing result: ").strip()
        if answer in {"1", "2"}:
            case["review"] = "passed" if answer == "1" else "failed"
            case["review_note"] = input("Note: ").strip()
    write_report(directory, data)
