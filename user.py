from pydantic import BaseModel, HttpUrl
from typing import List


class User(BaseModel):
    email: str
    firstName: str
    lastName: str
    password: str
