import discord
from discord.ext import commands
from pydantic import BaseModel

from ipcx_typed import Server

TOKEN = ""


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


class MyDiscordBot(commands.Bot):
    def __init__(self, intents: discord.Intents):
        super().__init__(command_prefix="!", intents=intents)
        self.server = Server(host="localhost", port=8080)

    async def setup_hook(self):
        await self.server.start()


intents = discord.Intents.default()
intents.message_content = True

bot = MyDiscordBot(intents=intents)


@bot.server.route(param_model=GuildParam, return_model=GuildInfo)
async def guild_info(payload: GuildParam) -> GuildInfo:
    guild: discord.Guild | None = bot.get_guild(payload.guild_id)
    if not guild:
        raise ValueError(f"Guild with id {payload.guild_id} not found")

    return GuildInfo(
        name=guild.name,
        member_count=guild.member_count,
        owner_id=guild.owner_id,
        role_count=len(guild.roles),
        channel_count=len(guild.channels),
        emoji_count=len(guild.emojis),
        voice_channel_count=len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)]),
        text_channel_count=len([c for c in guild.channels if isinstance(c, discord.TextChannel)]),
    )


bot.run(TOKEN)
