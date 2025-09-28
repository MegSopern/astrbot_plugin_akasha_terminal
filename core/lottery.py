import json
import random
from pathlib import Path

import astrbot.api.message_components as Comp

from ..utils.utils import read_json, write_json


class Lottery:
    def __init__(self):
        """
        初始化抽奖系统
        """
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        self.backpack_path = (
            BASE_DIR
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_backpack"
        )
        self.user_data_path = (
            BASE_DIR / "plugin_data" / "astrbot_plugin_akasha_terminal" / "user_data"
        )
        self.weapon_path = (
            BASE_DIR
            / "plugin"
            / "astrbot_plugin_akasha_terminal"
            / "data"
            / "weapon.json"
        )
        # 字典，定义每个星级下的具体武器 {weapon_star: [weapon_id1,weapon_id2, ...]}
        weapon_star_data = self.load_weapon_data()
        # 星级池子含有的武器列表
        self.weapon_all_data = weapon_star_data or {}
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

    async def update_data(
        self, user_id: str, target_weapon_id: str, user_data, user_backpack
    ) -> bool:
        """
        更新用户背包数据

        :param user_id: 用户ID
        :param weapon_id: 武器ID
        :param user_data: 用户数据字典
        :param user_backpack: 用户背包字典
        :return: 更新成功返回True，否则返回False
        """
        # 读取现有用户数据
        weapon_new_data = await self.get_weapon_info(target_weapon_id)
        weapon_star = weapon_new_data.get("class")
        # 初始化抽奖记录结构（如果不存在）
        if "weapon" not in user_backpack:
            user_backpack["weapon"] = {
                "纠缠之缘": 0,
                "总抽奖次数": 0,
                "武器计数": {},
                "武器详细": {
                    "三星武器": {"数量": 0, "详细信息": {}},
                    "四星武器": {"数量": 0, "详细信息": {}},
                    "五星武器": {"数量": 0, "详细信息": {}},
                },
            }
        if user_backpack["weapon"] and isinstance(weapon_new_data, dict):
            # 更新抽奖记录
            user_backpack["weapon"]["总抽奖次数"] += 1
            user_backpack["weapon"]["武器计数"][target_weapon_id] = (
                user_backpack["weapon"]["武器计数"].get(target_weapon_id, 0) + 1
            )
            user_backpack["weapon"]["武器详细"][weapon_star]["数量"] += 1
            if (
                target_weapon_id
                not in user_backpack["weapon"]["武器详细"][weapon_star]["详细信息"]
            ):
                user_backpack["weapon"]["武器详细"][weapon_star]["详细信息"][
                    target_weapon_id
                ] = weapon_new_data
            # 写回更新后的数据
            await write_json(self.user_data_path / f"{user_id}.json", user_data)
            await write_json(self.backpack_path / f"{user_id}.json", user_backpack)
            return True
        else:
            return False

    async def weapon_draw(self, user_id: str, count: int = 10):
        """
        执行武器抽卡\n
        :param user_id: 用户ID
        :param count: 抽卡数量
        1. 根据权重选择一个主奖项（星级）
        2. 从对应的子奖项列表中随机选择一个具体武器
        3. 返回主奖项和子奖项

        :return: 抽中的奖项
        """
        user_data = await read_json(self.user_data_path / f"{user_id}.json") or {}
        user_backpack = await read_json(self.backpack_path / f"{user_id}.json") or {}
        entangled_fate = user_backpack.get("weapon", {}).get("纠缠之缘", 0)
        cost = 10 * count  # 每次抽卡消耗10个纠缠之缘
        # 检查纠缠之缘是否足够
        if entangled_fate < cost:
            message = [
                Comp.At(qq=user_id),
                Comp.Plain(f"\n需要{cost}颗纠缠之缘，你当前只有{entangled_fate}颗\n"),
                Comp.Plain("💡 可以通过[签到]获得更多纠缠之缘"),
            ]
            return message
        # 扣减纠缠之缘
        user_backpack["weapon"]["纠缠之缘"] = entangled_fate - cost
        rand_num = random.uniform(0, self.total_weight)
        # 确定随机数落在哪个区间
        current = 0
        for i, weight in enumerate(self.weights):
            current += weight
            if current >= rand_num:
                # 选中的武器星级
                weapon_star = self.items[i]
                if weapon_star == "三星武器":
                    rarity = 3
                elif weapon_star == "四星武器":
                    rarity = 4
                elif weapon_star == "五星武器":
                    rarity = 5
                if (
                    weapon_star in self.weapon_all_data
                    and self.weapon_all_data[weapon_star]
                ):
                    # 从该池中随机选择一个具体的武器（等概率）
                    target_weapon_id = str(
                        random.choice(self.weapon_all_data[weapon_star])
                    )
                    target_weapon_data = await self.get_weapon_info(target_weapon_id)
                    message = ""
                    weapon_count = user_backpack["weapon"]["武器详细"][weapon_star][
                        "数量"
                    ]
                    if rarity >= 4:
                        if rarity == 5:
                            message = "\n🎉 恭喜获得传说武器！"
                            # 五星武器增加好感度
                            spouse_name = str(
                                user_data.get("home", {}).get("spouse_name")
                            )
                            if spouse_name:
                                user_data["home"]["love"] = (
                                    user_data.get("home", {}).get("love", 0) + 20
                                )
                                message += (
                                    f"\n💕 {spouse_name}为你的好运感到高兴！好感度+20"
                                )
                        # 组装消息段
                        message = [
                            Comp.At(qq=user_id),
                            Comp.Plain(f"恭喜获得{'⭐' * rarity} {rarity}星武器！"),
                            Comp.Plain(f"⚔️ {target_weapon_data['name']}\n"),
                            Comp.Plain(f"📦 这是你的第{weapon_count}把{rarity}星武器"),
                        ]
                        # if image_path:
                        #     message.append(Comp.Image.fromFileSystem(image_path))  # 从本地文件目录发送图片

                    else:
                        # 三星武器收集起来
                        three_star_results = {}
                        three_star_results.append(
                            {
                                "name": target_weapon_data["name"],
                                "count": weapon_count,
                                # 'imagePath': image_path
                            }
                        )
                    # ----- 批量发送三星武器结果 -----
                    if three_star_results:
                        if count == 1:
                            w = three_star_results[0]
                            message = [
                                Comp.At(qq=user_id),
                                Comp.Plain(f"⭐⭐⭐ 获得三星武器：{w['name']}\n"),
                                Comp.Plain(f"📦 这是你的第{w['count']}把三星武器\n"),
                                Comp.Plain(
                                    f"💎 剩余纠缠之缘：{user_backpack['weapon']['纠缠之缘']}"
                                ),
                            ]
                            # if w["imagePath"]:
                            #     message.append(Comp.Image.fromFileSystem(w["imagePath"]))

                        # else:
                        #     lines = [
                        #         Comp.At(qq=user_id),
                        #         Comp.Plain("\n★★★ 获得三星武器：\n"),
                        #     ]
                        #     for w in three_star_results:
                        #         lines.append(f"⚔️ {w['name']} (第{w['count']}把)")
                        #     lines.append(
                        #         f"\n💎 剩余纠缠之缘：{user_backpack['weapon']['纠缠之缘']}"
                        #     )

                        #     if total_luck_bonus > 0:
                        #         lines.append(f"\n🍀 幸运加成：+{total_luck_bonus}%")
                        #         if location_desc:
                        #             lines.append(f" ({location_desc})")
                        #         if love_bonus > 0:
                        #             lines.append(f" ({wife_name}的祝福)")
                        #         if time_desc:
                        #             lines.append(f" ({time_desc})")

                        #     await e.reply("".join(lines))
                    # 更新用户数据
                    await self.update_data(
                        user_id, target_weapon_id, user_data, user_backpack
                    )
                return message
