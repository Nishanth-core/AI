from typing import Optional

from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    bio: Optional[str] = Field(
        default=None,
        max_length=500,
    )
