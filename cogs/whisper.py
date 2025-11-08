import discord
from discord.ext import commands

class Whisper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name = "whisper")
    async def whisper(self, ctx: commands.Context[commands.Bot], user: discord.User | None = None, *, msg: str | None = None):
        #if user runs the command in dm
        if not ctx.guild:
            return await ctx.reply("You can only whisper someone in a server.")
        
        #if user doesn't enter a target user
        if not user:
            return await ctx.reply("You must mention a Member to whisper.")
        
        target = ctx.guild.get_member(user.id)

        if not target:
            return await ctx.reply(f"{user.display_name} is not a member of this server.")
        
        #if user target is user himself
        if target.id == ctx.author.id:
            return await ctx.reply("You can't whisper to yourself.")
        
        #if target user is a bot except the bot itself
        if target.bot and target.id != ctx.me.id:
            return await ctx.reply("You can't whisper to dumb bots. (except me ofc)")
        
        if not msg:
            return await ctx.reply("You must write your message to be whispered.")
        
        await ctx.message.delete() #deletes the users message

        #the bot responds if target is the bot
        if target.id == ctx.me.id:
            return await ctx.reply("I hear your words..")
        
        view = WhisperView(ctx, target, msg) #initializes the view
        await view.start() #starts the view

    @whisper.error
    async def whisper_error(self, ctx: commands.Context[commands.Bot], error: commands.CommandError):
        #if user mentioned an invalid user
        if isinstance(error, commands.BadArgument):
            await ctx.reply("user not found. Please mention a valid member.")
        else:
            print(f"❌ something went wrong with whisper command: {error}")
            await ctx.reply("something went wrong with **whisper**.")

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
            return await interaction.response.send_message(f"*You whisper to {self.target.mention}:*\n{self.msg}", ephemeral = True)
        
        await interaction.response.send_message(f"*{self.ctx.author.display_name} whispers to you:*\n{self.msg}", ephemeral = True) #shows whisper to the target

        finalEmbed = discord.Embed(
            title = "whisper",
            description = f"{self.target.display_name} has read the whisper from {self.ctx.author.display_name}."
        )
        await self.ctxMsg.edit(embed = finalEmbed, view = None) #edits the sent message to show the reading status

        self.stop() #stops the view after target has read the whisper

    async def on_timeout(self):
        self.read.disabled = True

        toEmbed = discord.Embed(
            title = "whisper",
            description = f"⏰ The whisper got forgotten.. {self.target.display_name} didn't get it early."
        )
        try:
            await self.ctxMsg.edit(embed = toEmbed, view = self)
        except discord.NotFound:
            pass

        self.stop()

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item[discord.ui.View]):
        print(f"❌ something went wrong with whisper interaction -> error: {error}\nbtn_name: {getattr(item, 'label', 'unknown')}")
        try:
            await interaction.response.send_message("something went wrong with **whisper**.", ephemeral = True)
        except discord.InteractionResponded:
            await interaction.followup.send("something went wrong with **whisper**.", ephemeral = True)
        except Exception:
            pass
            
        self.stop() #stops further interaction


async def setup(bot: commands.Bot):
    await bot.add_cog(Whisper(bot))