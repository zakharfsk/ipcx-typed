# ruff: noqa: S106
import discord
from discord.ext import commands
from pydantic import BaseModel

from ipcx_typed import Client

TOKEN = ""


class UserSessionParam(BaseModel):
    guild_id: int
    member_id: int


class UserSessionInfo(BaseModel):
    name: str
    age: int
    session_id: str


class MyDiscordBot(commands.Bot):
    def __init__(self, intents: discord.Intents):
        super().__init__(command_prefix="!", intents=intents)
        self.client = Client(host="localhost", port=8080, secret_key="secret")


intents = discord.Intents.default()
intents.message_content = True

bot = MyDiscordBot(intents=intents)


@bot.command()
async def get_user_session(ctx: commands.Context, member: discord.Member):
    if not ctx.guild:
        raise commands.CommandError("This command can only be used in a guild")

    response = await bot.client.request(
        "get_user_session", UserSessionParam(guild_id=ctx.guild.id, member_id=member.id), UserSessionInfo
    )
    await ctx.send(f"User {member.name} has session {response.data.session_id}")


bot.run(TOKEN)
