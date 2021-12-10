from typing import Optional

from fastapi_users import models


class CustomCreateUpdateDictModel(models.BaseModel):
    def create_update_dict(self):
        return self.dict(
            exclude_unset=True,
            exclude={
                "id",
                "is_superuser",
                "is_active",
                "is_verified",
                "oauth_accounts",
                "probing_enabled",  # Custom field
                "probing_limit",  # Custom field
            },
        )


class User(models.BaseUser, models.BaseOAuthAccountMixin):
    firstname: str = "string"
    lastname: str = "string"
    probing_enabled: bool = False
    probing_limit: Optional[int] = 0


class UserCreate(CustomCreateUpdateDictModel, models.BaseUserCreate):
    firstname: str = "string"
    lastname: str = "string"
    probing_enabled: bool = False
    probing_limit: Optional[int] = 0


class UserUpdate(CustomCreateUpdateDictModel, models.BaseUserUpdate):
    firstname: str = "string"
    lastname: str = "string"
    probing_enabled: bool = False
    probing_limit: Optional[int] = 0


class UserDB(User, models.BaseUserDB):
    pass
