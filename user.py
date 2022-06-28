from pydantic import BaseModel


class User(BaseModel):
    email: str
    firstName: str
    lastName: str
    password: str


class loginUser(BaseModel):
    email: str
    password: str


class changePassword(BaseModel):
    old_password: str
    new_password: str


class resetPassword(BaseModel):
    email: str
    reset_token: int
    new_password: str

class searchForUser(BaseModel):
    email: str