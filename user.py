from pydantic import BaseModel, HttpUrl
from typing import Sequence


class User(BaseModel):
    email: str
    firstName: str
    lastName: str
    password: str
