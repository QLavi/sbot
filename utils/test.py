import tokenize
from io import BytesIO
# xdf = pd.read_csv('databases/messages.csv')
# df = xdf.loc[:, ['channel_id', 'author_id', 'timestamp']]
# df['created_at'] = pd.to_datetime(df['timestamp']).dt.strftime('%s')
# df.drop(['timestamp'], axis=1, inplace=True)

# df.to_csv('databases/readable.csv', header=False, index=False)

# xdf = pd.read_csv('user_metrics.csv')
# df = xdf.loc[:, ['timestamp', 'online']]
# df['total'] = xdf['online'] + xdf['offline'] + xdf['idle']
# df['time'] = pd.to_datetime(df['timestamp']).dt.strftime("%Y-%m-%d %H:%M:%S")
# df.drop(['timestamp'], axis=1, inplace=True)
# df = df[['time', 'online', 'total']]

# df.to_csv('databases/user_metrics.csv', header=False, index=False)

string = '"string", 20, "I hate, love myself"'

pos = 0
while True:
  while string[pos].isspace():
    pos += 1

  