# Setup Guide

This guide walks through getting smart-receipt running locally on Windows
with 8 GB RAM. Adjust paths and commands for macOS or Linux as needed.

## 1. Prerequisites

* Python 3.11 (tested) or 3.10
* Node.js 20 or higher
* Docker Desktop (for Redis and monitoring)
* Git

Anaconda or Miniconda is recommended for managing the Python environment.

## 2. Clone and enter project

```bash
git clone https://github.com/Venta02/smart-receipt.git
cd smart-receipt
```

## 3. Python environment

Create a fresh conda environment (recommended on Windows):

```bash
conda create -n smartreceipt python=3.11 -y
conda activate smartreceipt
```

Install dependencies:

```bash
pip install -r requirements.txt
```

PaddleOCR will download model weights on first use (around 15 MB total
for detection, recognition, and angle classification). The models
cache to `~/.paddleocr` and need to be downloaded only once.

## 4. Environment file

```bash
cp .env.example .env
```

The defaults are fine for local development. Set `OCR_USE_GPU=true`
only if you have CUDA configured.

## 5. Start Redis

```bash
docker compose up -d redis
```

Confirm it is running:

```bash
docker ps
```

You should see `sr-redis` with status `Up (healthy)`.

## 6. Run the API

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

First startup downloads PaddleOCR models if they are not cached. Wait
for `Application ready` in the logs.

Open these URLs to verify:

* http://localhost:8000 returns service info
* http://localhost:8000/docs shows Swagger UI
* http://localhost:8000/health returns service status

## 7. Run the frontend

In a separate terminal:

```bash
cd frontend/nextjs_app
npm install
npm run dev
```

Open http://localhost:3000.

## 8. Smoke test

You can run a quick CLI test without the API:

```bash
python scripts/test_extraction.py path/to/receipt.jpg
```

Or upload an image through the web UI at http://localhost:3000.

## 9. Optional: full monitoring stack

```bash
docker compose up -d
```

Open:

* Prometheus at http://localhost:9090
* Grafana at http://localhost:3001 (login admin / admin)

## Troubleshooting

### PaddleOCR fails to install on Windows

This usually means a Visual C++ Build Tools issue. Try installing
in this order from the conda environment:

```bash
pip install paddlepaddle==2.6.1
pip install paddleocr==2.7.3
```

### Out of memory during OCR

Lower the image size before processing or increase Docker memory
allocation. PaddleOCR with default settings uses around 1 to 1.5 GB
of RAM during inference.

### Redis connection refused

Confirm Docker Desktop is running and the `sr-redis` container is up.
If port 6379 is already used by a local Redis install, stop it or
change `REDIS_PORT` in `.env`.

### Frontend cannot reach API

Check that uvicorn is bound to `0.0.0.0` (not `127.0.0.1`) and that
no firewall is blocking port 8000. The frontend reads
`NEXT_PUBLIC_API_URL` from the environment, defaulting to
`http://localhost:8000`.
