import discord
from discord.ext import commands

class Whisper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "whisper")
    async def whisper(self, ctx: commands.Context[commands.Bot], target: discord.Member | None = None, *, msg: str | None = None):
        #if user runs the command in dm
        if not ctx.guild:
            return await ctx.reply("You must whisper someone in a server.")
        
        #if user doesn't enter a target user
        if not target:
            return await ctx.reply("You must enter a user to whisper.")
        
        #if user target is user himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't whisper to yourself.")
        
        #if target user is a bot except the bot itself
        if target.bot and target.id != ctx.me.id:
            return await ctx.reply("You can't whisper to dumb bots.")
        
        if not msg:
            return await ctx.reply("You must write your message to be whispered.")
        
        await ctx.message.delete() #deletes the users message

        #the bot responds if target is the bot
        if target.id == ctx.me.id:
            await ctx.reply("I hear your words..")
            return
        
        view = WhisperView(ctx, target, msg) #initializes the view
        await view.start() #starts the view

    @whisper.error
    async def whisper_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user mentioned an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("user not found. Please mention a valid user.")
        else:
            print(f"❌ something went wrong with vrps command: {error}")
            await ctx.reply("something went wrong with **vrps**.")

class WhisperView(discord.ui.View):
    def __init__(self, ctx: commands.Context[commands.Bot], target: discord.Member, msg: str):
        super().__init__(timeout = 300)
        self.ctx = ctx
        self.target = target
        self.msg = msg

    async def start(self):
        whisperEmbed = discord.Embed(
            title = "whisper",
            description = f"{self.target.mention}, You have a whisper from {self.ctx.author.mention}."
        )
        self.ctxMsg = await self.ctx.send(embed = whisperEmbed, view = self)

    #defines read button
    @discord.ui.button(label = "read" , style = discord.ButtonStyle.grey)
    async def read(self, interaction: discord.Interaction, button: discord.ui.Button[discord.ui.View]):
        if interaction.user.id not in [self.target.id, self.ctx.author.id]:
            return await interaction.response.send_message("You can't read others whisper.", ephemeral = True)
        
        #if user trys to read his own whisper
        if interaction.user.id == self.ctx.author.id:
            return await interaction.response.send_message(f"`you sent this whisper to {self.target.display_name}`\n{self.msg}", ephemeral = True)
        
        await interaction.response.send_message(f"`{self.ctx.author.display_name} whispers to you`\n{self.msg}", ephemeral = True) #shows whisper to the target

        finalEmbed = discord.Embed(
            title = "whisper",
            description = f"{self.target.display_name} has read the whisper from {self.ctx.author.display_name}."
        )
        await self.ctxMsg.edit(embed = finalEmbed, view = None) #edits the sent message to show the reading status

        self.stop() #stops the view after target has read the whisper

    async def on_timeout(self):
        pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        print(f"❌ something went wrong with whisper interaction -> error: {error} | item: {getattr(item, 'lable', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **whisper**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **whisper**.", ephemeral = True)
            
        self.stop() #stops further interaction


async def setup(bot: commands.Bot):
    await bot.add_cog(Whisper(bot))