import os, time, queue
from config import Config
from nextcord.ext import commands, tasks
import nextcord
import matplotlib.pyplot as plot
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import pandas as pd
from collections import Counter

class UserMetrics(commands.Cog, name='User Metrics'):
  def __init__(self, bot):
    self.bot = bot
    self.msg_queue = queue.Queue(maxsize=100)

  @commands.Cog.listener()
  async def on_ready(self):
    self.bg_data_process.start()
    self.bg_metrics_collect.start()

  def cog_unload(self):
    self.flush_messages()

  def get_msg_from_queue(self):
    while not self.msg_queue.empty():
      yield self.msg_queue.get()

  def flush_messages(self):
    print("saving cached data")
    buffer = ''.join(self.get_msg_from_queue())

    with open(Config.data_csv_path, 'a') as file:
      file.write('\n' + buffer)

  @commands.Cog.listener()
  async def on_message(self, msg):
    cmd_list = [f'{self.bot.command_prefix}{cmd.name}' for cmd in self.bot.commands]
    if msg.author.bot or (msg.content in cmd_list) or len(msg.content) == 0: return

    if self.msg_queue.full(): self.flush_messages()
    self.msg_queue.put(f'{msg.channel.id},{msg.author.id},{int(msg.created_at.timestamp())}' + '\n')

  @tasks.loop(hours=1)
  async def bg_metrics_collect(self):
    guild = self.bot.get_guild(int(self.bot.guild_id))

    online_count = 0
    for m in guild.members:
      if m.status == nextcord.Status.online:
        online_count += 1

    with open(Config.metrics_csv_path, 'a') as file:
      file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")},{online_count},{guild.member_count}' + '\n')

  @bg_metrics_collect.before_loop
  async def before_bg_task(self):
    await self.bot.wait_until_ready()

  @tasks.loop(hours=2)
  async def bg_data_process(self):
    guild = self.bot.get_guild(int(self.bot.guild_id))
    past_days = 10
    max_users = 10
    start = time.perf_counter()

    plot.style.use('dark_background')
    plot.rcParams['axes.facecolor'] = Config.bg_color
    plot.rcParams['savefig.facecolor'] = Config.bg_color
    _, axs = plot.subplots(nrows=2)

    df = pd.read_csv(Config.data_csv_path, names=['channel_id', 'user_id', 'created_at'])

    days_limit = time.time() - (86400 * past_days)
    df = df[df['created_at'] > days_limit]
    df['users'] = [guild.get_member(usr_id).name for usr_id in df['user_id'].values]
    df['date'] = pd.to_datetime(df['created_at'], unit='s')

    in_general_channels = df['channel_id'].isin(Config.general_channels)
    general_user_ids = Counter(df[in_general_channels]['users'].values).most_common(max_users)
    general_users = pd.DataFrame(general_user_ids, columns=['name', 'count'])

    in_help_channels = df['channel_id'].isin(Config.help_channels)
    help_user_ids = Counter(df[in_help_channels]['users'].values).most_common(max_users)
    help_users = pd.DataFrame(help_user_ids, columns=['name', 'count'])

    axs[0].barh(general_users['name'], general_users['count'])
    axs[0].set_title(f'General Users Activity [Past {past_days} Days')
    axs[0].set_ylim(axs[0].get_ylim()[::-1])

    axs[1].barh(help_users['name'], help_users['count'])
    axs[1].set_title(f'Helper Users Activity [Past {past_days} Days')
    axs[1].set_ylim(axs[1].get_ylim()[::-1])
    axs[1].set_xlabel('Message Volume')

    plot.tight_layout()
    plot.savefig('plots/user_activity.png', format='png')

    df = pd.read_csv(Config.metrics_csv_path, names=['time', 'online', 'total'], parse_dates=['time'])

    df.set_index('time', inplace=True)
    df = df.resample('60min').mean()

    _, axs = plot.subplots(nrows=2, sharex=True)
    axs[0].plot(df.index, df['online'], label='Active Users')
    axs[0].set_ylabel('Active Users')
    axs[0].set_title('Community Report')

    axs[1].set_ylabel('Total Users')
    axs[1].plot(df.index, df['total'], label='Total Users')
    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d\n%H:%M'))
    axs[1].xaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='lower'))

    plot.tight_layout()
    plot.savefig('plots/community_report.png', format='png')

    el = time.perf_counter() - start
    print(f'processing took: {el:.4f}secs')

  @bg_data_process.before_loop
  async def before_bg_task(self):
    await self.bot.wait_until_ready()

  @commands.command(help="renders plot of members' activity")
  async def user_activity(self, ctx):
    await ctx.send('', files=[nextcord.File('plots/user_activity.png')])

  @commands.command(help="no idea")
  async def report(self, ctx):
    await ctx.send('', files=[nextcord.File('plots/community_report.png')])

def setup(bot):
  bot.add_cog(UserMetrics(bot))
