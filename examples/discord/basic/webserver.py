# ruff: noqa: S106
from fastapi import FastAPI
from pydantic import BaseModel

from ipcx_typed.client import Client

app = FastAPI()
client = Client(host="localhost", port=8080, secret_key="secret")


class GuildParam(BaseModel):
    guild_id: int


class GuildInfo(BaseModel):
    name: str
    member_count: int | None
    owner_id: int | None
    role_count: int
    channel_count: int
    emoji_count: int
    voice_channel_count: int
    text_channel_count: int


@app.get("/")
async def root():
    return {
        "guild_info": await client.request("guild_info", GuildParam(guild_id=12345678), GuildInfo),
    }
