import sqlite3
import pandas as pd

with sqlite3.connect('databases/user_data.db') as db:
    data = db.execute('SELECT on_channel_id, user_id, time_stamp FROM Messages').fetchall()

df = pd.DataFrame(data, columns=['channel_id', 'user_id', 'time_stamp'])
df['time_stamp'] = df['time_stamp'].astype('int64')
df.to_csv('databases/user_data.csv', index=False, header=False)
