from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from postgrest import APIError

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.core.config import settings
from app.core.supabase_client import supabase

app = FastAPI(title="InnerWhispers Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.frontend_url)],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/db-test")
def db_test():
    try:
        response = (
            supabase
            .table("users")
            .select("*")
            .limit(1)
            .execute()
        )
        return {
            "success": True,
            "data": response.data,
        }
    except APIError as exc:
        return {
            "success": False,
            "error": str(exc),
            "hint": "Create the users table in Supabase or verify your SUPABASE_URL/SUPABASE_KEY",
        }
