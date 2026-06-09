import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.dependencies import get_current_user
from app.core.supabase_client import supabase
from app.schemas.user import UpdateProfileRequest
from app.services.user_service import (
    delete_user,
    get_user_profile,
    update_user_profile,
)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me")
def profile(current_user=Depends(get_current_user)):
    user = get_user_profile(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me")
def update_profile(
    payload: UpdateProfileRequest,
    current_user=Depends(get_current_user),
):
    data = payload.model_dump(exclude_none=True)
    user = update_user_profile(current_user["sub"], data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/me")
def delete_profile(current_user=Depends(get_current_user)):
    delete_user(current_user["sub"])
    return {"message": "Account deleted"}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_content = await file.read()

    supabase.storage.from_("avatars").upload(filename, file_content)
    avatar_url = supabase.storage.from_("avatars").get_public_url(filename)

    supabase.table("users").update({"avatar_url": avatar_url}).eq("id", current_user["sub"]).execute()

    return {"avatar_url": avatar_url}
