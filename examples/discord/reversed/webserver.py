# ruff: noqa: S106
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from ipcx_typed import Server


@asynccontextmanager
async def lifespan(app: FastAPI):
    await server.start()
    yield
    await server.stop()


app = FastAPI(lifespan=lifespan)
server = Server(host="localhost", port=8080, secret_key="secret")


class UserSessionParam(BaseModel):
    guild_id: int
    member_id: int


class UserSessionInfo(BaseModel):
    name: str
    age: int
    session_id: str


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@server.route(param_model=UserSessionParam, return_model=UserSessionInfo)
async def get_user_session(payload: UserSessionParam) -> UserSessionInfo:
    data = {
        "name": "John Doe",
        "age": 25,
        "session_id": "1234567890",
        "guild_id": payload.guild_id,
        "member_id": payload.member_id,
    }  # imagine this is a database query

    return UserSessionInfo(**data)
