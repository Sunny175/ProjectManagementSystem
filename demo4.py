import os

from pynput import keyboard, mouse
from PIL import ImageGrab
import random
import time
import pyrebase
import platform
from datetime import datetime
import pandas as pd

t = 0
firebaseConfig = {
    "apiKey": "AIzaSyD7w1t1naoWypN4eEZUhiZhq0l0G6xMdvk",
    "authDomain": "projectmanagement-3e8a8.firebaseapp.com",
    "databaseURL": "https://projectmanagement-3e8a8-default-rtdb.firebaseio.com",
    "projectId": "projectmanagement-3e8a8",
    "storageBucket": "projectmanagement-3e8a8.appspot.com",
    "messagingSenderId": "398063613086",
    "appId": "1:398063613086:web:05aa2a5bb0ccb2d821778f",
    "measurementId": "G-DBHEPCK3YT"
}
system_name = platform.uname().node

firebase = pyrebase.initialize_app(firebaseConfig)
storage = firebase.storage()
database = firebase.database()


def take_screenshot():
    snapshot = ImageGrab.grab()
    file_name = str(time.time())
    file_name = file_name.strip() + ".png"
    snapshot.save(file_name)
    storage.child(system_name + "/" + file_name).put(file_name)
    os.remove(file_name)


now = datetime.now()
current_time = now.strftime("%d/%m/%y %H:%M:%S")
data = {
    'Status': ['Active'],
    'Time': [current_time]
}

main = pd.DataFrame(data, columns=['Status', 'Time'])

while t != 700:
    now = datetime.now()
    current_time = now.strftime("%d/%m/%y %H:%M:%S")
    with keyboard.Events() as events:
        event = events.get(1.0)

    with mouse.Events() as events1:
        event1 = events1.get(1.0)

    if event is None and event1 is None and t == random.randint(300, 500):
        df2 = {'Status': ['Inactive'], 'Time': [current_time]}
        df2 = pd.DataFrame(df2)
        main = pd.concat([main, df2], ignore_index=True)
        t = 0
    elif event is not None or event1 is not None:
        df2 = {'Status': ['Active'], 'Time': [current_time]}
        df2 = pd.DataFrame(df2)
        main = pd.concat([main, df2], ignore_index=True)

    elif t == random.randint(50, 200):
        take_screenshot()
    t += 1
    print(t)

main['Time'] = pd.to_datetime(main['Time'])
# create a new column with the time differences between rows
main['time_diff'] = main['Time'].diff()

# filter the DataFrame to only include active times
active_df = main[main['Status'] == 'Active']

# calculate the total active time
total_active_time = active_df['time_diff'].sum()

# print the total active time
current_date = str(datetime.now().date())
total_active_time = str(total_active_time).split()
data = {
    "pc_name": system_name,
    "active_time": total_active_time[2],
    "date": current_date
}

database.child("Time").push(data)
