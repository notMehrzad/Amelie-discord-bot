import discord
from discord.ext import commands
from typing import Any

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "help",
            aliases = ["h"],
            help = (
                "Shows the help menu which gives a brief information about Commands."
                "\nEnter a Command name for its full detail such as its application, usage, necessery permissions (if any) and etc. or don't, to get the help menu."
            ),
            brief = "Shows the help menu.",
            usage = "<command_name*[optional]*>",
            extras = {"Category": "Utility"}
    )
    async def help(self, ctx: commands.Context[commands.Bot], cmdStr: str | None = None):
        #help for specific command
        if cmdStr and cmdStr.lower() not in ["all", "list", "menu"]:
            cmd = self.bot.get_command(cmdStr.lower()) #fetches the command, None if not found

            #if user doesn't enter a valid command name
            if not cmd:
                return await ctx.reply(f"*{cmdStr}* doesn't exist. enter a valid command.")
            
            cmdEmbed = discord.Embed(
                title = "." + cmd.name,
                description = cmd.help or cmd.brief or "*no description*",
                color = discord.Color.blurple()
            ).set_author(name = "Help")
            #if command has aliases
            if cmd.aliases:
                cmdEmbed.add_field(name = "Aliases", value = ", ".join(cmd.aliases))
            
            if cmd.usage:
                cmdEmbed.add_field(name = "Usage", value = f".{cmd.name} {cmd.usage}")

            #if command has extra information
            for key, value in cmd.extras.items():
                if key == "Category":
                    continue
                cmdEmbed.add_field(name = key, value = value) #add extra information to fields

            await ctx.reply(embed = cmdEmbed)
        
        #shows the help menu
        else:
            categorized: dict[str, list[commands.Command[Any, Any, Any]]] = {} #a dictionary to list categories and commands
            #example:
            #{
            #   "Moderation": ["ban", "kick"],
            #   "Utils": ["ping", "help"]
            #}

            #fetches all registered commadns
            for cmd in self.bot.commands:
                if cmd.hidden:
                    continue

                category = cmd.extras.get("Category", "etc.") #fetches each commands category
                categorized.setdefault(category, []).append(cmd) #adds the command and its category to categorized
            
            #sorts command list for every category in categorized dictionary
            for category in categorized:
                categorized[category].sort(key = lambda cmd: cmd.name)

            categorized = dict(sorted(categorized.items(), key=lambda item: item[0].lower())) #rebuilds the dictionary but sorted keys this time

            categoryEmbeds: list[discord.Embed] = [] #a list to store embeds for each category

            #fetches categorized data
            for category, cmdList in categorized.items():
                embed = discord.Embed(
                    title = f"{category}",
                    color = discord.Color.blurple()
                ).set_author(name = "Help Menu")
                for cmd in cmdList:
                    embed.add_field(name = "." + cmd.name, value = cmd.brief or "*no description*", inline = False) #create fields based on fetched commands

                categoryEmbeds.append(embed) #appends the created embed
            
            #if there is only one category, no buttons needed
            if len(categoryEmbeds) == 1:
                await ctx.reply(embed = categoryEmbeds[0]) #send the help menu
            
            else:
                view = HelpView(ctx, categoryEmbeds) #initializes the help view
                await view.start()
    
    @help.error
    async def help_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        print(f"❌ something went wrong with help command: {error}")
        await ctx.reply("something went wrong with **help**.")

class HelpView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot], categoryEmbeds: list[discord.Embed]):
        super().__init__(timeout = 90)
        self.ctx = ctx
        self.categoryEmbeds = categoryEmbeds
        self.EmbedIndex = 0

    async def start(self):
        self.msg = await self.ctx.reply(embed = self.categoryEmbeds[0], view = self) #sends the help menu from the first category

    #close button
    @discord.ui.button(label = "Close", style = discord.ButtonStyle.red, row = 0)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("You can't control this help menu. try help command yourself.", ephemeral = True)
        
        await self.msg.delete() #deletes the menu
        self.stop()

    #previous button
    @discord.ui.button(emoji = "◀️", style = discord.ButtonStyle.grey, row = 0)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("You can't control this help menu. try help command yourself.", ephemeral = True)
        
        await interaction.response.defer()
        
        self.EmbedIndex = (self.EmbedIndex - 1) % len(self.categoryEmbeds) #previous embed
        await self.msg.edit(embed = self.categoryEmbeds[self.EmbedIndex])

    #next button
    @discord.ui.button(emoji = "▶️", style = discord.ButtonStyle.grey, row = 0)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("You can't control this help menu. try help command yourself.", ephemeral = True)
        
        await interaction.response.defer()
        
        self.EmbedIndex = (self.EmbedIndex + 1) % len(self.categoryEmbeds) #next embed
        await self.msg.edit(embed = self.categoryEmbeds[self.EmbedIndex])

    async def on_timeout(self):
        #disables buttons on timeout
        for btn in self.children:
            if isinstance(btn, discord.ui.Button):
                btn.disabled = True

        try:
            await self.msg.edit(view = None) #edits the message to remove buttons on timeout
        except discord.NotFound:
            pass
        
        self.stop() #stops further interaction on timeout

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        print(f"❌ something went wrong with help interaction -> error: {error} | item: {getattr(item, 'emoji', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **help**.", ephemeral = True)
        except Exception:
            pass

        self.stop() #stops further interaction on error


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))