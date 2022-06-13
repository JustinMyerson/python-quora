from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo Wrestlers"}


@app.get("/", status_code=200)
async def root():
    return {"message": "Hello World"}


@app.post("/items/", status_code=201)
async def create_item(name: str):
    return {"name": name}


@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}
