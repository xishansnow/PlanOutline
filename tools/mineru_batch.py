#!/usr/bin/env python3
"""批量提交本地文件到 MinerU v4 精准解析 API，轮询任务并落盘解析结果。

接口流程（对应 https://mineru.net/apiManage/docs 的「精准解析 API」）：
  1. POST /api/v4/file-urls/batch                   申请上传链接（单次 ≤50 个，链接 24 小时有效）
  2. PUT  <file_urls[i]>                            上传文件（不要带 Content-Type），传完系统自动提交解析
  3. GET  /api/v4/extract-results/batch/{batch_id}  轮询到全部 done/failed
  4. 下载 full_zip_url 解包：full.md、*_content_list.json、layout.json、images/ 等

Token 只从环境变量 MINERU_API_KEY 读取，不写入磁盘、不打印。

用法示例：
    MINERU_API_KEY=... python3 tools/mineru_batch.py standard --out standard/mineru
    python3 tools/mineru_batch.py standard --only 40087 --model vlm
    python3 tools/mineru_batch.py standard --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import requests

API_BASE = "https://mineru.net/api/v4"
BATCH_ENDPOINT = f"{API_BASE}/file-urls/batch"
RESULT_ENDPOINT = f"{API_BASE}/extract-results/batch"

SUPPORTED_SUFFIXES = {
    ".pdf", ".png", ".jpg", ".jpeg", ".jp2", ".webp", ".gif", ".bmp",
    ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
}
MAX_BYTES = 200 * 1024 * 1024
MAX_PAGES = 200
BATCH_LIMIT = 50
FINAL_STATES = {"done", "failed"}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def die(msg: str) -> None:
    sys.exit(f"错误：{msg}")


def make_data_id(index: int, path: Path) -> str:
    """data_id 只允许 [A-Za-z0-9_.-] 且不超过 128 字符，中文名需转写。"""
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", path.stem).strip("-.") or "file"
    digest = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:8]
    return f"{index:02d}-{stem[:80]}-{digest}"


def pdf_page_count(path: Path) -> int | None:
    if path.suffix.lower() != ".pdf" or not shutil.which("pdfinfo"):
        return None
    try:
        proc = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, timeout=60)
    except Exception:
        return None
    match = re.search(r"^Pages:\s+(\d+)", proc.stdout, re.M)
    return int(match.group(1)) if match else None


def collect(paths: list[str], only: str | None, recursive: bool) -> list[Path]:
    found: list[Path] = []
    for raw in paths:
        path = Path(raw).expanduser()
        if path.is_dir():
            walker = path.rglob("*") if recursive else path.glob("*")
            found.extend(sorted(p for p in walker if p.is_file()))
        elif path.is_file():
            found.append(path)
        else:
            die(f"路径不存在：{path}")
    seen: set[str] = set()
    result: list[Path] = []
    for path in found:
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if only and only not in path.name:
            continue
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def request_with_retry(session: requests.Session, method: str, url: str, *, tries: int = 4, **kwargs):
    """对 429 / 5xx 做退避重试，尊重 Retry-After。"""
    last: object = None
    for attempt in range(1, tries + 1):
        try:
            resp = session.request(method, url, **kwargs)
        except requests.RequestException as exc:
            last = exc
            if attempt == tries:
                raise
            time.sleep(min(2 ** attempt, 30))
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = float(resp.headers.get("Retry-After") or 0) or min(2 ** attempt, 30)
            log(f"HTTP {resp.status_code}，{wait:.0f}s 后重试（{attempt}/{tries}）")
            time.sleep(wait)
            last = RuntimeError(f"HTTP {resp.status_code}")
            continue
        return resp
    raise RuntimeError(f"请求失败：{url}（{last}）")


def submit_batch(session: requests.Session, files: list[dict], options: dict) -> tuple[str, list[str]]:
    payload = {
        "enable_formula": options["enable_formula"],
        "enable_table": options["enable_table"],
        "language": options["language"],
        "model_version": options["model_version"],
        "files": [
            {"name": item["name"], "data_id": item["data_id"], "is_ocr": options["is_ocr"]}
            for item in files
        ],
    }
    resp = request_with_retry(session, "POST", BATCH_ENDPOINT, json=payload, timeout=60)
    if resp.status_code != 200:
        die(f"申请上传链接失败：HTTP {resp.status_code} {resp.text[:300]}")
    body = resp.json()
    if body.get("code") != 0:
        die(f"申请上传链接失败：code={body.get('code')} msg={body.get('msg')} trace={body.get('trace_id')}")
    data = body["data"]
    urls = data["file_urls"]
    if len(urls) != len(files):
        die(f"返回的上传链接数量（{len(urls)}）与文件数量（{len(files)}）不一致")
    return data["batch_id"], urls


def upload_files(session: requests.Session, files: list[dict], urls: list[str]) -> None:
    for item, url in zip(files, urls):
        path: Path = item["path"]
        size_mb = path.stat().st_size / 1024 / 1024
        with path.open("rb") as handle:
            resp = request_with_retry(session, "PUT", url, data=handle, timeout=900)
        if resp.status_code != 200:
            die(f"上传失败：{path.name} HTTP {resp.status_code} {resp.text[:200]}")
        log(f"已上传 {path.name}（{size_mb:.1f} MB）")


def poll_batch(session: requests.Session, batch_id: str, names: dict[str, str],
               interval: float, overall_timeout: float) -> list[dict]:
    deadline = time.time() + overall_timeout
    last_seen: dict[str, str] = {}
    results: dict[str, dict] = {}
    while True:
        resp = request_with_retry(session, "GET", f"{RESULT_ENDPOINT}/{batch_id}", timeout=60)
        if resp.status_code != 200:
            die(f"查询任务失败：HTTP {resp.status_code} {resp.text[:300]}")
        body = resp.json()
        if body.get("code") != 0:
            die(f"查询任务失败：code={body.get('code')} msg={body.get('msg')} trace={body.get('trace_id')}")
        items = body["data"].get("extract_result") or []
        for item in items:
            key = item.get("data_id") or item.get("file_name") or ""
            label = names.get(key) or item.get("file_name") or key
            results[key] = item
            state = item.get("state", "?")
            progress = item.get("extract_progress") or {}
            if state == "running" and progress:
                state = f"running {progress.get('extracted_pages', '?')}/{progress.get('total_pages', '?')} 页"
            if last_seen.get(key) != state:
                suffix = f"  ↳ {item['err_msg']}" if item.get("err_msg") else ""
                log(f"{label}: {state}{suffix}")
                last_seen[key] = state
        if items and all(item.get("state") in FINAL_STATES for item in items):
            return list(results.values())
        if time.time() > deadline:
            log(f"等待超时（{overall_timeout:.0f}s），返回当前结果供人工判断")
            return list(results.values())
        time.sleep(interval)


def safe_extract(zip_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if not str((dest / member).resolve()).startswith(str(root)):
                die(f"压缩包内含越界路径：{member}")
        archive.extractall(dest)


def download_result(session: requests.Session, url: str, dest_dir: Path) -> None:
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp_zip = dest_dir.parent / (dest_dir.name + ".zip")
    resp = request_with_retry(session, "GET", url, stream=True, timeout=600)
    if resp.status_code != 200:
        die(f"下载结果失败：HTTP {resp.status_code}")
    with tmp_zip.open("wb") as handle:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            if chunk:
                handle.write(chunk)
    safe_extract(tmp_zip, dest_dir)
    tmp_zip.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="批量调用 MinerU v4 精准解析 API")
    parser.add_argument("paths", nargs="*", default=["standard"], help="文件或目录（默认 standard）")
    parser.add_argument("--out", default="standard/mineru", help="输出目录（默认 standard/mineru）")
    parser.add_argument("--model", dest="model_version", default="vlm",
                        choices=["pipeline", "vlm", "MinerU-HTML"], help="模型版本（默认 vlm）")
    parser.add_argument("--language", default="ch", help="解析语言（默认 ch）")
    parser.add_argument("--ocr", dest="is_ocr", action="store_true", help="强制开启 OCR")
    parser.add_argument("--no-table", dest="enable_table", action="store_false", help="关闭表格识别")
    parser.add_argument("--no-formula", dest="enable_formula", action="store_false", help="关闭公式识别")
    parser.add_argument("--only", default=None, help="只处理文件名包含该子串的文件")
    parser.add_argument("--recursive", action="store_true", help="目录内递归查找")
    parser.add_argument("--interval", type=float, default=10.0, help="轮询间隔秒数（默认 10）")
    parser.add_argument("--overall-timeout", type=float, default=1800.0, help="总等待上限秒数（默认 1800）")
    parser.add_argument("--force", action="store_true", help="已有结果也重新解析")
    parser.add_argument("--dry-run", action="store_true", help="只列出将要提交的文件")
    args = parser.parse_args()

    out_dir = Path(args.out).expanduser()
    files = collect(args.paths or ["standard"], args.only, args.recursive)
    if not files:
        die("没有找到可处理的文件")

    todo: list[dict] = []
    for index, path in enumerate(files, start=1):
        size = path.stat().st_size
        pages = pdf_page_count(path)
        if size > MAX_BYTES:
            log(f"跳过 {path.name}：{size / 1024 / 1024:.1f} MB 超过 200 MB 上限")
            continue
        if pages is not None and pages > MAX_PAGES:
            log(f"跳过 {path.name}：{pages} 页超过 200 页上限")
            continue
        dest = out_dir / path.stem
        if (dest / "full.md").exists() and not args.force:
            log(f"跳过 {path.name}：{dest / 'full.md'} 已存在（加 --force 可重跑）")
            continue
        todo.append({
            "path": path,
            "name": path.name,
            "data_id": make_data_id(index, path),
            "size": size,
            "pages": pages,
        })

    if not todo:
        log("没有需要提交的文件")
        return 0

    total_mb = sum(item["size"] for item in todo) / 1024 / 1024
    log(f"待提交 {len(todo)} 个文件，合计 {total_mb:.1f} MB，模型 {args.model_version}")
    for item in todo:
        pages = f"{item['pages']} 页" if item["pages"] else "页数未知"
        log(f"  - {item['name']}（{item['size'] / 1024 / 1024:.1f} MB，{pages}）")
    if args.dry_run:
        return 0

    token = os.environ.get("MINERU_API_KEY", "").strip()
    if not token:
        die("环境变量 MINERU_API_KEY 未设置")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "Accept": "*/*"})
    session.headers.pop("Content-Type", None)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    names = {item["data_id"]: item["name"] for item in todo}
    by_name = {item["name"]: item for item in todo}
    options = {
        "enable_formula": args.enable_formula,
        "enable_table": args.enable_table,
        "language": args.language,
        "model_version": args.model_version,
        "is_ocr": args.is_ocr,
    }

    batches: list[tuple[str, list[dict]]] = []
    for start in range(0, len(todo), BATCH_LIMIT):
        chunk = todo[start:start + BATCH_LIMIT]
        batch_id, urls = submit_batch(session, chunk, options)
        log(f"批任务已创建 batch_id={batch_id}（{len(chunk)} 个文件）")
        upload_files(session, chunk, urls)
        batches.append((batch_id, chunk))

    failures = 0
    for batch_id, _chunk in batches:
        results = poll_batch(session, batch_id, names, args.interval, args.overall_timeout)
        for item in results:
            key = item.get("data_id") or item.get("file_name") or ""
            source = by_name.get(names.get(key, "")) or by_name.get(item.get("file_name") or "")
            record = manifest.setdefault(key, {})
            record.update({
                "batch_id": batch_id,
                "file_name": item.get("file_name"),
                "source": str(source["path"]) if source else None,
                "state": item.get("state"),
                "full_zip_url": item.get("full_zip_url"),
                "err_msg": item.get("err_msg"),
            })
            if item.get("state") != "done" or not source:
                failures += 1
                if not source:
                    log(f"无法把结果 {item.get('file_name')} 对应回源文件")
                continue
            dest = out_dir / source["path"].stem
            download_result(session, item["full_zip_url"], dest)
            md = dest / "full.md"
            record["output_dir"] = str(dest)
            record["markdown"] = str(md) if md.exists() else None
            log(f"已落盘 {source['name']} → {md if md.exists() else dest}")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    done = sum(1 for r in manifest.values() if r.get("state") == "done")
    log(f"完成：成功 {done}，失败 {failures}；清单 {manifest_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
