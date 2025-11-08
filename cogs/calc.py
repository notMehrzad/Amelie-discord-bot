from discord.ext import commands
import sympy as sp

class Calc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
            name = "calc",
            aliases = ["calculator", "calculate"],
            usage = "<math_expression>",
            brief = "Calculates the given math expression.",
            help = (
                "Calculates the given math expression."
                "\nsupports trigonometric, logarithms and etc."
            ),
            extras = {"Category": "Utility"}
    )
    async def calc(self, ctx: commands.Context[commands.Bot], *, expression: str | None = None):
        if not expression:
            return await ctx.reply("You must enter a math expression to be calculated.")
        
        try:
            expression = expression.replace("^", "**")
            expression = expression.replace("√", "sqrt")

            result = sp.sympify(expression, locals = { # type: ignore
                "pi": sp.pi, "e": sp.E,
                "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "cot": sp.cot, "sec": sp.sec, "csc": sp.csc,
                "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "acot": sp.acot, "asec": sp.asec, "acsc": sp.acsc,
                "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh, "coth": sp.coth, "sech": sp.sech, "csch": sp.csch,
                "asinh": sp.asinh, "acosh": sp.acosh, "atanh": sp.atanh, "acoth": sp.acoth, "asech": sp.asech, "acsch": sp.acsch,
                "log": sp.log,
                "sqrt": sp.sqrt # type: ignore
            })

            #Converts symbolic to numeric if needed
            numeric_result = result.evalf() if result.is_real or result.is_complex else result # type: ignore

            await ctx.reply(f"= `{numeric_result:.2f}`")
        except Exception:
            await ctx.reply("Enter a valid math expression.")

    @calc.error
    async def calc_error(self, ctx: commands.Context[commands.Bot], error: Exception):
        print(f"❌ something went wrong with calc command: {error}")
        await ctx.reply("something went wrong with **calc**.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Calc(bot))