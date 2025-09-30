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
        # 加载武器数据（按星级分类）{weapon_star: [weapon_id1,weapon_id2, ...]}
        self.weapon_all_data = self.load_weapon_data() or {}
        # 武器池子概率（固定概率）
        self.five_star_prob = 1  # 五星武器基础概率1%
        self.four_star_prob = 5  # 四星武器基础概率5%
        self.three_star_prob = (
            100 - self.five_star_prob - self.four_star_prob
        )  # 三星武器基础概率94%

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
        更新用户背包、抽奖次数及武器计数（新增保底计数初始化）\n
        :param user_id: 用户ID
        :param weapon_id: 武器ID
        :param user_data: 用户数据字典
        :param user_backpack: 用户背包字典
        :return: 更新成功返回True，否则返回False
        """
        # 读取现有用户数据
        weapon_new_data = await self.get_weapon_info(target_weapon_id)
        if not weapon_new_data:
            return False

        weapon_star = weapon_new_data.get("class")
        # 初始化背包结构（含保底计数字段）
        if "weapon" not in user_backpack:
            user_backpack["weapon"] = {
                "纠缠之缘": 0,
                "总抽卡次数": 0,
                "武器计数": {},
                "武器详细": {
                    "三星武器": {"数量": 0, "详细信息": {}},
                    "四星武器": {"数量": 0, "详细信息": {}},
                    "五星武器": {"数量": 0, "详细信息": {}},
                },
                "未出五星计数": 0,  # 新增：累计未出5星次数（用于5星保底）
                "未出四星计数": 0,  # 新增：累计未出4星次数（用于4星保底）
            }

        # 更新抽卡记录与武器计数
        user_backpack["weapon"]["总抽卡次数"] += 1
        user_backpack["weapon"]["武器计数"][target_weapon_id] = (
            user_backpack["weapon"]["武器计数"].get(target_weapon_id, 0) + 1
        )
        user_backpack["weapon"]["武器详细"][weapon_star]["数量"] += 1
        # 仅在首次获得该武器时添加详细信息
        weapon_ids = [
            item["id"]
            for item in user_backpack["weapon"]["武器详细"][weapon_star]["详细信息"]
        ]
        if target_weapon_id not in weapon_ids:
            user_backpack["weapon"]["武器详细"][weapon_star]["详细信息"].append(
                weapon_new_data
            )

        # 写回数据
        await write_json(self.user_data_path / f"{user_id}.json", user_data)
        await write_json(self.backpack_path / f"{user_id}.json", user_backpack)
        return True

    async def weapon_draw(self, user_id: str, count: int = 1):
        """
        执行武器抽卡\n
        :param user_id: 用户ID
        :param count: 抽卡次数（每次消耗10纠缠之缘）
        1. 根据权重选择一个主奖项（星级）
        2. 从对应的子奖项列表中随机选择一个具体武器
        3. 返回主奖项和子奖项

        :return: 抽中的奖项
        """
        user_data = await read_json(self.user_data_path / f"{user_id}.json") or {}
        user_backpack = await read_json(self.backpack_path / f"{user_id}.json") or {}
        weapon_data = user_backpack.get("weapon", {})
        entangled_fate = weapon_data.get("纠缠之缘", 0)

        # 检查纠缠之缘是否足够（10颗/次）
        cost = 10 * count
        if entangled_fate < cost:
            return [
                Comp.At(qq=user_id),
                Comp.Plain(f"\n需要{cost}颗纠缠之缘，你当前只有{entangled_fate}颗\n"),
                Comp.Plain("💡 可通过[签到]获得更多纠缠之缘"),
            ]
        # 扣减纠缠之缘
        user_backpack["weapon"]["纠缠之缘"] = entangled_fate - cost

        # 初始化保底计数（从用户数据读取，无则为0）
        five_star_miss = weapon_data.get("未出五星计数", 0)  # 累计未出5星次数
        four_star_miss = weapon_data.get("未出四星计数", 0)  # 累计未出4星次数
        draw_results = []  # 存储每抽结果

        # 循环处理每一次抽卡（逐抽计算保底概率）
        message = []
        for _ in range(count):
            # 计算本次5星概率（阶梯保底：64抽后每抽+6.5%）
            if five_star_miss > 64:
                self.five_star_prob = self.five_star_prob + (five_star_miss - 64) * 6.5
                self.five_star_prob = min(self.five_star_prob, 100)  # 上限100%

            # 判断是否触发4星保底（每10抽必出，即连续9抽未出则第10抽保底）
            is_four_star_guarantee = four_star_miss >= 9

            # 随机判定抽中星级（0-100随机数，匹配概率规则）
            rand_val = random.uniform(0, 100)
            weapon_star = None

            # 优先判定5星（基础1%+阶梯保底）
            if rand_val <= self.five_star_prob:
                weapon_star = "五星武器"
            # 再判定4星（基础5%或保底强制）：五星已排除，剩余5%四星
            elif is_four_star_guarantee or rand_val <= (
                self.five_star_prob + self.four_star_prob
            ):
                weapon_star = "四星武器"
            # 否则为3星（基础94%）
            else:
                weapon_star = "三星武器"

            # 选择对应星级的武器（等概率抽取）
            if (
                weapon_star in self.weapon_all_data
                and self.weapon_all_data[weapon_star]
            ):
                # 从该池中随机选择一个具体的武器（等概率）
                target_weapon_id = str(random.choice(self.weapon_all_data[weapon_star]))
                target_weapon_info = await self.get_weapon_info(target_weapon_id)
                draw_results.append({"star": weapon_star, "info": target_weapon_info})
                # 更新保底计数（关键：根据抽中结果重置/累加计数）
                if weapon_star == "五星武器":
                    five_star_miss = 0  # 中5星：双计数重置
                    four_star_miss = 0
                    message.append("\n🎉 恭喜获得传说武器！")
                    spouse_name = str(user_data.get("home", {}).get("spouse_name"))
                elif weapon_star == "四星武器":
                    five_star_miss += 1  # 中4星：5星计数累加，4星计数重置
                    four_star_miss = 0
                    message.append("🎉 恭喜获得稀有武器！\n")
                    if spouse_name:
                        user_data["home"]["love"] = (
                            user_data.get("home", {}).get("love", 0) + 20
                        )
                        message.append(
                            f"💖 {spouse_name}为你的好运感到高兴！好感度+20\n"
                        )
                    else:
                        message.append("\n💡 你未绑定伴侣，绑定伴侣可提升好感度")
                else:  # 中3星：双计数均累加
                    five_star_miss += 1
                    four_star_miss += 1

                weapon_image_path = (
                    Path(__file__).resolve().parent.parent
                    / "resources"
                    / "weapon_images"
                    / "gacha.webp"
                )
                # 从本地文件目录发送图片
                if weapon_image_path:
                    message.append(Comp.Image.fromFileSystem(weapon_image_path))
                # 实时更新用户数据（含保底计数）
                user_backpack["weapon"]["未出五星计数"] = five_star_miss
                user_backpack["weapon"]["未出四星计数"] = four_star_miss
                await self.update_data(
                    user_id, target_weapon_id, user_data, user_backpack
                )

        # 构建最终抽卡结果消息
        message = [Comp.At(qq=user_id), Comp.Plain("\n【武器抽卡结果】：\n")]
        # 分离高星（5/4星）和三星结果，优先显示高星
        high_star = [r for r in draw_results if r["star"] in ["五星武器", "四星武器"]]
        three_star = [r for r in draw_results if r["star"] == "三星武器"]

        # 显示高星结果
        if high_star:
            for res in high_star:
                star = res["star"]
                info = res["info"]
                rarity = 5 if star == "五星武器" else 4
                total_count = user_backpack["weapon"]["武器详细"][star]["数量"]
                message.append(
                    Comp.Plain(f"🎉 恭喜获得{'⭐' * rarity} {rarity}星武器！\n"),
                    Comp.Plain(f"⚔️ 名称：{info['name']}\n"),
                    Comp.Plain(f"📦 累计拥有：第{total_count}把{rarity}星武器\n\n"),
                )

        # 显示三星结果
        if three_star:
            three_star_names = [res["info"]["name"] for res in three_star]
            total_three_star = user_backpack["weapon"]["武器详细"]["三星武器"]["数量"]
            message.append(
                Comp.Plain(f"⭐⭐⭐ 获得三星武器共{len(three_star)}把：\n"),
                Comp.Plain(f"⚔️ {', '.join(three_star_names)}\n"),
                Comp.Plain(f"📦 累计拥有：{total_three_star}把三星武器\n\n"),
            )

        # 显示保底进度与剩余资源
        message.append(
            Comp.Plain(f"💎 剩余纠缠之缘：{user_backpack['weapon']['纠缠之缘']}\n"),
            Comp.Plain(
                f"🎯 五星保底进度：{five_star_miss}/80（当前概率：{self.five_star_prob:.1f}%）\n"
            ),
            Comp.Plain(f"🎯 四星保底进度：{four_star_miss}/10"),
        )

        # if image_path:
        #     message.append(Comp.Image.fromFileSystem(image_path))  # 从本地文件目录发送图片
        # if total_luck_bonus > 0:
        #     lines.append(f"\n🍀 幸运加成：+{total_luck_bonus}%")
        # if location_desc:
        #     lines.append(f" ({location_desc})")
        # if love_bonus > 0:
        #     lines.append(f" ({wife_name}的祝福)")
        # if time_desc:
        #     lines.append(f" ({time_desc})")
        # 更新用户数据
        await self.update_data(user_id, target_weapon_id, user_data, user_backpack)
        return message
