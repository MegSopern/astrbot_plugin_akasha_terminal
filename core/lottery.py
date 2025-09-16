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
    def __init__(self, items_with_weight):
        # 初始化抽奖配置
        self.weapon_data = None  # 初始化属性

        try:
            file_path = Path(__file__).parent.parent / "data" / "weapon.json"
            self.weapon_data = read_json(file_path)

        except FileNotFoundError:
            logger.error(f"抽奖配置文件未找到: {file_path}")
        except json.JSONDecodeError:
            logger.error(f"抽奖配置文件格式错误: {file_path}")
        except Exception as e:
            logger.error(f"加载抽奖配置时发生未知错误: {e}")

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
