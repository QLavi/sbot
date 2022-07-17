import nextcord
from nextcord.ext import commands
import matplotlib.pyplot as plt
from collections import Counter

import io
import os
import time
import queue
import asyncio
import aiosqlite
import pandas as pd

create_channels_table = """
CREATE TABLE IF NOT EXISTS Channels(
  id   NCHAR(18),
  name NVARCHAR(24) NOT NULL UNIQUE,
  PRIMARY KEY(id)
)
"""
create_users_table = """
CREATE TABLE IF NOT EXISTS Users(
  id         NCHAR(18),
  name       NVARCHAR(128) NOT NULL UNIQUE,
  PRIMARY KEY(id)
)
"""
create_messages_table = """
CREATE TABLE IF NOT EXISTS Messages(
  id            NCHAR(18),
  on_channel_id INTEGER,
  user_id       INTEGER,
  time_stamp    INTEGER,
  content       TEXT NOT NULL,
  PRIMARY KEY(id)
  FOREIGN KEY(user_id) REFERENCES Users(id)
  FOREIGN KEY(on_channel_id) REFERENCES Channels(id)
)
"""

class UserMetrics(commands.Cog, name='User Metrics'):
  def __init__(self, bot):
    self.bot = bot
    self.db_path = "databases/user_data.db"

    # buffer 100 or so messages before inserting into the database
    self.msg_queue = queue.Queue(maxsize=100)

    # TODO(qlavi): now it is getting painful to store it here. move it out
    self.general_channel_ids = [
      988202173760405557, # general
      991016201813626880] # off-topic
    self.help_channel_ids = [
      988498937793105920, # help 1
      988498938782953532, # help 2
      988498939818934272] # help 3

  async def add_all_users(self, db, member_list):
    members = ((member.id, member.name) for member in member_list)
    insert_query = "INSERT OR IGNORE INTO Users(id, name) VALUES (?, ?)"
    await db.executemany(insert_query, members)

  async def add_all_channels(self, db, channel_list):
    channels = ((channel.id, channel.name) for channel in channel_list)
    insert_query = "INSERT OR IGNORE INTO Channels(id, name) VALUES (?, ?)"
    await db.executemany(insert_query, channels)

  def cog_unload(self):
    print(f'saving cached messages to {self.db_path}')
    loop = asyncio.get_running_loop()
    asyncio.ensure_future(self.flush(), loop=loop)

  @commands.Cog.listener()
  async def on_ready(self):
    if os.path.exists(self.db_path): return
    print(f'creating: {self.db_path}')
    guild = self.bot.get_guild(int(self.bot.guild_id))

    async with aiosqlite.connect(self.db_path) as db:
      await db.execute(create_messages_table)
      await db.execute(create_users_table)
      await db.execute(create_channels_table)

      if self.guild:
        await self.add_all_channels(db, self.guild.channels)
        await self.add_all_users(db, self.guild.members)
        await db.commit()

  def pull_msg_from_queue(self):
    while not self.msg_queue.empty():
      yield self.msg_queue.get()

  async def flush(self):
    # TODO(qlavi): There is a possibilty that this queue might get a new message WHILE being emptied.
    insert_query = "INSERT INTO Messages(id, on_channel_id, user_id, time_stamp, content) VALUES (?, ?, ?, ?, ?)"
    async with aiosqlite.connect(self.db_path) as db:
      await db.executemany(insert_query, self.pull_msg_from_queue())
      await db.commit()

  @commands.command(name='force_push', help='used for adding new data which might be cached')
  async def force_push(self, ctx): await self.flush()

  @commands.Cog.listener()
  async def on_message(self, msg):
    cmd_list = [f'{self.bot.command_prefix}{cmd.name}' for cmd in self.bot.commands]
    if msg.author.bot or (msg.content in cmd_list) or len(msg.content) == 0: return

    if self.msg_queue.full(): await self.flush()
    self.msg_queue.put(
      (f'{msg.id}', f'{msg.channel.id}', msg.author.id, msg.created_at.timestamp(), msg.content))

  @commands.command(name='user_activity', help="renders a plot of members' activity")
  async def user_activity(self, ctx):
    # TODO(qlavi): setup a Async Background Task so data manipulation is not done here.
    Past_Days = 21
    Max_Users = 10
    Discord_Bg_Color = '#36393E'
    plt.style.use('dark_background')

    plt.rcParams['axes.facecolor']    = Discord_Bg_Color
    plt.rcParams['savefig.facecolor'] = Discord_Bg_Color
    fig, axs = plt.subplots(nrows=2)

    async with aiosqlite.connect('databases/user_data.db') as db:
      msgs_table = await db.execute_fetchall('SELECT * FROM Messages')

    msgs = pd.DataFrame(msgs_table, columns=['id', 'on_channel_id', 'user_id', 'time_stamp', 'content'])
    msgs = msgs[msgs['time_stamp'] > time.time() - (86400 * Past_Days)]
    active_users_general = Counter(msgs[msgs['on_channel_id'].isin(self.general_channel_ids)]['user_id'].values)
    active_users_help = Counter(msgs[msgs['on_channel_id'].isin(self.help_channel_ids)]['user_id'].values)

    users = []
    msg_counts = []
    guild = self.bot.get_guild(int(self.bot.guild_id))

    for user_id, count in active_users_general.most_common(Max_Users):
      member = await guild.fetch_member(user_id)
      users.append(member.name)
      msg_counts.append(count)

    axs[0].barh(users, msg_counts)
    axs[0].set_title(f'General Users Activity [Past {Past_Days} Days]')
    axs[0].set_ylim(axs[0].get_ylim()[::-1])

    users = []
    msg_counts = []
    for user_id, count in active_users_help.most_common(Max_Users):
      member = await guild.fetch_member(user_id)
      users.append(member.name)
      msg_counts.append(count)

    axs[1].barh(users, msg_counts)
    axs[1].set_title(f'Helping Users Activity [Past {Past_Days} Days]')
    axs[1].set_ylim(axs[1].get_ylim()[::-1])
    axs[1].set_xlabel('Message Volume')

    plt.tight_layout()

    image = io.BytesIO()
    plt.savefig(image, format='png')
    image.seek(0)

    await ctx.send('', files=[nextcord.File(image, 'user_activity.png')])

def setup(bot):
  bot.add_cog(UserMetrics(bot))
