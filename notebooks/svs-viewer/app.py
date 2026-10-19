"""Read-only SVS whole-slide image browser. Start with `pixi run viewer`.

Only *reads* .svs files under data_root (configs/svs_viewer.toml). Nothing in data_root is
ever written, moved or deleted. The only file this tool writes is its slide index cache
(index_file in the config, under the gitignored data/processed/). Case-level CSV/parquet
tables are read into memory by clinical.py.
"""

import argparse
import io
import json
import os
import re
import threading
import time
import tomllib
from collections import OrderedDict
from functools import lru_cache

import clinical
import openslide
from flask import Flask, abort, jsonify, request, send_file, send_from_directory
from openslide.deepzoom import DeepZoomGenerator

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_CONFIG = os.path.join(REPO_ROOT, "configs", "svs_viewer.toml")
TILE_SIZE = 254  # Deep Zoom tile edge in pixels; 254 + 2 * OVERLAP = 256
OVERLAP = 1

# filename like 2019-0654-B_HE_SLAA00498_M01210.044.svs  -> stain "HE"
NAME_RE = re.compile(r"^(?P<acc>[^_]+)_(?P<stain>.+?)_(?P<case>[A-Z]{4}\d{5})_")

app = Flask(__name__, static_folder=None)
config = {"data_root": "", "index_file": ""}  # filled by load_config()
index = {"files": [], "ready": False, "scanned": 0, "built": None}


# ---------------------------------------------------------------- config
def load_config(path):
    """Read the TOML config; relative paths are resolved from the repository root."""
    with open(path, "rb") as fh:
        cfg = tomllib.load(fh)

    cfg["data_root"] = os.path.realpath(cfg["data_root"])
    if not os.path.isabs(cfg["index_file"]):
        cfg["index_file"] = os.path.join(REPO_ROOT, cfg["index_file"])
    return cfg


# ---------------------------------------------------------------- indexing
def parse(rel, size):
    parts = rel.split("/")
    name = parts[-1]
    m = NAME_RE.match(name)
    stain = m.group("stain") if m else "(not in filename)"
    # IHC2019-151-22 -> IHC
    stain_group = (re.sub(r"[\d\-]+.*$", "", stain).strip("_") or stain) if m else stain
    return {
        "path": rel,
        "name": name,
        "country": parts[0] if len(parts) > 1 else "",
        "case": parts[-2] if len(parts) > 2 else "",
        "stain": stain,
        "stain_group": stain_group.upper(),
        "size": size,
    }


def _find_slides(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for f in filenames:
            if not f.lower().endswith(".svs"):
                continue

            full = os.path.join(dirpath, f)
            try:
                size = os.stat(full).st_size
            except OSError:
                continue
            files.append(parse(os.path.relpath(full, root), size))
            index["scanned"] = len(files)
    return sorted(files, key=lambda x: x["path"])


def _write_index(path, built, files):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as fh:
        json.dump({"built": built, "files": files}, fh)
    os.replace(path + ".tmp", path)


def scan():
    files = _find_slides(config["data_root"])
    index.update(files=files, ready=True, built=time.time())
    _write_index(config["index_file"], index["built"], files)


def load_index(rescan):
    path = config["index_file"]
    if rescan or not os.path.exists(path):
        threading.Thread(target=scan, daemon=True).start()
        return

    with open(path) as fh:
        d = json.load(fh)
    index.update(files=d["files"], ready=True, built=d["built"], scanned=len(d["files"]))


# ---------------------------------------------------------------- slides
def safe_path(rel):
    """Resolve a relative path and guarantee it is an .svs inside data_root."""
    root = config["data_root"]
    full = os.path.realpath(os.path.join(root, rel))
    if not full.startswith(root + os.sep) or not full.lower().endswith(".svs"):
        abort(404)
    if not os.path.isfile(full):
        abort(404)
    return full


class SlideCache:
    """Keeps the most recently used slides open (LRU)."""

    def __init__(self, n=16):
        self.n, self.d, self.lock = n, OrderedDict(), threading.Lock()

    def get(self, rel):
        full = safe_path(rel)
        with self.lock:
            if full in self.d:
                self.d.move_to_end(full)
                return self.d[full]

        slide = openslide.OpenSlide(full)  # opens read-only
        dz = DeepZoomGenerator(slide, tile_size=TILE_SIZE, overlap=OVERLAP, limit_bounds=True)
        entry = (slide, dz)

        with self.lock:
            self.d[full] = entry
            while len(self.d) > self.n:
                _, (old, _) = self.d.popitem(last=False)
                old.close()
        return entry


slides = SlideCache()


def img_response(img, fmt="jpeg", quality=85):
    buf = io.BytesIO()
    if fmt == "jpeg" and img.mode != "RGB":
        img = img.convert("RGB")
    img.save(buf, fmt, quality=quality)
    buf.seek(0)

    resp = send_file(buf, mimetype=f"image/{fmt}")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@lru_cache(maxsize=4096)
def thumb_bytes(rel, size):
    slide, _ = slides.get(rel)
    img = slide.get_thumbnail((size, size)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "jpeg", quality=80)
    return buf.getvalue()


# ---------------------------------------------------------------- pages
@app.route("/")
def home():
    return send_from_directory(HERE, "shell.html")


@app.route("/viewer")
def viewer_page():
    return send_from_directory(HERE, "index.html")


@app.route("/diagram")
def diagram():
    return send_from_directory(HERE, "diagram.html")


@app.route("/map")
def disease_map_page():
    return send_from_directory(HERE, "map.html")


# ---------------------------------------------------------------- index API
def enrich():
    """Attach organ / clinical-data flags to the index once the tables are loaded."""
    if clinical.state["ready"] and index["ready"] and not index.get("enriched"):
        for f in index["files"]:
            f.update(clinical.slide_meta(f["case"], f["name"]))
        index["enriched"] = True


def _count(files, key):
    counts = {}
    for f in files:
        counts[f[key]] = counts.get(f[key], 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def _filter_files(files, args):
    """Apply the slide-list filters from the query string."""
    data_filters = {
        "yes": lambda f: f.get("has_data"),
        "no": lambda f: not f.get("has_data"),
        "tacpos": lambda f: f.get("tac_pos"),
    }

    if args.get("country"):
        files = [f for f in files if f["country"] == args["country"]]
    if args.get("stain"):
        files = [f for f in files if f["stain_group"] == args["stain"]]
    if args.get("organ"):
        files = [f for f in files if f.get("organ") == args["organ"]]
    if args.get("data") in data_filters:
        files = [f for f in files if data_filters[args["data"]](f)]

    cause, measure = args.get("cause"), args.get("measure") or "uc"
    if cause and clinical.state["ready"]:
        files = [
            f
            for f in files
            if f.get("deid") and cause in (clinical.case_diseases(f["deid"], measure) or ())
        ]

    terms = args.get("q", "").lower().split()
    if terms:
        files = [
            f
            for f in files
            if all(t in (f["path"] + " " + f.get("organ", "")).lower() for t in terms)
        ]
    return files


@app.route("/api/status")
def status():
    return jsonify(
        ready=index["ready"],
        scanned=index["scanned"],
        built=index["built"],
        root=config["data_root"],
    )


@app.route("/api/rescan", methods=["POST"])
def rescan():
    if index["ready"]:
        index.update(ready=False, scanned=0)
        threading.Thread(target=scan, daemon=True).start()
    return jsonify(ok=True)


@app.route("/api/facets")
def facets():
    enrich()
    files, enriched = index["files"], bool(index.get("enriched"))
    return jsonify(
        countries=_count(files, "country"),
        stains=_count(files, "stain_group"),
        organs=_count(files, "organ") if enriched else [],
        clinical_ready=enriched,
        clinical_error=clinical.state["error"],
        with_data=sum(f.get("has_data", False) for f in files),
        total=len(files),
        cases=len({f["case"] for f in files}),
    )


@app.route("/api/files")
def list_files():
    offset = int(request.args.get("offset", 0))
    limit = min(int(request.args.get("limit", 200)), 1000)
    res = _filter_files(index["files"], request.args)
    return jsonify(total=len(res), items=res[offset : offset + limit])


# ---------------------------------------------------------------- clinical API
@app.route("/api/disease_map")
def disease_map_api():
    if not clinical.state["ready"]:
        return jsonify(ready=False, error=clinical.state["error"])

    measure = request.args.get("measure", "uc")
    if measure not in ("uc", "ic", "any", "tac"):
        abort(400)

    deids = None
    if request.args.get("scope") == "slides":
        cases = {f["case"] for f in index["files"]}
        study2deid = clinical.D["study2deid"]
        deids = {study2deid[c] for c in cases if c in study2deid}
    return jsonify(ready=True, **clinical.disease_map(measure, deids))


@app.route("/api/clinical/<path:rel>")
def clinical_for(rel):
    safe_path(rel)
    parts = rel.split("/")
    return jsonify(clinical.case_data(parts[-2] if len(parts) > 1 else "", parts[-1]))


# ---------------------------------------------------------------- slide API
@app.route("/api/info/<path:rel>")
def info(rel):
    slide, _ = slides.get(rel)
    p = dict(slide.properties)
    levels = zip(slide.level_dimensions, slide.level_downsamples, strict=True)
    return jsonify(
        path=rel,
        size=os.path.getsize(safe_path(rel)),
        dimensions=slide.dimensions,
        levels=[{"dims": d, "downsample": ds} for d, ds in levels],
        mpp_x=float(p.get("openslide.mpp-x", 0) or 0),  # micrometres per pixel at level 0
        mpp_y=float(p.get("openslide.mpp-y", 0) or 0),
        objective=p.get("openslide.objective-power"),
        vendor=p.get("openslide.vendor"),
        associated=sorted(slide.associated_images.keys()),
        properties=p,
    )


@app.route("/thumb/<int:size>/<path:rel>")
def thumb(size, rel):
    size = max(64, min(size, 1024))
    try:
        data = thumb_bytes(rel, size)
    except openslide.OpenSlideError:
        abort(500)

    resp = send_file(io.BytesIO(data), mimetype="image/jpeg")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.route("/assoc/<name>/<path:rel>")
def assoc(name, rel):
    slide, _ = slides.get(rel)
    if name not in slide.associated_images:
        abort(404)
    return img_response(slide.associated_images[name], "png")


@app.route("/dzi/<path:rel>.dzi")
def dzi(rel):
    _, dz = slides.get(rel)
    return app.response_class(dz.get_dzi("jpeg"), mimetype="application/xml")


@app.route("/dzi/<path:rel>_files/<int:level>/<int:col>_<int:row>.jpeg")
def tile(rel, level, col, row):
    _, dz = slides.get(rel)
    try:
        t = dz.get_tile(level, (col, row))
    except ValueError:
        abort(404)
    return img_response(t, "jpeg", 80)


@app.route("/region/<path:rel>")
def region(rel):
    """PNG of the current view (at most 2048 px). x, y, w, h are level-0 pixel coordinates."""
    slide, _ = slides.get(rel)
    x, y, w, h = (int(float(request.args[k])) for k in ("x", "y", "w", "h"))

    lvl = slide.get_best_level_for_downsample(max(w, h) / 2048)
    ds = slide.level_downsamples[lvl]
    img = slide.read_region((x, y), lvl, (max(1, int(w / ds)), max(1, int(h / ds))))
    img.thumbnail((2048, 2048))
    return img_response(img, "png")


# ---------------------------------------------------------------- startup
def parse_args():
    ap = argparse.ArgumentParser(description="Read-only SVS viewer for the CHAMPS slides.")
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="TOML settings file")
    ap.add_argument("--port", type=int, help="override the port from the config")
    ap.add_argument("--host", help="override the host from the config")
    ap.add_argument("--rescan", action="store_true", help="re-walk data_root, ignore the cache")
    return ap.parse_args()


def main():
    args = parse_args()
    config.update(load_config(args.config))
    host, port = args.host or config["host"], args.port or config["port"]

    clinical.configure(config["data_root"])
    load_index(args.rescan)
    clinical.start()

    print(f"SVS viewer on http://{host}:{port}  (data root: {config['data_root']}, read-only)")
    app.run(host=host, port=port, threaded=True)


if __name__ == "__main__":
    main()
