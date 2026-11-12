# Barium - ModMail Static Log Viewer

A reproducible static site and SQLite index generator for Discord ModMail logs.

- **Fast Static Site Generation**: Generates 18,000+ thread pages in under 3 seconds using Python multiprocessing and Jinja2 templating.
- **Legacy URLs**: Each log is written to `dist/logs/<key>.html`, served at `/logs/<key>`, matching the old `modmail.pydis.wtf/logs/<key>` links.
- **Discord-Styled UI**: Clean, responsive Discord dark theme supporting embeds, image attachments, files, bot/mod/internal badges, and markdown.
- **Client-Side WASM Search**: Queries the generated SQLite database directly in the browser via `sql.js` (WebAssembly) with zero backend server requirements.

---

## Requirements

- **Node.js** >= 18 and **npm**
- **Python** >= 3.11 with [uv](https://docs.astral.sh/uv/) (or standard python venv)

---

## Project Structure

```
.
├── generator/              # Python static generator package
│   ├── cli.py             # CLI runner with batch streaming & multiprocessing
│   ├── formatter.py       # Discord markdown parser & path helpers
│   ├── indexer.py         # SQLite index builder
│   ├── templates/         # Jinja2 templates (thread.html)
│   └── worker.py          # Multiprocess thread page renderer
├── src/frontend/           # Frontend SPA for WASM SQLite querying
│   ├── index.html         # Search interface
│   ├── main.js            # sql.js WASM integration and querying
│   └── style.css          # Search frontend styling
├── public/                 # Static assets copied directly to dist/
│   └── thread.css         # Thread page styling
├── dist/                   # Build output (reproducible static site)
│   ├── index.html         # Built search frontend
│   ├── index.db           # SQLite database index
│   ├── assets/            # Bundled JS, CSS, and WASM binary
│   └── logs/              # Thread HTML pages (logs/<key>.html -> /logs/<key>)
├── package.json            # Node build scripts & dependencies
├── pyproject.toml          # Python project definitions (uv managed)
└── vite.config.js          # Vite build config
```

---

## Quickstart

### 1. Install Dependencies

```bash
npm install
uv sync
```

### 2. Build the Static Site and SQLite Index

```bash
# Build frontend bundle + generate all thread pages and SQLite database
npm run build
```

Individual build commands:
- `npm run build:frontend` — Compiles the Vite frontend and bundles sql.js WASM into `dist/`.
- `npm run build:pages` — Generates thread HTML pages into `dist/logs/` and builds `dist/index.db` (thread metadata only; message text lives in the pages).
- Or pass custom inputs/outputs:
  ```bash
  uv run python -m generator.cli --input logs.jsonl --output dist --concurrency 8
  ```

### 3. Preview Locally

```bash
npm run serve
```
Open the printed URL (e.g., `http://localhost:4173/`) in your browser to test instant WASM-based SQLite queries.

---

## Container image

The logs are private, so the image is built locally from a Modmail export and pushed to a private package. CI never sees the data.

```bash
npm run build:frontend
uv run python -m generator.cli --input export/logs.jsonl --output dist
docker build -t ghcr.io/owl-corp/barium:latest .
docker push ghcr.io/owl-corp/barium:latest
```

The image is nginx serving `dist/` on port 8000 (`nginx.conf` maps `/logs/<key>` to `logs/<key>.html`).
