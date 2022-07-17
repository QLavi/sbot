import os
from dotenv import load_dotenv
import nextcord
from nextcord.ext import commands

load_dotenv()
sbot_version = '0.0.0.1'
token = os.environ.get('TOKEN')

intents = nextcord.Intents.all()

class SBot(commands.Bot):
  def __init__(self, **options):
    super().__init__(**options)
    self.guild_id = os.environ.get('GUILD_ID')

  @commands.Cog.listener()
  async def on_ready(self):
    guild = self.get_guild(int(self.guild_id))
    print(f'Logged In as {bot.user} on {guild}')

  @commands.Cog.listener()
  async def on_command_error(self, ctx, error):
    await ctx.send(f'Error: {error}')

  def load_cogs(self):
    for file in os.listdir('cogs'):
      if file.endswith('_cog.py'):
        try:
          bot.load_extension(f'cogs.{file[:-3]}')
        except nextcord.DiscordException as e: print(e)

bot = SBot(command_prefix='sbot.', intents=intents)

bot.load_cogs()
bot.run(token)
