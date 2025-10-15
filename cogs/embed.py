import discord
from discord.ext import commands
import re
import asyncio
from urllib.parse import urlparse

def parse_args(args):
    matches = re.findall(r'(\w+)\s*:\s*\((.*?)\)', args)
    return matches

def colorValidation(value: str):
    #removes leading '#' if any
    value = value.lstrip("#")

    #ensure that the hex code is 3 or 6 characters to be valid
    if len(value) not in [6, 3]:
        return False
    
    return bool(re.fullmatch(r"[0-9a-fA-F]{3}|[0-9a-fA-F]{6}", value))

def urlValidation(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except:
        return False

async def assignVars(ctx: commands.Context, arg_list):
    data = {
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
                        await ctx.reply("enter a valid attribute (like `title`, `description`, ..)")
                        return None
                        
    return data

class Embed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "embed")
    async def embed(self, ctx: commands.Context, cmd: str = None, *, args: str = ""):
        try:
            cmd = cmd.lower() if cmd else None

            #if subcommand is send
            if cmd == "send":
                try:
                    argList = parse_args(args) #parsing args
                    data = await assignVars(ctx, argList) #collecting the data from args

                    if not data:
                        return
                    
                    #creates the embed with the fetched data
                    embed = discord.Embed(
                        title = data["title"],
                        description = data["desc"],
                        url = data["url"],
                        color = data["color"],
                        timestamp = data["timestamp"]
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
                    await ctx.reply(f"something went wrong with **embed**.", delete_after = 5)

            elif cmd is None:
                await ctx.reply("You must enter a subcommand for this command.", delete_after = 5)
                await asyncio.sleep(5)
                await ctx.message.delete()

            else:
                await ctx.reply("Enter a valid subcommand.", delete_after = 5)
                await asyncio.sleep(5)
                await ctx.message.delete()
                
        except Exception as e:
            print(f"❌ something went wrong with embed command: {e}")
            await ctx.reply(f"something went wrong with **embed**.", delete_after = 5)

async def setup(bot: commands.Bot):
    await bot.add_cog(Embed(bot))