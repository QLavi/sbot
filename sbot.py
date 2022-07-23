import os
from dotenv import load_dotenv
import nextcord
from nextcord.ext import commands
from config import Config

load_dotenv()
sbot_version = '0.0.0.1'
token = os.environ.get('Token')

intents = nextcord.Intents.all()

class SBot(commands.Bot):
  def __init__(self, **options):
    super().__init__(**options)
    self.guild_id = int(os.environ.get('Guild_ID'))

  async def on_ready(self):
    guild = self.get_guild(self.guild_id)
    print(f'Logged In as {bot.user} on {guild}')

  async def on_command_error(self, ctx, error):
    await ctx.send(f'Error: {error}')

  async def on_message(self, msg):
    if msg.author.bot or len(msg.content) == 0: return
    ctx = await self.get_context(msg)

    valid_call = False
    used_cmd = ''
    if msg.content.startswith(Config.cmd_prefix):
      for cmd in self.commands:
        begin = len(Config.cmd_prefix)
        end   = begin + len(cmd.name)

        if msg.content[begin:end] == cmd.name:
          used_cmd = cmd.name
          valid_call = True
          break
          
      if not valid_call:
        await ctx.send(f'Error: {error}')
        return

      begin = msg.content.find('(')
      end   = msg.content.find(')')
      original = msg.content

      if begin +1 == end:
        msg.content = f'{Config.cmd_prefix}{used_cmd}'
      else:
        args = msg.content[begin+1:end]
        msg.content = f'{Config.cmd_prefix}{used_cmd} ({args})'

      await self.process_commands(msg)
      msg.content = original

  def load_cogs(self):
    for file in os.listdir('cogs'):
      if file.endswith('_cog.py'):
        try:
          self.load_extension(f'cogs.{file[:-3]}')
        except nextcord.DiscordException as e: print(e)

bot = SBot(command_prefix=Config.cmd_prefix, intents=intents)

bot.load_cogs()
bot.run(token, reconnect=True)
