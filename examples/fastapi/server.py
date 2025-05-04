from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from ipcx_typed.server import Server


@asynccontextmanager
async def lifespan(app: FastAPI):
    await server.start()
    yield
    await server.stop()


app = FastAPI(lifespan=lifespan)
server = Server(host="localhost", port=8080)


class PlusTwoNumbers(BaseModel):
    a: int
    b: int


class PlusTwoNumbersResponse(BaseModel):
    string: str
    result: int
    complex_data: list[PlusTwoNumbers]


@server.route(param_model=PlusTwoNumbers, return_model=PlusTwoNumbersResponse)
async def numbers(param: PlusTwoNumbers):
    return PlusTwoNumbersResponse(
        string="Hello, world!",
        result=param.a + param.b,
        complex_data=[PlusTwoNumbers(a=1, b=2), PlusTwoNumbers(a=3, b=4)],
    )


@app.get("/")
async def root():
    return {"message": "Hello, World!"}
