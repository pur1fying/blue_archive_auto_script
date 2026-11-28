"""Source-only OCR inventory. Never imports game modules or executes a task."""
import argparse
import ast
from collections import Counter
import html
import json
import os
from pathlib import Path
import re

METHODS = {"get_region_res", "get_region_raw_res", "get_region_pure_english",
           "get_region_pure_chinese", "recognize_int", "recognize_number", "ocr_for_single_line", "ocr"}
SKIP = {".git", ".worktrees", "__pycache__", "node_modules", "build", "dist", "output", "output_images", ".pyside6_android_deploy"}
COORDINATE_HELPERS = {"swipe_search_target_str", "get_item_holding_quantity", "get_item_selected_quantity",
                      "get_item_holding_quantity_region", "get_item_selected_quantity_region"}


def python_files(root):
    # Walk the working tree, not Git's allowlist: local service files may be ignored.
    for directory, folders, files in os.walk(root):
        folders[:] = sorted(f for f in folders if f not in SKIP and not f.startswith((".venv", "venv")))
        for name in sorted(files):
            if name.endswith(".py"):
                yield Path(directory) / name


def expression(node):
    return ast.unparse(node) if node is not None else ""


def line_of(node):
    return getattr(node, "lineno", getattr(getattr(node, "iter", None), "lineno", 0))


def ancestor_functions(node, parents):
    result = []
    while node in parents:
        node = parents[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.append(node)
    return result


def conditions(node, parents):
    result = []
    while node in parents:
        parent = parents[node]
        if isinstance(parent, ast.If):
            test = expression(parent.test)
            result.append(test if node in parent.body else "not (" + test + ")")
        node = parent
    return list(reversed(result))


def bindings_for(node, seeds, parents):
    functions = ancestor_functions(node, parents)
    scopes = functions or [next(n for n in [node] if n is not None)]
    candidates = []
    for scope in scopes:
        for item in ast.walk(scope):
            if line_of(item) > node.lineno:
                continue
            if isinstance(item, ast.Assign):
                targets = item.targets
                value = item.value
            elif isinstance(item, (ast.AnnAssign, ast.AugAssign)):
                targets, value = [item.target], item.value
            elif isinstance(item, (ast.For, ast.comprehension)):
                targets, value = [item.target], item.iter
            else:
                continue
            if value is None:
                continue
            names = {n.id for target in targets for n in ast.walk(target) if isinstance(n, ast.Name)}
            candidates.append((item, names, value))
    needed = {n.id for seed in seeds if seed is not None for n in ast.walk(seed) if isinstance(n, ast.Name)}
    picked = {}
    while True:
        old = len(picked)
        for item, names, value in candidates:
            if names & needed:
                picked[id(item)] = (item, names, value)
                needed |= {n.id for n in ast.walk(value) if isinstance(n, ast.Name)}
        if old == len(picked):
            break
    output = []
    for item, names, value in sorted(picked.values(), key=lambda row: line_of(row[0])):
        try:
            literal = ast.literal_eval(value)
        except (ValueError, TypeError):
            literal = None
        output.append({"line": line_of(item), "names": sorted(names), "expression": expression(value),
                       "literal": literal, "conditions": conditions(item, parents)})
    return output


def argument(call, name, position):
    return next((kw.value for kw in call.keywords if kw.arg == name),
                call.args[position] if len(call.args) > position else None)


def scan(root):
    root = Path(root)
    records, helpers, definitions, failures, references, helper_definitions = [], [], [], [], [], []
    count = 0
    for path in python_files(root):
        count += 1
        relative = path.relative_to(root).as_posix()
        try:
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source, filename=relative)
        except (UnicodeError, SyntaxError) as exc:
            failures.append({"file": relative, "error": str(exc)})
            continue
        if re.search(r'ocr|recognize_int|recognize_number', source, re.I):
            references.append(relative)
        parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in COORDINATE_HELPERS and node.name.endswith("_region"):
                helper_definitions.append({"file": relative, "line": node.lineno, "function": node.name,
                                           "source": ast.get_source_segment(source, node)})
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in METHODS:
                definitions.append({"file": relative, "line": node.lineno, "name": node.name,
                                    "parameters": expression(node.args)})
            if not isinstance(node, ast.Call):
                continue
            method = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            functions = ancestor_functions(node, parents)
            function = ".".join(f.name for f in reversed(functions)) or "<module>"
            if method not in METHODS:
                if method in COORDINATE_HELPERS or (method in {"read", "read_text"} and relative.startswith("service/plugins/hoard_")):
                    helpers.append({"file": relative, "line": node.lineno, "function": function,
                                    "call": expression(node), "bindings": bindings_for(node, list(node.args) + [k.value for k in node.keywords], parents)})
                continue
            if relative.startswith(("tests/", "develop_tools/", "docs/")) or '.example.' in relative:
                category = "test_or_example"
            elif relative.startswith("core/ocr/") or relative == "service/android_ocr_client.py":
                category = "ocr_engine_or_transport"
            else:
                category = "game_ocr_call"
            region = argument(node, "origin_image", 2 if method == "ocr_for_single_line" else 1) if method in {"ocr", "ocr_for_single_line"} else argument(node, "region", 1)
            label = (None if method in {"get_region_raw_res", "recognize_number", "ocr"}
                     else argument(node, "log_info", 3 if method == "get_region_res" else 1 if method == "ocr_for_single_line" else 2))
            record = {"id": f"{relative}:{node.lineno}", "file": relative, "line": node.lineno,
                      "end_line": node.end_lineno, "function": function, "method": method, "category": category,
                      "label_expression": expression(label), "region_expression": expression(region),
                      "call": expression(node), "conditions": conditions(node, parents),
                      "coordinate_bindings": bindings_for(node, [region], parents), "findings": []}
            if category == "game_ocr_call":
                if method == "recognize_number":
                    record["findings"].append("Legacy recognize_number API is absent from the current Baas_ocr class")
                if method == "get_region_res" and node.args and expression(node.args[0]).endswith("latest_img_array"):
                    record["findings"].append("An image array is passed where current get_region_res requires a BAAS instance")
                if method == "get_region_raw_res":
                    record["findings"].append("Check the legacy caller: current raw OCR returns response.text, not a list of text/position dictionaries")
                if method == "ocr_for_single_line" and "_ocr_crop(" in expression(region):
                    record["findings"].append("Preprocessing may detach crop coordinates; transformed inputs need explicit provenance for full-frame annotation")
            records.append(record)
    records.sort(key=lambda r: (r["file"], r["line"]))
    return {"version": 1, "python_files_scanned": count, "scope": "Current checkout, including Git-ignored source files. No game modules are imported.",
            "excluded_directories": sorted(SKIP) + [".venv*", "venv*"], "parse_errors": failures,
            "categories": dict(Counter(r["category"] for r in records)), "calls": records,
            "coordinate_helpers": helpers, "coordinate_helper_definitions": helper_definitions,
            "interface_definitions": definitions, "ocr_reference_files": references}


def write_inventory(directory, inventory, cases=()):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    observed = []
    for case in cases:
        for group in case.get("ocr_evidence", {}).get("groups", []):
            for call in group.get("calls", []):
                observed.append({"case_id": case["case_id"], "image": group["annotated"], **call})
    data = dict(inventory)
    records = []
    for record in inventory["calls"]:
        record = dict(record)
        record["observations"] = [c for c in observed if c.get("source", {}).get("file") == record["file"]
                                   and record["line"] <= c.get("source", {}).get("line", -1) <= record["end_line"]]
        record["coverage"] = "observed" if record["observations"] else "not_observed"
        records.append(record)
    data["calls"] = records
    temporary = directory / "ocr-inventory.json.tmp"
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temporary.replace(directory / "ocr-inventory.json")
    esc = lambda value: html.escape(str(value), quote=True)
    sections = []
    for r in records:
        if r["category"] != "game_ocr_call":
            continue
        bindings = "\n".join(f"L{b['line']} {','.join(b['names'])} = {b['expression']}" + (" | when " + ' AND '.join(b['conditions']) if b['conditions'] else '') for b in r["coordinate_bindings"])
        images = " ".join(f'<a href="{esc(c["image"])}">Observed frame</a>' for c in r["observations"])
        sections.append(f'<details open><summary>{esc(r["id"])} · {esc(r["function"])} · {esc(r["coverage"])}</summary><p>{esc(r["label_expression"])}</p><pre>{esc(r["call"])}</pre><pre>{esc(bindings)}</pre><p class="finding">{esc("; ".join(r["findings"]))}</p>{images}</details>')
    helpers = "\n\n".join(f"{h['file']}:{h['line']} {h['function']}\n{h['call']}\n" + "\n".join(f"L{b['line']} {','.join(b['names'])} = {b['expression']}" for b in h['bindings']) for h in data['coordinate_helpers'])
    helpers += "\n\n" + "\n\n".join(f"{h['file']}:{h['line']}\n{h['source']}" for h in data['coordinate_helper_definitions'])
    errors = json.dumps(data['parse_errors'], ensure_ascii=False)
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Project OCR Inventory</title>
<style>body{{font:15px system-ui;max-width:1250px;margin:30px auto;padding:0 20px;color:#25314a}}details{{border:1px solid #ccd4de;border-radius:8px;margin:12px 0;padding:12px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f6fa;padding:12px}}summary{{font-weight:600}}.finding{{color:#a33c00}}</style>
<h1>Project OCR Inventory</h1><p>{data['python_files_scanned']} Python files scanned. {esc(data['categories'])}</p>
<p>Every game OCR call site is listed, including unexecuted branches and historical APIs. One call site may produce multiple server-specific or dynamic regions. Observed does not certify all server/region variants or OCR correctness.</p>
<p>Git ignore rules are not used for source discovery. Parse errors: {esc(errors)}</p><p><a href="ocr-inventory.json">Complete inventory, interfaces, helpers and scan scope</a></p>
{''.join(sections)}<details><summary>Indirect coordinate producers and callback regions</summary><pre>{esc(helpers)}</pre></details></html>'''
    (directory / "ocr-inventory.html").write_text(page, encoding="utf-8")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/test_runs/ocr-inventory"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    data = write_inventory(args.output, scan(root))
    print(json.dumps({"files": data["python_files_scanned"], "categories": data["categories"], "parse_errors": data["parse_errors"]}))
    print("Inventory: " + str((args.output / 'ocr-inventory.html').resolve()))


if __name__ == "__main__":
    main()
