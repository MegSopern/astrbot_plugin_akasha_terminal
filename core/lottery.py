import json
import random
from pathlib import Path

import aiohttp  # noqa: F401
import astrbot.api.message_components as Comp
from aiocqhttp import CQHttp  # noqa: F401
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from ..utils.utils import read_json, write_json


class lottery:
 
    def __init__(self):
        self.weapon_data = None
        try:
            file_path = Path(__file__).parent.parent / "data" / "weapon.json"
            with open(file_path, 'r', encoding='utf-8') as f:
        self.weapon_data = json.load(f)
        
        def lottery(self):
            """执行一次抽奖"""
            self.items = ["五星", "四星", "三星"]  # 获奖
            self.weights = ["1", "2", "17"]  # 权重
            rand_sum = random.uniform(0, 20)  # 生成一个随机数,在0~20之间

            current = 0

            for i in range(0, 3):
                current += self.weights[i]
                if rand_sum <= current:
                    main_prizes = self.items

                    if main_prizes == "五星":
                        a = random.randint(500, 531)
                        print(f"{self.weapon_data[a]['name']}")

                    elif main_prizes == "四星":
                        a = random.randint(400, 429)
                        print(f"{self.weapon_data[a]['name']}")

                    else:
                        a = random.randint(300, 312)
                        print(f"{self.weapon_data[a]['name']}")

