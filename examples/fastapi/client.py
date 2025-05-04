from fastapi import FastAPI
from pydantic import BaseModel

from ipcx_typed.client import Client

app = FastAPI()
client = Client(host="localhost", port=8080)


class PlusTwoNumbers(BaseModel):
    a: int
    b: int


class PlusTwoNumbersResponse(BaseModel):
    string: str
    result: int
    complex_data: list[PlusTwoNumbers]


@app.get("/")
async def root():
    return {
        "message": "Hello, World!",
        "result": await client.request("numbers", PlusTwoNumbers(a=1, b=2), PlusTwoNumbersResponse),
    }
