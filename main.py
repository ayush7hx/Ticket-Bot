"""
╔══════════════════════════════════════════════════╗
║          Ticket Bot                              ║
║          Fork customized by Ayush7hx             ║
║          discord.py 2.7+ • Python 3.10+          ║
╚══════════════════════════════════════════════════╝
"""

import os
import asyncio
import discord
from aiohttp import web
from discord.ext import commands
from dotenv import load_dotenv
from utils.emojis import sync_application_emojis

load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN not found in .env — copy .env.example to .env and fill it in.")

# ── Intents ────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ── Bot ────────────────────────────────────────────────────────
COGS = ["cogs.setup", "cogs.tickets"]


class TicketBot(commands.Bot):
    async def setup_hook(self):
        if self.application_id is None:
            raise RuntimeError("Discord did not provide an application ID; cannot sync emojis.")

        created = await sync_application_emojis(self.application_id, TOKEN)
        print(f"  Synced {created} application emoji(s)")

        for cog in COGS:
            await self.load_extension(cog)
            print(f"  Loaded: {cog}")


bot = TicketBot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    case_insensitive=True,
)


async def health(request: web.Request) -> web.Response:
    return web.json_response(
        {"status": "ok", "discord_connected": bot.is_ready()}
    )


def create_web_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    return app


@bot.event
async def on_ready():
    print("=" * 52)
    print("  ██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗██╗  ██╗")
    print("  ██║     ██║████╗  ██║██║   ██║╚██╗██╔╝╚██╗██╔╝")
    print("  ██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝  ╚███╔╝ ")
    print("  ██║     ██║██║╚██╗██║██║   ██║ ██╔██╗  ██╔██╗ ")
    print("  ███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗██╔╝ ██╗")
    print("  ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝")
    print("=" * 52)
    print(f"  Bot      : {bot.user}")
    print(f"  ID       : {bot.user.id}")
    print(f"  Servers  : {len(bot.guilds)}")
    print(f"  Customized: Ayush7hx")
    print(f"  Original  : wmikon")
    print(f"  Brand     : Ticket Bot")
    print("=" * 52)
    try:
        synced = await bot.tree.sync()
        print(f"  Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"  Slash sync failed: {e}")
    print("=" * 52)


async def main():
    port = int(os.getenv("PORT", "10000"))
    runner = web.AppRunner(create_web_app())
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"  Health server listening on port {port}")
    try:
        async with bot:
            await bot.start(TOKEN)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
