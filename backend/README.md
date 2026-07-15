# LocalHub Backend

## Overview

This folder contains the FastAPI backend skeleton for the LocalHub project.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Health check

```bash
curl http://127.0.0.1:8000/health
```
