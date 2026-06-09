from app.core.supabase_client import supabase


def get_user_profile(user_id: str):
    result = (
        supabase
        .table("users")
        .select("id,email,name,bio,avatar_url,created_at")
        .eq("id", user_id)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def update_user_profile(user_id: str, data: dict):
    result = (
        supabase
        .table("users")
        .update(data)
        .eq("id", user_id)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def delete_user(user_id: str):
    supabase.table("users").delete().eq("id", user_id).execute()
    return True
