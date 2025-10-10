import discord
from discord.ext import commands
import re

def parse_args(args):
    matches = re.findall(r"(\w+)\s*:\s*'(.*?)'", args)
    return matches

class EmbedSend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name = "embedsend", aliases = ["sendembed", "embed"])
    async def embedsend(self, ctx, *, args):
        try:
            #initializing variables
            title = desc = url = color = imgurl = thumbnailurl = author = authorurl = authoriconurl = footer = footericonurl = timestamp = None

            #parsing args
            argList = parse_args(args)

            #loops through arglist and checks variables
            for arg, value in argList:
                arg = arg.lower()
                if arg == "title":
                    if len(value) > 256:
                        await ctx.reply(content = "title can only be up to **256** characters.", ephemeral = True)
                    title = value
                elif arg in ["desc", "description"]:
                    desc = value
                elif arg == "url":
                    url = value
                elif arg in ["color", "colour"]:
                    color = discord.Color.from_str(value)
                elif arg in ["image url", "imageurl", "imgurl"]:
                    imgurl = value
                elif arg in ["thumbnail url", "thumbnailurl"]:
                    thumbnailurl = value
                elif arg == "author":
                    author = value
                elif arg in ["authorurl", "author url"]:
                    authorurl = value
                elif arg in ["authoriconurl", "author icon url"]:
                    authoriconurl = value
                elif arg == "footer":
                    footer = value
                elif arg in ["footericonurl", "footer icon url"]:
                    footericonurl = value
                elif arg == "timestamp" and value.lower() in ["yes", "true", "y"]:
                    timestamp = discord.utils.utcnow()

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

        except Exception as e:
            print(f"\nerror at sendembed command: {e}")
            await ctx.reply("something went wrong.")

async def setup(bot):
    await bot.add_cog(EmbedSend(bot))