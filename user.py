from pydantic import BaseModel
from typing import List


class User(BaseModel):
    email: str
    firstName: str
    lastName: str
    password: str


class resetPassword(BaseModel):
    email: str
    reset_token: int
    new_password: str
