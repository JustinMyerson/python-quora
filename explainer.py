
from fastapi import FastAPI

# Here the app variable will be an "instance" of the class FastAPI.
# This will be the main point of interaction to create all your API.
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}
