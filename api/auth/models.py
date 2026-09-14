from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    disabled: bool = False

class UserInDB(User):
    hashed_password: str