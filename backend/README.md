# InnerWhispers Backend

Python FastAPI backend for the InnerWhispers project.

## Requirements

- Python 3.11+
- `pip`

## Install

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## Health check

Open:

```bash
http://127.0.0.1:5000
```

Expected JSON:

```json
{
  "message": "InnerWhispers Backend Running"
}
```
