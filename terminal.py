from discord.ext import commands


class Terminal:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def command(self, cmdRaw: str):
        if not cmdRaw:
            return

        cmd = cmdRaw.split(" ")

        if cmd[0] == "ping":
            return self.ping()
        elif cmd[0] in ("commandsync", "csync"):
            return await self.commandSync()

        elif cmd[0] == "cog":
            return await self.cog(cmd)
        elif cmd[0] in ("shutdown", "sd"):
            await self.bot.close()
            print("\n--------------")
            print(f"The Bot has been shut down. ⏹️")
        else:
            print("\n--------------")
            print(f"{cmd[0]} is not a valid terminal command.")

    # ping commands
    def ping(self):
        ws = self.bot.latency * 1000
        print("\n--------------")
        print(f"Ping result -> {int(ws)}ms")

    # commandsync command
    async def commandSync(self):
        syncedCmds = await self.bot.tree.sync()
        syncedCmds = [("/" + cmd.name) for cmd in syncedCmds]
        print("\n--------------")
        print(f"{syncedCmds} commands have been synced. ✔️")

    # cog command
    async def cog(self, cmd: list[str]):
        if len(cmd) == 1:
            print("Enter a subcommand for this command. (reload/list)")
            return
        extensionList = list(self.bot.extensions)
        if cmd[1] in ("reload", "r"):
            if len(cmd) == 2 or cmd[2] == "all":
                print("\n--------------")
                print("Reloading all cogs..")
                for ext in extensionList:
                    await self.bot.reload_extension(ext)
                    print(f"🔄️ {ext.split(".")[-1]} reloaded.")
                print("All cogs have been reloaded succesfully. ✅")
            else:
                match = None
                for ext in extensionList:
                    if ext.split(".")[-1] == cmd[2]:
                        match = ext
                        break
                if not match:
                    print(f"`{cmd[2]}` is not a loaded cog.")
                    return

                print("\n--------------")
                print(f"Reloading `{match.split(".")[-1]}` cog..")
                await self.bot.reload_extension(match)
                print(f"`{match.split(".")[-1]}` cog has been reloaded. 🔄️")
        elif cmd[1] == "list":
            print(f"\n--------------")
            print(extensionList)
        else:
            print("Enter a valid subcommand.")
