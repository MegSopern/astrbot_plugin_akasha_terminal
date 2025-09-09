import re
import aiohttp  # noqa: F401
import astrbot.api.message_components as Comp
from aiocqhttp import CQHttp  # noqa: F401
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
import json
import time
from pathlib import Path
import random

key = random.randint(1,6)

class Task():
    def __init__(self,Task_name,Task_reward_1,Task_reward_2,Task_time):
        with ("./data/task.json","r") as Task_file:
              self.Task_name = Task_file["key"]["2"]
              self.Task_reward_1 = Task_file["key"]["4"]["1"]   #奖励钱
              self.Task_reward_2 = Task_file["key"]["4"]["3"]   #奖励quest_points
        #冷却时间 待定
        if key == 1:    self.Task_time = 1
        elif key == 2:    self.Task_time = 1
        elif key == 3:    self.Task_time = 1
        elif key == 4:    self.Task_time = 1
        elif key == 5:    self.Task_time = 1
        else: self.Task_time = 1


    
 
            