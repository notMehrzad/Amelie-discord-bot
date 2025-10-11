import discord
from discord.ext import commands
import re
import asyncio
from urllib.parse import urlparse

def parse_args(args):
    matches = re.findall(r"(\w+)\s*:\s*'(.*?)'", args)
    return matches

def colorValidation(s):
    if len(s) not in [6, 3]:
        return False
    return bool(re.fullmatch(r"([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", s))

def urlValidation(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except:
        return False

async def assignVars(ctx, arg_list):
    for arg, value in arg_list:
                    arg = arg.lower()
                    if arg == "title":
                        if len(value) > 256:
                            await ctx.reply("title can only be up to **256** characters.")
                            return
                        title = value
                    elif arg in ["desc", "description"]:
                        if len(value) > 4096 :
                            await ctx.reply("title can only be up to **4096** characters.")
                            return
                        desc = value
                    elif arg == "url":
                        if urlValidation(value):
                            url = value
                        else:
                            await ctx.reply("enter a valid **url** for the embed (like 'https://example.com').")
                            return
                    elif arg in ["color", "colour"]:
                        if str(value).startswith("#") and colorValidation(value):
                            color = discord.Color.from_str(value)
                        elif colorValidation(value):
                            value = f"#{value}"
                            color = discord.Color.from_str(value)
                        else:
                            await ctx.reply("enter a valid **hex code** for `color` (like '#ffffff').")
                            return
                    elif arg in ["image url", "imageurl", "imgurl"]:
                        if urlValidation(value):
                            imgurl = value
                        else:
                            await ctx.reply("enter a valid **url** for `imageurl` (like 'https://example.com').")
                            return
                    elif arg in ["thumbnail url", "thumbnailurl"]:
                        if urlValidation(value):
                            thumbnailurl = value
                        else:
                            await ctx.reply("enter a valid **url** for `thumbnailurl` (like 'https://example.com').")
                            return
                    elif arg in ["author", "author name", "authorname"]:
                        if len(value) > 256:
                            await ctx.reply("author name can only be up to **256** characters.")
                            return
                        author = value
                    elif arg in ["authorurl", "author url"]:
                        if urlValidation(value):
                            authorurl = value
                        else:
                            await ctx.reply("enter a valid **url** for `authorurl` (like 'https://example.com').")
                            return
                    elif arg in ["authoriconurl", "author icon url"]:
                        if urlValidation(value):
                            authoriconurl = value
                        else:
                            await ctx.reply("enter a valid **url** for `authoriconurl` (like 'https://example.com').")
                            return
                    elif arg == "footer":
                        if len(value) > 2048 :
                            await ctx.reply("footer can only be up to **2048** characters.")
                            return
                        footer = value
                    elif arg in ["footericonurl", "footer icon url"]:
                        if urlValidation(value):
                            footericonurl = value
                        else:
                            await ctx.reply("enter a valid **url** for `footericonurl` (like 'https://example.com').")
                            return
                    elif arg in ["timestamp", "ts"]:
                        if value.lower() in ["yes", "y", "true", "now"]:
                            timestamp = discord.utils.utcnow()
                        else:
                            await ctx.reply("you must select **yes/no** for `timestamp`.")

class Embed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = "embed")
    async def embed(self, ctx, cmd: str = None, *, args):
        try:
            cmd = cmd.lower() if cmd else None

            #initializing variables
            title = desc = url = color = imgurl = thumbnailurl = author = authorurl = authoriconurl = footer = footericonurl = timestamp = None

            #if subcommand is send
            if cmd == "send":
                #parsing args
                argList = parse_args(args)
                await assignVars(ctx, argList) #loops through arglist and assigns variables

                #print(title, desc, url, color, imgurl, thumbnailurl, author, authorurl, authoriconurl, footer, footericonurl, timestamp)

                embed = discord.Embed(
                    title = title,
                    description = desc,
                    url = url,
                    color = color,
                    timestamp = timestamp
                ).set_image(url = imgurl).set_thumbnail(url = thumbnailurl).set_author(name = author, url = authorurl, icon_url = authoriconurl).set_footer(text = footer, icon_url = footericonurl)
                if author == None:
                    embed = embed.remove_author()

                await ctx.send(embed = embed)

            #if subcommand is edit
            if cmd == "edit":
                pass #will create this later
                

        except Exception as e:
            print(f"❌ something went wrong with embed command: {e}")
            msg = await ctx.reply(f"❌ something went wrong with **embed**.")
            await asyncio.sleep(3)
            await msg.delete()

async def setup(bot):
    await bot.add_cog(Embed(bot))