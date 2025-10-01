import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import astrbot.api.message_components as Comp

from ..utils.utils import create_user_data, read_json, write_json


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
        # 仅在首次获得该武器时增加数量及添加武器详细信息
        weapon_ids = [
            item["id"]
            for item in user_backpack["weapon"]["武器详细"][weapon_star]["详细信息"]
        ]
        if target_weapon_id not in weapon_ids:
            user_backpack["weapon"]["武器详细"][weapon_star]["数量"] += 1
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
        if not (self.user_data_path / f"{user_id}.json").exists():
            await create_user_data(user_id)
        user_data = await read_json(self.user_data_path / f"{user_id}.json")
        user_backpack = await read_json(self.backpack_path / f"{user_id}.json") or {}
        weapon_data = user_backpack.get("weapon", {})
        entangled_fate = weapon_data.get("纠缠之缘", 0)

        # 检查纠缠之缘是否足够（1颗/次）
        cost = 1 * count
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
        # 用于每次抽卡的基础概率
        base_five_star_prob = self.five_star_prob
        base_four_star_prob = self.four_star_prob
        draw_results = []  # 存储每抽结果

        # 循环处理每一次抽卡（逐抽计算保底概率）
        message = [Comp.At(qq=user_id), Comp.Plain("\n【武器抽卡结果】：\n")]
        for _ in range(count):
            # 计算本次5星概率（阶梯保底：64抽后每抽+6.5%）
            current_five_star_prob = base_five_star_prob
            if five_star_miss > 64:
                current_five_star_prob += (five_star_miss - 64) * 6.5
                current_five_star_prob = min(current_five_star_prob, 100)  # 上限100%

            # 判断是否触发4星保底（每10抽必出，即连续9抽未出则第10抽保底）
            is_four_star_guarantee = four_star_miss >= 9

            # 随机判定抽中星级（0-100随机数，匹配概率规则）
            rand_val = random.uniform(0, 100)
            weapon_star = None

            # 优先判定5星（基础1%+阶梯保底）
            if rand_val <= current_five_star_prob:
                weapon_star = "五星武器"
            # 再判定4星（基础5%或保底强制）：五星已排除，剩余5%四星
            elif is_four_star_guarantee or rand_val <= (
                current_five_star_prob + base_four_star_prob
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
                spouse_name = str(user_data.get("home", {}).get("spouse_name"))
                # 更新保底计数（关键：根据抽中结果重置/累加计数）
                if weapon_star == "五星武器":
                    five_star_miss = 0  # 中5星：双计数重置
                    four_star_miss = 0
                    message.append("\n🎉 恭喜获得传说武器！")
                    if spouse_name:
                        user_data["home"]["love"] = (
                            user_data.get("home", {}).get("love", 0) + 30
                        )
                        message.append(
                            f"💖 {spouse_name}为你的好运感到高兴！好感度+30\n"
                        )
                    else:
                        message.append("\n💡 你未绑定伴侣，绑定伴侣可提升好感度")
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
        message = [Comp.At(qq=user_id), Comp.Plain("\n【武器抽卡结果】：\n", message)]
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
                message.extend(
                    [
                        Comp.Plain(f"🎉 恭喜获得{'⭐' * rarity} {rarity}星武器！\n"),
                        Comp.Plain(f"⚔️ 名称：{info['name']}\n"),
                        Comp.Plain(f"📦 累计拥有：第{total_count}把{rarity}星武器\n\n"),
                    ]
                )

        # 显示三星结果
        if three_star:
            three_star_names = [res["info"]["name"] for res in three_star]
            total_three_star = user_backpack["weapon"]["武器详细"]["三星武器"]["数量"]
            message.extend(
                [
                    Comp.Plain(f"⭐⭐⭐ 获得三星武器共{len(three_star)}把：\n"),
                    Comp.Plain(f"⚔️ {', '.join(three_star_names)}\n"),
                    Comp.Plain(f"📦 累计拥有：{total_three_star}把三星武器\n\n"),
                ]
            )

        # 显示保底进度与剩余资源
        message.extend(
            [
                Comp.Plain(f"💎 剩余纠缠之缘：{user_backpack['weapon']['纠缠之缘']}\n"),
                Comp.Plain(
                    f"🎯 五星保底进度：{five_star_miss}/80（当前概率：{self.five_star_prob:.1f}%）\n"
                ),
                Comp.Plain(f"🎯 四星保底进度：{four_star_miss}/10"),
            ]
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
        return message

    async def daily_sign_in(self, user_id: str):
        """处理每日签到，获取纠缠之缘"""
        # 设置「中国标准时间」
        CN_TIMEZONE = ZoneInfo("Asia/Shanghai")
        if not (self.user_data_path / f"{user_id}.json").exists():
            await create_user_data(user_id)
        user_data = await read_json(self.user_data_path / f"{user_id}.json")
        user_backpack = await read_json(self.backpack_path / f"{user_id}.json") or {}
        today = datetime.now(CN_TIMEZONE).date().strftime("%Y-%m-%d")
        message = [Comp.At(qq=user_id), Comp.Plain("\n")]
        # 初始化签到数据及检测是否为首次签到的新用户
        if "sign_info" not in user_backpack:
            user_backpack["sign_info"] = {"last_sign": "", "streak_days": 0}
            judge_new_user = True
        # 检查是否已签到
        if user_backpack["sign_info"]["last_sign"] == today:
            message.append(Comp.Plain("你今天已经签到过啦，明天再来吧~"))
            return message
        base_reward = 1
        location_bonus, house_bonus, love_bonus, streak_bonus = 0, 0, 0, 0
        # 新用户奖励
        if judge_new_user:
            message.append(
                Comp.Plain(
                    "🎉 欢迎来到虚空武器抽卡系统！\n💎 注册成功，获得初始纠缠之缘5颗\n\n"
                )
            )
            base_reward += 5
        # 更新签到信息
        last_sign = user_backpack["sign_info"]["last_sign"]
        if last_sign == (datetime.now(CN_TIMEZONE).date() - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        ):
            if user_backpack["sign_info"]["streak_days"] <= 30:
                user_backpack["sign_info"]["streak_days"] += 1
            else:
                user_backpack["sign_info"]["streak_days"] = 1  # 连续签到天数上限30天
        else:
            user_backpack["sign_info"]["streak_days"] = 1
        streak_count = user_backpack["sign_info"]["streak_days"]
        user_backpack["sign_info"]["last_sign"] = today
        # 连续签到加成（每3天+1，最多+5）
        streak_bonus = min(streak_count // 3, 5)

        # 位置加成计算
        if user_data["home"] and "place" in user_data["home"]:
            current_place = user_data.get("home", {}).get("place", "home")
            location_config = {
                "city": (2, "城市的繁华带来额外收益"),
                "business": (3, "商业区的商机"),
                "bank": (1, "银行的稳定收益"),
                "prison": (-1, "监狱环境恶劣"),
                "home": (0, "家的温馨"),
            }
            if current_place in location_config:
                location_bonus, location_desc = location_config[current_place]
            else:
                location_bonus, location_desc = 0, "未知地点"

        # 房屋等级加成
        if user_data["house"] and "house_level" in user_data["house"]:
            house_level = user_data.get("house", {}).get("house_level", 1)
            house_bonus = house_level // 2  # 每2级+1颗纠缠之缘

        # 好感度加成
        if user_data["home"] and "spouse_id" in user_data["home"]:
            spouse_name = user_data["home"].get("spouse_name", "伴侣")
            spouse_id = user_data["home"].get("spouse_id")
            if spouse_id and spouse_id not in [0, None, "", "0"]:
                love_level = user_data["home"].get("love", 0)
                love_bonus = love_level // 50  # 每50好感度+1

        total_reward = (
            base_reward + location_bonus + house_bonus + love_bonus + streak_bonus
        )

        message.extend(
            [
                Comp.Plain(f"✅ 签到成功！获得{total_reward - 5}颗纠缠之缘\n"),
                Comp.Plain(
                    f"💎 当前拥有：{user_backpack['weapon']['纠缠之缘']}颗纠缠之缘\n"
                ),
                Comp.Plain(f"📅 当前连续签到{streak_count}天\n"),
                Comp.Plain("💡 可以使用[抽武器]来获得强力装备！\n"),
            ]
        )

        # 幸运奖励事件（10%概率）
        lucky_reward = 0
        if random.random() < 0.1:
            lucky_reward = 5 + random.randint(0, 10)
            message.append(
                Comp.Plain(f"🎁 幸运奖励：额外获得{lucky_reward}颗纠缠之缘！\n\n")
            )
        # 添加各种加成信息
        if location_bonus != 0:
            message.append(f"📍 位置加成：{location_bonus:+d} ({location_desc})")
        if house_bonus > 0:
            message.append(f"🏠 房屋加成：+{house_bonus}")
        if love_bonus > 0:
            message.append(f"💕 {spouse_name}的爱意加成：+{love_bonus}")
        if streak_bonus > 0:
            message.append(f"🔥 连续签到{streak_count}天加成：+{streak_bonus}")
        # 更新用户金钱
        user_backpack["weapon"]["纠缠之缘"] += total_reward + lucky_reward
        await write_json(self.backpack_path / f"{user_id}.json", user_backpack)
        return message

    # 个人武器库展示功能
    async def show_my_weapons(self, user_id: str):
        """展示个人武器的统计信息"""
        user_data = await read_json(self.user_data_path / f"{user_id}.json")
        user_backpack = await read_json(self.backpack_path / f"{user_id}.json") or {}
        weapon_data = user_backpack.get("weapon", {})
        weapon_details = weapon_data.get("武器详细", {})

        total = sum(star_data.get("数量", 0) for star_data in weapon_details.values())
        if total == 0:
            return [
                Comp.At(qq=user_id),
                Comp.Plain("\n你还没有任何武器，快去抽卡吧！\n"),
                Comp.Plain("💡 使用[抽武器]开始你的冒险之旅吧！"),
            ]

        location_name = user_data.get("home", {}).get("place", "home")
        spouse_name = user_data["home"]["spouse_name"]
        spouse_love = user_data["home"]["love"]
        if user_data["house"] and "house_level" in user_data["house"]:
            house_level = user_data["house"]["house_level"]

        # 计算最爱武器（拥有数量最多的武器）
        rarity = None
        favorite_weapon = max(
            weapon_data.get("武器计数", {}).items(),
            key=lambda x: x[1],
            default=(None, 0),
        )
        favorite_weapon_id = favorite_weapon[0]
        favorite_weapon_count = favorite_weapon[1]
        if 500 <= favorite_weapon_id < 600:
            rarity = 5
            for weapon in user_backpack["weapon"]["武器详细"]["五星武器"]["详细信息"]:
                if weapon["id"] == favorite_weapon_id:
                    favorite_weapon_name = weapon["name"]
                    break
        elif 400 <= favorite_weapon_id < 500:
            rarity = 4
            for weapon in user_backpack["weapon"]["武器详细"]["四星武器"]["详细信息"]:
                if weapon["id"] == favorite_weapon_id:
                    favorite_weapon_name = weapon["name"]
                    break
        elif 300 <= favorite_weapon_id < 400:
            rarity = 3
            for weapon in user_backpack["weapon"]["武器详细"]["三星武器"]["详细信息"]:
                if weapon["id"] == favorite_weapon_id:
                    favorite_weapon_name = weapon["name"]
                    break
        achievements = []
        # 战斗力评估及判定徽章成就
        for weapons_by_rarity, weapons_by_data in weapon_details.items():
            if weapons_by_rarity == "五星武器" and weapons_by_data["数量"] > 0:
                five_star_combat_power = weapons_by_data["数量"] * 500
                if weapons_by_data["数量"] >= 10:
                    achievements.append("🏆 五星武器收藏家")
            elif weapons_by_rarity == "四星武器" and weapons_by_data["数量"] > 0:
                four_star_combat_power = weapons_by_data["数量"] * 100
                if weapons_by_data["数量"] >= 50:
                    achievements.append("💎 四星武器大师")
            elif weapons_by_rarity == "三星武器" and weapons_by_data["数量"] > 0:
                three_star_combat_power = weapons_by_data["数量"] * 20
            combat_power = (
                five_star_combat_power
                + four_star_combat_power
                + three_star_combat_power
            )
        total_weapons = len(weapon_data.get("武器计数", {}))
        if total_weapons >= 100:
            achievements.append("🎖️ 武器收集达人")
        # 战斗力评级
        if combat_power >= 3000:
            combat_rank = "🔥 传奇战士"
        elif combat_power >= 1500:
            combat_rank = "⚔️ 精英战士"
        elif combat_power >= 500:
            combat_rank = "🛡️ 熟练战士"
        else:
            combat_rank = "🗡️ 新手战士"
        # 构建消息
        message = [
            Comp.At(qq=user_id),
            Comp.Plain("\n🗡️ 你的武器图鉴\n"),
            Comp.Plain(f"📍 当前位置：{location_name}"),
            Comp.Plain(
                f"💖 伴侣：{spouse_name}（好感度：{spouse_love}）\n"
                if spouse_name not in ["", None]
                else "💡 你还没有伴侣，绑定伴侣可提升好感度\n"
            ),
            Comp.Plain(
                f"🏠 房屋等级：{house_level}\n"
                if house_level
                else "💡 你还没有房屋，快去建造吧！\n"
            ),
            Comp.Plain(f"💪 战斗力：{combat_power} ({combat_rank})\n\n"),
        ]
        # 成就徽章展示

        message.extend(
            [
                Comp.Plain("🎖️ 成就徽章\n"),
                Comp.Plain("━━━━━━━━━━━━━━━━\n"),
                Comp.Plain(f"{', '.join(achievements)}\n"),
            ]
        )
        # 基础统计信息
        message.extend(
            [
                Comp.Plain("━━━━━━━━━━━━━━━━\n"),
                Comp.Plain("📊 武器统计\n"),
                Comp.Plain(f"🎯 总计：{total}把武器\n"),
                Comp.Plain(f"⭐⭐⭐ 三星：{weapon_details['三星武器']['数量']}把\n"),
                Comp.Plain(f"⭐⭐⭐⭐ 四星：{weapon_details['四星武器']['数量']}把\n"),
                Comp.Plain(
                    f"⭐⭐⭐⭐⭐ 五星：{weapon_details['五星武器']['数量']}把\n\n"
                ),
            ]
        )
        # 显示最爱武器
        message.extend(
            [
                Comp.Plain("💖 你最喜欢的武器是：\n"),
                Comp.Plain("━━━━━━━━━━━━━━━━\n"),
                Comp.Plain(
                    f"{'⭐' * rarity} {favorite_weapon_name}*{favorite_weapon_count}\n"
                ),
            ]
        )

        # 添加各星级武器列表
        for star in ["五星武器", "四星武器", "三星武器"]:
            stars = "⭐" * int(star[0])
            details = weapon_details.get(star, {})
            if details.get("数量", 0) > 0:
                message.append(Comp.Plain(f"{stars} {star}列表：\n"))
                for item in details.get("详细信息", [])[:5]:  # 只显示前5个
                    count = weapon_data.get("武器计数", {}).get(item["id"], 0)
                    message.append(Comp.Plain(f"- {item['name']}（{count}把）\n"))
                if len(details.get("详细信息", [])) > 5:
                    message.append(
                        Comp.Plain(f"... 还有{len(details['详细信息']) - 5}件未显示\n")
                    )
        if spouse_name not in ["", None] and random.random() < 0.1:
            spouse_comments = [
                f"{spouse_name}想要试试你的武器",
                f"{spouse_name}觉得你很有安全感",
                f"{spouse_name}对你的实力很有信心",
                f"{spouse_name}想要和你一起战斗",
                f"你的武器让{spouse_name}也想去冒险了！",
            ]
            target_comments = random.choice(spouse_comments)
            message.append(Comp.Plain(f"\n💬 {target_comments}\n"))
        return message
