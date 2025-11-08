import discord
from discord.ext import commands
import re
from urllib.parse import urlparse
import datetime

def parse_args(args: str):
    matches: list[tuple[str, str]] = re.findall(r'(\w+)\s*:\s*\((.*?)\)', args)
    return matches

def colorValidation(value: str):
    #removes leading '#' if any
    value = value.lstrip("#")

    #ensure that the hex code is 3 or 6 characters to be valid
    if len(value) not in [6, 3]:
        return False
    
    return bool(re.fullmatch(r"[0-9a-fA-F]{3}|[0-9a-fA-F]{6}", value))

def urlValidation(url: str):
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except:
        return False

async def assignVars(ctx: commands.Context[commands.Bot], arg_list: list[tuple[str, str]]):
    data: dict[str, None | str | discord.Color | datetime.datetime] = {
        "title": None,
        "desc": None,
        "url": None,
        "color": None,
        "imgurl": None,
        "thumbnailurl": None,
        "author": None,
        "authorurl": None,
        "authoriconurl": None,
        "footer": None,
        "footericonurl": None,
        "timestamp": None,
    }
    for arg, value in arg_list:
                    arg = arg.lower()
                    if arg == "title":
                        if len(value) > 256:
                            await ctx.reply("title can only be up to **256** characters.")
                            return None
                        data["title"] = value

                    elif arg in ["desc", "description"]:
                        if len(value) > 4096 :
                            await ctx.reply("description can only be up to **4096** characters.")
                            return None
                        data["desc"] = value

                    elif arg == "url":
                        if urlValidation(value):
                            data["url"] = value
                        else:
                            await ctx.reply("enter a valid **url** for the embed (like 'https://example.com').")
                            return None
                        
                    elif arg in ["color", "colour"]:
                        if colorValidation(value):
                            if not str(value).startswith("#"):
                                value = f"#{value}"
                            data["color"] = discord.Color.from_str(value)
                        else:
                            await ctx.reply("enter a valid **hex code** for `color` (like '#ffffff').")
                            return None
                            
                    elif arg in ["image url", "imageurl", "imgurl"]:
                        if urlValidation(value):
                            data["imgurl"] = value
                        else:
                            await ctx.reply("enter a valid **url** for `imageurl` (like 'https://example.com').")
                            return None
                        
                    elif arg in ["thumbnail url", "thumbnailurl"]:
                        if urlValidation(value):
                            data["thumbnailurl"] = value
                        else:
                            await ctx.reply("enter a valid **url** for `thumbnailurl` (like 'https://example.com').")
                            return None
                        
                    elif arg in ["author", "author name", "authorname"]:
                        if len(value) > 256:
                            await ctx.reply("author name can only be up to **256** characters.")
                            return None
                        data["author"] = value

                    elif arg in ["authorurl", "author url"]:
                        if urlValidation(value):
                            data["authorurl"] = value
                        else:
                            await ctx.reply("enter a valid **url** for `authorurl` (like 'https://example.com').")
                            return None
                        
                    elif arg in ["authoriconurl", "author icon url"]:
                        if urlValidation(value):
                            data["authoriconurl"] = value
                        else:
                            await ctx.reply("enter a valid **url** for `authoriconurl` (like 'https://example.com').")
                            return None
                        
                    elif arg == "footer":
                        if len(value) > 2048 :
                            await ctx.reply("footer can only be up to **2048** characters.")
                            return None
                        data["footer"] = value

                    elif arg in ["footericonurl", "footer icon url"]:
                        if urlValidation(value):
                            data["footericonurl"] = value
                        else:
                            await ctx.reply("enter a valid **url** for `footericonurl` (like 'https://example.com').")
                            return None
                        
                    elif arg in ["timestamp", "ts"]:
                        if value.lower() in ["yes", "y", "true", "now"]:
                            data["timestamp"] = discord.utils.utcnow()

                        elif value.lower() in ["no", "n", "false"]:
                            pass
                    
                        else:
                            await ctx.reply("you must select **yes/no** for `timestamp`.")
                            return None
                        
                    else:
                        await ctx.reply(f"{arg} is not a valid argument.")
                        return None
                        
    return data #returns the data dictionary if no problems else None is returned

class Embed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "embed",
            usage = "embed <subcommand> <embed_arguments>",
            help = (
                "This command can sends or edits an embed in the channel."
                "\nYou can specify Embed attributes like `key: (value)` (title: (hi) for instance). Supports all kind of Embed attributes."
            ),
            brief = "Sends or Edits an embed in the channel.",
            extras = {"Category": "Utility", "Subcommands": "send | edit(soon.)"}
    )
    async def embed(self, ctx: commands.Context[commands.Bot], cmd: str | None = None, *, args: str | None = None):
        #if user runs the command in dm
        if not ctx.guild:
            return await ctx.reply("You can't use this command in dm.")
        
        #if user doesn't enter a subcommand
        if not cmd:
            await ctx.reply("You must enter a subcommand for this command.", delete_after = 5)
            await ctx.message.delete(delay = 5)
            return
        
        cmd = cmd.lower()
        #send subcommand
        if cmd == "send":
            #if user doesn't enter the arguments
            if not args:
                return await ctx.reply("You must enter the arguments to create the Embed.")
            
            try:
                argList = parse_args(args) #parsing args
                data = await assignVars(ctx, argList) #collecting the data from args

                #returns if no data is available
                if not data:
                    return
                
                #creates the embed with the fetched data
                embed = discord.Embed(
                    title = data["title"],
                    description = data["desc"],
                    url = data["url"],
                    color = data["color"] if data["color"] is discord.Color else None,
                    timestamp = data["timestamp"] if data["timestamp"] is datetime.datetime else None
                ).set_footer(text = data["footer"], icon_url = data["footericonurl"])
                if data["author"]:
                    embed = embed.set_author(name = data["author"], url = data["authorurl"], icon_url = data["authoriconurl"])
                if data["imgurl"]:
                    embed = embed.set_image(url = data["imgurl"])
                if data["thumbnailurl"]:
                    embed = embed.set_thumbnail(url = data['thumbnailurl'])

                await ctx.send(embed = embed)

            except Exception as e:
                print(f"\n❌ something went wrong with embed-send command: {e}")
                await ctx.reply(f"something went wrong with **embed**.")

        else:
            await ctx.reply("Enter a valid subcommand.", delete_after = 5)
            await ctx.message.delete(delay = 5)

    @embed.error
    async def embed_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        print(f"❌ something went wrong with embed command: {error}")
        await ctx.reply(f"something went wrong with **embed**.", delete_after = 5)


async def setup(bot: commands.Bot):
    await bot.add_cog(Embed(bot))