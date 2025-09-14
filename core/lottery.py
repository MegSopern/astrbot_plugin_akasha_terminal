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

    async def draw(self, times: int):
        xhh = int(1)  # 默认抽奖次数
        weapon = []  # 存储抽取武器名称

        for xhh in range(0, times):
            q = random.randint(1, 313)
            # 五星
            if q >= 1 and q <= 32:
                a = random.randint(44, 75)  # 抽取武器序号
                weapon_id = str(a)
                b = self.weapon_data[weapon_id]["name"]  # 武器名称
                weapon.append(b)
            # 四星
            elif q >= 33 and q <= 93:
                a = random.randint(1, 30)
                weapon_id = str(a)
                b = self.weapon_data[weapon_id]["name"]
                weapon.append(b)
            # 三星
            elif q >= 94 and q <= 313:
                a = random.randint(31, 43)
                weapon_id = str(a)
                b = self.weapon_data[weapon_id]["name"]
                weapon.append(b)
