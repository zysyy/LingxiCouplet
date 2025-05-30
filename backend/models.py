from pydantic import BaseModel

class Profile(BaseModel):
    KEY: int

class User(BaseModel):
    username: str
    age: int
    profile: Profile

class CoupletRequest(BaseModel):
    text: str

class EvaluateRequest(BaseModel):
    up_text: str
    down_text: str

