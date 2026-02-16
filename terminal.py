from discord.ext import commands


async def command(bot: commands.Bot, cmd: str | None = None):
    if not cmd:
        return

    if cmd == "ping":
        return ping(bot)
    elif cmd in ("commandsync", "csync"):
        return await commandSync(bot)
    elif cmd == "shutdown":
        await bot.close()
        print("\n--------------")
        print(f"The Bot has been shut down. ⏹️")
    else:
        print("\n--------------")
        print(f"{cmd} is not a valid terminal command. try `help`")


# ping commands
def ping(bot: commands.Bot):
    ws = bot.latency * 1000
    print("\n--------------")
    print(f"Ping result -> {int(ws)}ms")


# commandsync command
async def commandSync(bot: commands.Bot):
    syncedCmds = await bot.tree.sync()
    syncedCmds = [("/" + cmd.name) for cmd in syncedCmds]
    print("\n--------------")
    print(f"{syncedCmds} commands have been synced. ✔️")
