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

From the `backend` folder, start the server with the repository virtual environment:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If the virtual environment is already activated, use:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
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
