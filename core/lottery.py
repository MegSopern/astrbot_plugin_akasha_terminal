import json
import random
from pathlib import Path

from astrbot.api import logger

from ..utils.utils import read_json, write_json


class Lottery:
    def __init__(self):
        """
        初始化抽奖系统
        """
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.backpack_path = (
            BASE_DIR.parent.parent
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_backpack"
        )
        self.weapon_path = BASE_DIR / "data" / "weapon.json"
        # 字典，定义每个星级下的具体武器 {weapon_star: [weapon_id1,weapon_id2, ...]}
        weapon_star_data = self.load_weapon_data()
        # 星级池子含有的武器列表
        self.weapon_star_data = weapon_star_data if weapon_star_data else {}
        pool_weights = {"三星武器": 17, "四星武器": 2, "五星武器": 1}
        self.items = list(pool_weights.keys())
        self.weights = list(pool_weights.values())
        self.total_weight = sum(self.weights)

    def load_weapon_data(file_path="weapon.json"):
        """加载武器数据并按星级分类"""
        try:
            # 读取JSON文件
            with open(
                Path(__file__).parent.parent / file_path, "r", encoding="utf-8"
            ) as f:
                weapon_data = json.load(f)

            # 按ID范围分类武器（300-399:三星, 400-499:四星, 500-599:五星）
            three_star = []
            four_star = []
            five_star = []

            for weapon_key in weapon_data.keys():
                try:
                    # 提取武器id
                    weapon_id = int(weapon_key)
                    if 300 <= weapon_id <= 399:
                        three_star.append(weapon_id)
                    elif 400 <= weapon_id <= 499:
                        four_star.append(weapon_id)
                    elif 500 <= weapon_id <= 599:
                        five_star.append(weapon_id)
                except ValueError:
                    # 忽略非数字ID的武器
                    continue
            return {
                "三星武器": three_star,
                "四星武器": four_star,
                "五星武器": five_star,
            }
        except FileNotFoundError:
            print(f"错误：未找到{file_path}文件，请确保文件在同目录下")
            return None
        except json.JSONDecodeError:
            print(f"错误：{file_path}文件格式不正确")
            return None

    # 根据武器id获取武器详细信息
    async def get_weapon_info(self, weapon_id: str) -> dict | None:
        """
        根据武器ID获取武器详细信息\n
        :param weapon_id: 武器ID
        :return: 武器详细信息
        """
        weapon_data = await read_json(self.weapon_path)
        return weapon_data.get(weapon_id)

    async def update_data(self, user_id: str, str, target_weapon_id: str) -> bool:
        """
        更新用户的抽奖数据，记录抽中的武器\n
        :param user_id: 用户ID
        :param star: 武器星级
        :param weapon: 武器名称
        :return: 是否更新成功
        """
        # 读取现有用户数据
        self.user_backpack_path = self.backpack_path / f"{user_id}.json"
        user_backpack = await read_json(self.user_backpack_path) or {}
        weapon_new_data = await self.get_weapon_info(target_weapon_id)
        # 初始化抽奖记录结构（如果不存在）
        if "weapon_data" not in user_backpack:
            user_backpack["weapon_data"] = {"total_draws": 0, "weapons": {}}
        if user_backpack["weapon_data"] and isinstance(weapon_new_data, dict):
            # 更新抽奖记录
            user_backpack["weapon_data"]["total_draws"] += 1
            user_backpack["weapon_data"]["weapons"].update(weapon_new_data)
            # 写回更新后的数据
            await write_json(self.user_backpack_path, user_backpack)
            return True
        else:
            return False

    async def draw_single(self, user_id: str):
        """
        执行单次抽奖\n
        1. 根据权重选择一个主奖项（星级）
        2. 从对应的子奖项列表中随机选择一个具体武器
        3. 返回主奖项和子奖项
        :return: 抽中的奖项
        """
        # 生成一个随机数（0到总权重之间）
        rand_num = random.uniform(0, self.total_weight)
        # 确定随机数落在哪个区间
        current = 0
        for i, weight in enumerate(self.weights):
            current += weight
            if current >= rand_num:
                # 选中的武器星级
                weapon_star = self.items[i]
                if (
                    weapon_star in self.weapon_star_data
                    and self.weapon_star_data[weapon_star]
                ):
                    # 从该池中随机选择一个具体的武器（等概率）
                    target_weapon_id = str(
                        random.choice(self.weapon_star_data[weapon_star])
                    )
                    # 更新用户数据
                    await self.update_data(user_id, target_weapon_id)
                    weapon_name = (await self.get_weapon_info(target_weapon_id)).get(
                        "name", "未知武器"
                    )
                    if weapon_star and weapon_name:
                        message = f"恭喜你抽中了{weapon_star}：{weapon_name}！\n"
                    else:
                        message = "抽奖失败，请稍后再试~"
            return message

    async def draw_multiple(self, user_id: str):
        """
        执行十连抽\n
        :param user_id: 用户ID
        :return: 抽中的奖项列表
        """
        message = "十连抽结果如下：\n"
        for _ in range(10):
            result = await self.draw_single(user_id)
            message += result
        return message
