# Dependencies

Every direct dependency and why we need it. Versions live in `pixi.lock`.

| Package | Purpose |
| --- | --- |
| python | Pinned to 3.14 so everyone runs the same interpreter |
| pixi | Environments, lockfile and tasks in one tool; changes are reviewable in PRs |
| ruff | Linting, import sorting, formatting |
| openslide-python | SVS viewer: reads `.svs` slides (tiles, thumbnails, label/macro images, metadata); brings the OpenSlide C library |
| flask | SVS viewer: local web server for pages, tiles and JSON endpoints |
| pillow | SVS viewer: encodes tiles, thumbnails and snapshots |
| pandas | SVS viewer: loads the case CSVs, CPL reports and derived tables |
| pyarrow | Parquet engine for pandas (`slide_labels.parquet`, `pigment_confirmation.parquet`) |
| pypdf | SVS viewer: reads TAC assay names from the dataset description PDF |

The viewer pages also load OpenSeadragon 4.1.1, d3 7.9.0, topojson-client 3.1.0 and world-atlas 2.0.2 from pinned CDN URLs (not Pixi dependencies).
