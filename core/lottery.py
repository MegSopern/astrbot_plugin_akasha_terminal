import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import astrbot.api.message_components as Comp
from astrbot.api import logger

from ..utils.utils import create_user_data, read_json, write_json


class Lottery:
    def __init__(self):
        """初始化抽奖系统，设置路径和概率参数"""
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        plugin_data_dir = base_dir / "plugin_data" / "astrbot_plugin_akasha_terminal"
        self.backpack_path = plugin_data_dir / "user_backpack"
        self.user_data_path = plugin_data_dir / "user_data"
        self.weapon_path = (
            base_dir
            / "plugin"
            / "astrbot_plugin_akasha_terminal"
            / "data"
            / "weapon.json"
        )
        # 加载武器数据（按星级分类）{weapon_star: [weapon_id1,weapon_id2, ...]}
        self.weapon_all_data = self.load_weapon_data() or {}

        # 武器池子概率配置
        self.five_star_prob = 1  # 五星武器基础概率1%
        self.four_star_prob = 5  # 四星武器基础概率5%
        self.three_star_prob = (
            100 - self.five_star_prob - self.four_star_prob
        )  # 三星武器基础概率94%

    @staticmethod
    def load_weapon_data(file_path="weapon.json"):
        """
        加载武器数据并按星级分类（300-399:三星, 400-499:四星, 500-599:五星）
        """
        try:
            with open(
                Path(__file__).parent.parent / file_path, "r", encoding="utf-8"
            ) as f:
                weapon_data = json.load(f)

            # 按ID范围分类武器（300-399:三星, 400-499:四星, 500-599:五星）
            three_star, four_star, five_star = [], [], []
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
                    logger.warning(f"忽略非数字ID的武器: {weapon_key}")
                    continue

            return {
                "三星武器": three_star,
                "四星武器": four_star,
                "五星武器": five_star,
            }
        except FileNotFoundError:
            logger.error(f"未找到武器数据文件: {file_path}")
            return None
        except json.JSONDecodeError:
            logger.error(f"武器数据文件格式错误: {file_path}")
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

    async def get_user_data_and_backpack(self, user_id: str):
        """获取用户数据和背包数据（不存在则创建）"""
        user_data_file = self.user_data_path / f"{user_id}.json"
        if not user_data_file.exists():
            await create_user_data(user_id)
        user_data = await read_json(user_data_file)
        user_backpack = await read_json(self.backpack_path / f"{user_id}.json") or {}

        # 初始化武器背包结构
        if "weapon" not in user_backpack:
            user_backpack["weapon"] = {
                "纠缠之缘": 0,
                "总抽卡次数": 0,
                "武器计数": {},
                "武器详细": {
                    "三星武器": {"数量": 0, "详细信息": []},
                    "四星武器": {"数量": 0, "详细信息": []},
                    "五星武器": {"数量": 0, "详细信息": []},
                },
                "未出五星计数": 0,
                "未出四星计数": 0,
            }
        return user_data, user_backpack

    async def update_data(
        self, user_id: str, target_weapon_id: str, user_data, user_backpack
    ) -> bool:
        """更新用户背包和武器数据"""
        weapon_info = await self.get_weapon_info(target_weapon_id)
        if not weapon_info:
            return False

        weapon_star = weapon_info["class"]
        weapon_detail = user_backpack["weapon"]["武器详细"][weapon_star]

        # 更新抽卡次数和武器计数
        user_backpack["weapon"]["总抽卡次数"] += 1
        user_backpack["weapon"]["武器计数"][target_weapon_id] = (
            user_backpack["weapon"]["武器计数"].get(target_weapon_id, 0) + 1
        )

        # 首次获得该武器时添加详细信息
        if not any(
            item["id"] == target_weapon_id for item in weapon_detail["详细信息"]
        ):
            weapon_detail["数量"] += 1
            weapon_detail["详细信息"].append(weapon_info)

        # 保存数据
        await write_json(self.user_data_path / f"{user_id}.json", user_data)
        await write_json(self.backpack_path / f"{user_id}.json", user_backpack)
        return True

    async def handle_single_draw(
        self, user_id, user_data, user_backpack, five_star_miss, four_star_miss
    ):
        """处理单次抽卡逻辑，返回抽卡结果和更新后的计数"""
        # 计算五星概率（64抽后每抽+6.5%）
        current_five_star_prob = self.five_star_prob
        if five_star_miss > 64:
            current_five_star_prob += (five_star_miss - 64) * 6.5
            current_five_star_prob = min(current_five_star_prob, 100)

        # 四星保底判定（每10抽必出）
        is_four_star_guarantee = four_star_miss > 9

        # 随机判定星级
        rand_val = random.uniform(0, 100)
        if rand_val <= current_five_star_prob:
            weapon_star = "五星武器"
        elif is_four_star_guarantee or rand_val <= (
            current_five_star_prob + self.four_star_prob
        ):
            weapon_star = "四星武器"
        else:
            weapon_star = "三星武器"

        # 随机选择武器
        target_weapon_id = str(random.choice(self.weapon_all_data[weapon_star]))
        target_weapon_info = await self.get_weapon_info(target_weapon_id)
        spouse_name = user_data.get("home", {}).get("spouse_name")
        message_snippets = []

        # 更新保底计数和好感度
        if weapon_star == "五星武器":
            five_star_miss = 0
            four_star_miss = 0
            message_snippets.append("🎉 恭喜获得传说武器！\n")
            if spouse_name not in [0, None, ""]:
                user_data["home"]["love"] += 30
                message_snippets.append(
                    f"💖 {spouse_name}为你的好运感到高兴！好感度+30\n"
                )
            else:
                message_snippets.append("💡 你未绑定伴侣，绑定伴侣可提升好感度\n")
        elif weapon_star == "四星武器":
            five_star_miss += 1
            four_star_miss = 0
            message_snippets.append("🎉 恭喜获得稀有武器！\n")
            if spouse_name not in [0, None, ""]:
                user_data["home"]["love"] += 20
                message_snippets.append(
                    f"💖 {spouse_name}为你的好运感到高兴！好感度+20\n"
                )
            else:
                message_snippets.append("💡 你未绑定伴侣，绑定伴侣可提升好感度\n")
        else:
            five_star_miss += 1
            four_star_miss += 1

        # 添加武器图片
        weapon_image_path = (
            Path(__file__).resolve().parent.parent
            / "resources"
            / "weapon_images"
            / "gacha.webp"
        )
        if weapon_image_path.exists():
            message_snippets.append(Comp.Image.fromFileSystem(weapon_image_path))

        # 更新用户数据
        user_backpack["weapon"]["未出五星计数"] = five_star_miss
        user_backpack["weapon"]["未出四星计数"] = four_star_miss
        await self.update_data(user_id, target_weapon_id, user_data, user_backpack)

        return (
            {
                "star": weapon_star,
                "info": target_weapon_info,
                "message_snippets": message_snippets,
            },
            five_star_miss,
            four_star_miss,
            current_five_star_prob,
        )

    async def weapon_draw(self, user_id: str, count: int = 1):
        """执行武器抽卡主逻辑"""
        user_data, user_backpack = await self.get_user_data_and_backpack(user_id)
        weapon_data = user_backpack["weapon"]
        entangled_fate = weapon_data["纠缠之缘"]
        cost = count  # 每次消耗1颗纠缠之缘

        # 检查资源是否充足
        if entangled_fate < cost:
            return [
                Comp.At(qq=user_id),
                Comp.Plain(f"\n需要{cost}颗纠缠之缘，你当前只有{entangled_fate}颗\n"),
                Comp.Plain("💡 可通过[签到]获得更多纠缠之缘"),
            ]
        user_backpack["weapon"]["纠缠之缘"] -= cost

        # 初始化保底计数
        five_star_miss = weapon_data["未出五星计数"]
        four_star_miss = weapon_data["未出四星计数"]
        draw_results = []
        all_snippets = []

        # 处理多次抽卡
        for _ in range(count):
            (
                result,
                five_star_miss,
                four_star_miss,
                current_five_star_prob,
            ) = await self.handle_single_draw(
                user_id, user_data, user_backpack, five_star_miss, four_star_miss
            )
            five_star_prob = current_five_star_prob
            draw_results.append(result)
            all_snippets.extend(result["message_snippets"])

        # 构建最终消息
        message = [Comp.At(qq=user_id), Comp.Plain("\n【武器抽卡结果】：\n")]
        message.extend(all_snippets)

        # 分离高星和三星结果
        high_star = [r for r in draw_results if r["star"] in ["五星武器", "四星武器"]]
        three_star = [r for r in draw_results if r["star"] == "三星武器"]

        # 添加高星结果
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

        # 添加三星结果
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

        # 添加保底进度和剩余资源
        message.extend(
            [
                Comp.Plain(f"💎 剩余纠缠之缘：{user_backpack['weapon']['纠缠之缘']}\n"),
                Comp.Plain(
                    f"🎯 五星保底进度：{five_star_miss}/80（当前概率：{five_star_prob:.2f}%）\n"
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

    async def calculate_sign_rewards(self, user_data, user_backpack, base_reward):
        """计算签到奖励及加成"""
        CN_TIMEZONE = ZoneInfo("Asia/Shanghai")
        today = datetime.now(CN_TIMEZONE).date().strftime("%Y-%m-%d")
        last_sign = user_backpack["sign_info"].get("last_sign", "")
        streak_count = user_backpack["sign_info"].get("streak_days", 0)

        # 连续签到逻辑
        if last_sign == (datetime.now(CN_TIMEZONE).date() - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        ):
            streak_count += 1
        else:
            streak_count = 1
        if streak_count > 30:
            streak_count = 1  # 上限30天

        # 连续签到加成（每3天+1，最多+5）
        streak_bonus = min(streak_count // 3, 5)

        # 位置加成
        location_bonus = 0
        location_desc = ""
        current_place = user_data.get("home", {}).get("place", "home")
        location_config = {
            "prison": (-1, "监狱环境恶劣"),
            "home": (0, "家的温馨"),
            "bank": (1, "银行的稳定收益"),
            "city": (2, "城市的繁华带来额外收益"),
            "business": (3, "商业区的商机"),
        }
        if current_place in location_config:
            location_bonus, location_desc = location_config[current_place]

        # 房屋加成
        house_bonus = user_data.get("house", {}).get("house_level", 1) // 2

        # 好感度加成
        love_bonus = 0
        spouse_name = ""
        if user_data.get("home", {}).get("spouse_id") not in [0, None, ""]:
            spouse_name = user_data["home"].get("spouse_name", "伴侣")
            love_bonus = user_data["home"].get("love", 0) // 50

        # 幸运奖励（10%概率）
        lucky_reward = 5 + random.randint(0, 10) if random.random() < 0.1 else 0
        total_reward = (
            base_reward + location_bonus + house_bonus + love_bonus + streak_bonus
        )

        return {
            "streak_count": streak_count,
            "streak_bonus": streak_bonus,
            "location_bonus": location_bonus,
            "location_desc": location_desc,
            "house_bonus": house_bonus,
            "love_bonus": love_bonus,
            "spouse_name": spouse_name,
            "lucky_reward": lucky_reward,
            "total_reward": total_reward,
        }

    async def daily_sign_in(self, user_id: str):
        """处理每日签到逻辑"""
        CN_TIMEZONE = ZoneInfo("Asia/Shanghai")
        user_data, user_backpack = await self.get_user_data_and_backpack(user_id)
        today = datetime.now(CN_TIMEZONE).date().strftime("%Y-%m-%d")

        # 初始化签到信息
        judge_new_user = False
        base_reward = 1
        if "sign_info" not in user_backpack:
            user_backpack["sign_info"] = {"last_sign": "", "streak_days": 0}
            base_reward += 5  # 新用户额外5颗
            judge_new_user = True

        # 检查是否已签到
        if user_backpack["sign_info"]["last_sign"] == today:
            return [
                Comp.At(qq=user_id),
                Comp.Plain("\n你今天已经签到过啦，明天再来吧~"),
            ]

        # 计算奖励
        reward_data = await self.calculate_sign_rewards(
            user_data, user_backpack, base_reward
        )

        # 更新签到信息
        user_backpack["sign_info"]["last_sign"] = today
        user_backpack["sign_info"]["streak_days"] = reward_data["streak_count"]

        # 更新纠缠之缘数量
        total_reward = reward_data["total_reward"] + reward_data["lucky_reward"]
        user_backpack["weapon"]["纠缠之缘"] += total_reward

        # 构建消息
        message = [Comp.At(qq=user_id), Comp.Plain("\n")]

        # 新用户提示
        if judge_new_user:
            message.append(
                Comp.Plain(
                    "🎉 欢迎来到虚空武器抽卡系统！\n💎 注册成功，获得初始纠缠之缘5颗\n\n"
                )
            )

        # 基础奖励消息
        message.extend(
            [
                Comp.Plain(
                    f"✅ 签到成功！获得{reward_data['total_reward'] - 5 if judge_new_user else reward_data['total_reward']}颗纠缠之缘\n"
                ),
                Comp.Plain(
                    f"💎 当前拥有：{user_backpack['weapon']['纠缠之缘']}颗纠缠之缘\n"
                ),
                Comp.Plain(f"📅 当前连续签到{reward_data['streak_count']}天\n"),
                Comp.Plain("💡 可以使用[抽武器]来获得强力装备！\n"),
            ]
        )

        # 幸运奖励消息
        if reward_data["lucky_reward"] > 0:
            message.append(
                Comp.Plain(
                    f"🎁 幸运奖励：额外获得{reward_data['lucky_reward']}颗纠缠之缘！\n\n"
                )
            )

        # 加成信息
        bonus_messages = []
        if reward_data["location_bonus"] != 0:
            bonus_messages.append(
                f"📍 位置加成：{reward_data['location_desc']} +({reward_data['location_bonus']:+d})\n"
            )
        if reward_data["house_bonus"] > 0:
            bonus_messages.append(f"🏠 房屋加成：+{reward_data['house_bonus']}\n")
        if reward_data["love_bonus"] > 0:
            bonus_messages.append(
                f"💕 {reward_data['spouse_name']}的爱意加成：+{reward_data['love_bonus']}\n"
            )
        if reward_data["streak_bonus"] > 0:
            bonus_messages.append(
                f"🔥 连续签到{reward_data['streak_count']}天加成：+{reward_data['streak_bonus']}\n"
            )

        if bonus_messages:
            message.append(Comp.Plain(" ".join(bonus_messages)))

        # 保存数据
        await write_json(self.backpack_path / f"{user_id}.json", user_backpack)
        return message

    async def show_my_weapons(self, user_id: str):
        """展示个人武器库统计信息"""
        user_data, user_backpack = await self.get_user_data_and_backpack(user_id)
        weapon_data = user_backpack["weapon"]
        weapon_details = weapon_data["武器详细"]

        # 总武器数量检查
        total_weapons = sum(star_data["数量"] for star_data in weapon_details.values())
        if total_weapons == 0:
            return [
                Comp.At(qq=user_id),
                Comp.Plain("\n你还没有任何武器，快去抽卡吧！\n"),
                Comp.Plain("💡 使用[抽武器]开始你的冒险之旅吧！"),
            ]

        # 基础信息
        location_name = user_data["home"]["place"]
        spouse_name = user_data["home"]["spouse_name"]
        spouse_love = user_data["home"]["love"]
        house_level = user_data["house"]["house_level"]

        # 计算最爱武器
        favorite_weapon = max(
            weapon_data["武器计数"].items(), key=lambda x: x[1], default=(None, 0)
        )
        favorite_weapon_id, favorite_weapon_count = favorite_weapon
        favorite_weapon_name = ""
        rarity = 0
        if favorite_weapon_id:
            weapon_id_int = int(favorite_weapon_id)
            if 500 <= weapon_id_int < 600:
                rarity = 5
                star_key = "五星武器"
            elif 400 <= weapon_id_int < 500:
                rarity = 4
                star_key = "四星武器"
            else:
                rarity = 3
                star_key = "三星武器"

            for weapon in weapon_details[star_key]["详细信息"]:
                if weapon["id"] == favorite_weapon_id:
                    favorite_weapon_name = weapon["name"]
                    break

        # 计算战斗力和成就
        five_star_count = weapon_details["五星武器"]["数量"]
        four_star_count = weapon_details["四星武器"]["数量"]
        three_star_count = weapon_details["三星武器"]["数量"]
        combat_power = (
            five_star_count * 500 + four_star_count * 100 + three_star_count * 20
        )
        achievements = []
        if five_star_count >= 10:
            achievements.append("🏆 五星武器收藏家")
        if four_star_count >= 50:
            achievements.append("💎 四星武器大师")
        if len(weapon_data["武器计数"]) >= 100:
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
            Comp.Plain(f"📍 当前位置：{location_name}\n"),
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

        # 成就展示
        message.extend(
            [
                Comp.Plain("🎖️ 成就徽章\n"),
                Comp.Plain("━━━━━━━━━━━━━━━━\n"),
                Comp.Plain(
                    f"{', '.join(achievements) if achievements else '暂无成就'}\n\n"
                ),
            ]
        )

        # 武器统计
        message.extend(
            [
                Comp.Plain("━━━━━━━━━━━━━━━━\n"),
                Comp.Plain("📊 武器统计\n"),
                Comp.Plain(f"🎯 总计：{total_weapons}把武器\n"),
                Comp.Plain(f"⭐⭐⭐⭐⭐ 五星：{five_star_count}把\n\n"),
                Comp.Plain(f"⭐⭐⭐⭐ 四星：{four_star_count}把\n"),
                Comp.Plain(f"⭐⭐⭐ 三星：{three_star_count}把\n"),
            ]
        )

        # 最爱武器
        message.extend(
            [
                Comp.Plain("💖 你最喜欢的武器是：\n"),
                Comp.Plain("━━━━━━━━━━━━━━━━\n"),
                Comp.Plain(
                    f"{'⭐' * rarity} {favorite_weapon_name}*{favorite_weapon_count}\n\n"
                ),
            ]
        )

        # 各星级武器列表
        for star in ["五星武器", "四星武器", "三星武器"]:
            stars = "⭐" * int(star[0])
            details = weapon_details[star]
            if details["数量"] > 0:
                message.append(Comp.Plain(f"{stars} {star}列表：\n"))
                for item in details["详细信息"][:5]:  # 显示前5个
                    count = weapon_data["武器计数"].get(item["id"], 0)
                    message.append(Comp.Plain(f"- {item['name']}（{count}把）\n"))
                if len(details["详细信息"]) > 5:
                    message.append(
                        Comp.Plain(f"... 还有{len(details['详细信息']) - 5}件未显示\n")
                    )

        # 随机伴侣评论
        if spouse_name not in [None, ""] and random.random() < 0.1:
            spouse_comments = [
                f"{spouse_name}想要试试你的武器",
                f"{spouse_name}觉得你很有安全感",
                f"{spouse_name}对你的实力很有信心",
                f"{spouse_name}想要和你一起战斗",
                f"你的武器让{spouse_name}也想去冒险了！",
            ]
            message.append(Comp.Plain(f"\n💬 {random.choice(spouse_comments)}\n"))

        return message
