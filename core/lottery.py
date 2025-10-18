import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from astrbot.api import logger
from astrbot.api.star import StarTools
from astrbot.core import AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from ..utils.utils import (
    get_at_ids,
    get_user_data_and_backpack,
    read_json,
    seconds_to_duration,
    write_json,
)


class Lottery:
    def __init__(self, config: AstrBotConfig):
        """初始化抽奖系统，设置路径和概率参数"""
        # 设置文件路径
        PLUGIN_DATA_DIR = Path(StarTools.get_data_dir("astrbot_plugin_akasha_terminal"))
        PLUGIN_DIR = Path(__file__).resolve().parent.parent
        self.backpack_path = PLUGIN_DATA_DIR / "user_backpack"
        self.user_data_path = PLUGIN_DATA_DIR / "user_data"
        self.weapon_file = PLUGIN_DIR / "data" / "weapon.json"
        self.image_base_path = PLUGIN_DIR / "resources" / "weapon_image"

        # 从配置接收抽卡冷却时间
        self.draw_card_cooldown = config.get("draw_card_cooldown", 10)  # 默认10秒

        # 存储群冷却时间
        self.group_cooldowns = {}  # {group_id: 下次可抽卡时间}

        # 加载武器数据（按星级分类）{weapon_star: [weapon_id1,weapon_id2, ...]}
        self.weapon_all_data = self.load_weapon_data() or {}

        # 武器池子概率配置
        self.five_star_prob = 1  # 五星武器基础概率1%
        self.four_star_prob = 5  # 四星武器基础概率5%
        self.three_star_prob = (
            100 - self.five_star_prob - self.four_star_prob
        )  # 三星武器基础概率94%

    def check_group_cooldown(self, group_id: str) -> int:
        """检查群冷却时间，返回剩余冷却秒数，0表示无冷却"""
        if not group_id:
            return 0  # 私聊无冷却

        current_time = datetime.now(ZoneInfo("Asia/Shanghai")).timestamp()
        next_available_time = self.group_cooldowns.get(group_id, 0)
        remaining = next_available_time - current_time
        return max(remaining, 0)

    def update_group_cooldown(self, group_id: str):
        """更新群冷却时间"""
        if not group_id or self.draw_card_cooldown <= 0:
            return

        current_time = datetime.now(ZoneInfo("Asia/Shanghai")).timestamp()
        self.group_cooldowns[group_id] = current_time + self.draw_card_cooldown

    def load_weapon_data(self):
        """
        加载武器数据并按星级分类（300-399:三星, 400-499:四星, 500-599:五星）
        """
        try:
            with open(self.weapon_file, "r", encoding="utf-8") as f:
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
            logger.error(
                f"错误：未找到武器数据文件 {self.weapon_file}，请检查路径是否正确"
            )
            return None
        except json.JSONDecodeError:
            logger.error("错误：武器数据文件格式不正确")
            return None

    # 根据武器id获取武器详细信息
    async def get_weapon_info(self, weapon_id: str) -> dict | None:
        """
        根据武器ID获取武器详细信息\n
        :param weapon_id: 武器ID
        :return: 武器详细信息
        """
        weapon_data = await read_json(self.weapon_file)
        return weapon_data.get(weapon_id)

    async def update_data(
        self, user_id: str, target_weapon_id: str, user_data, user_backpack
    ) -> bool:
        """更新用户背包和武器数据"""
        try:
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
        except Exception as e:
            logger.error(f"更新用户数据失败: {str(e)}")
            return False

    async def handle_single_draw(
        self, user_id, user_data, user_backpack, five_star_miss, four_star_miss
    ):
        """处理单次抽卡逻辑，返回抽卡结果和更新后的计数"""
        try:
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
            message_snippets = ""

            # 更新保底计数和好感度
            if weapon_star == "五星武器":
                five_star_miss = 0
                four_star_miss = 0
                message_snippets += "🎉 恭喜获得传说武器！\n"
                if spouse_name not in [0, None, ""]:
                    user_data["home"]["love"] += 30
                    message_snippets += (
                        f"💖 {spouse_name}为你的好运感到高兴！好感度+30\n"
                    )
                else:
                    message_snippets += "💡 你未绑定伴侣，绑定伴侣可提升好感度\n"
            elif weapon_star == "四星武器":
                five_star_miss += 1
                four_star_miss = 0
                message_snippets += "🎉 恭喜获得稀有武器！\n"
                if spouse_name not in [0, None, ""]:
                    user_data["home"]["love"] += 20
                    message_snippets += (
                        f"💖 {spouse_name}为你的好运感到高兴！好感度+20\n"
                    )
                else:
                    message_snippets += "💡 你未绑定伴侣，绑定伴侣可提升好感度\n"
            else:
                five_star_miss += 1
                four_star_miss += 1

            # 更新用户数据
            user_backpack["weapon"]["未出五星计数"] = five_star_miss
            user_backpack["weapon"]["未出四星计数"] = four_star_miss
            await self.update_data(user_id, target_weapon_id, user_data, user_backpack)

            # 添加武器图片
            weapon_name = target_weapon_info["name"]
            weapon_image = f"{weapon_name}.png"
            weapon_image_path = str(self.image_base_path / weapon_star / weapon_image)

            return (
                {
                    "star": weapon_star,
                    "info": target_weapon_info,
                    "message_snippets": message_snippets,
                },
                five_star_miss,
                four_star_miss,
                current_five_star_prob,
                weapon_image_path,
            )
        except Exception as e:
            logger.error(f"处理单次抽卡失败: {str(e)}")
            return None, None, None, None, None

    async def weapon_draw(self, event: AiocqhttpMessageEvent, count: int = 1):
        """执行武器抽卡主逻辑"""
        try:
            group_id = event.get_group_id() or None
            if group_id:
                remaining_time = self.check_group_cooldown(group_id)
            if remaining_time > 0:
                return (
                    f"抽卡冷却中，还剩{seconds_to_duration(remaining_time):.1f}",
                    None,
                )
            user_id = str(event.get_sender_id())
            user_data, user_backpack = await get_user_data_and_backpack(user_id)
            weapon_data = user_backpack["weapon"]
            entangled_fate = weapon_data["纠缠之缘"]
            cost = count  # 每次消耗1颗纠缠之缘

            # 检查资源是否充足
            if entangled_fate < cost:
                return (
                    f"\n需要{cost}颗纠缠之缘，你当前只有{entangled_fate}颗\n",
                    "💡 可通过[签到]获得更多纠缠之缘",
                )
            user_backpack["weapon"]["纠缠之缘"] -= cost

            # 初始化保底计数
            five_star_miss = weapon_data["未出五星计数"]
            four_star_miss = weapon_data["未出四星计数"]
            draw_results = []
            image_paths = []
            all_snippets = ""

            # 更新冷却时间
            self.update_group_cooldown(group_id)

            # 处理多次抽卡
            for _ in range(count):
                (
                    result,
                    five_star_miss,
                    four_star_miss,
                    current_five_star_prob,
                    weapon_image_path,
                ) = await self.handle_single_draw(
                    user_id, user_data, user_backpack, five_star_miss, four_star_miss
                )
                five_star_prob = current_five_star_prob
                draw_results.append(result)
                all_snippets += result["message_snippets"]
                image_paths.append(weapon_image_path)

            if count == 1:
                image_paths = str(image_paths[0])  # 单抽只返回一张图片
            # 构建最终消息
            message = "\n【武器抽卡结果】：\n"
            message += all_snippets

            # 分离高星和三星结果
            high_star = [
                r for r in draw_results if r["star"] in ["五星武器", "四星武器"]
            ]
            three_star = [r for r in draw_results if r["star"] == "三星武器"]

            # 添加高星结果
            if high_star:
                for res in high_star:
                    star = res["star"]
                    info = res["info"]
                    rarity = 5 if star == "五星武器" else 4
                    total_count = user_backpack["weapon"]["武器详细"][star]["数量"]
                    message += (
                        f"🎉 恭喜获得{'⭐' * rarity} {rarity}星武器！\n"
                        f"⚔️ 武器名称：{info['name']}\n"
                        f"📦 累计拥有：第{total_count}把{rarity}星武器\n\n"
                    )

            # 添加三星结果
            if three_star:
                three_star_names = [res["info"]["name"] for res in three_star]
                total_three_star = user_backpack["weapon"]["武器详细"]["三星武器"][
                    "数量"
                ]
                message += (
                    f"⭐⭐⭐ 获得三星武器共{len(three_star)}把：\n"
                    f"⚔️ 名称：{', '.join(three_star_names)}\n"
                    f"📦 累计拥有：{total_three_star}把三星武器\n\n"
                )

            # 添加保底进度和剩余资源
            message += (
                f"💎 剩余纠缠之缘：{user_backpack['weapon']['纠缠之缘']}\n"
                f"🎯 五星保底进度：{five_star_miss}/80（当前概率：{five_star_prob:.2f}%）\n"
                f"🎯 四星保底进度：{four_star_miss}/10\n"
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

            return message, image_paths
        except Exception as e:
            logger.error(f"武器抽卡失败: {str(e)}")
            return "抽武器时发生错误，请稍后再试~", None

    async def calculate_sign_rewards(self, user_data, user_backpack, base_reward):
        """计算签到奖励及加成"""
        CN_TIMEZONE = ZoneInfo("Asia/Shanghai")
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

    async def daily_sign_in(self, event: AiocqhttpMessageEvent):
        """处理每日签到逻辑"""
        try:
            user_id = str(event.get_sender_id())
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
                return "你今天已经签到过啦，明天再来吧~\n"

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
            message = ""

            # 新用户提示
            if judge_new_user:
                message += "🎉 欢迎来到虚空武器抽卡系统！\n💎 注册成功，获得初始纠缠之缘5颗\n\n"

            # 基础奖励消息
            message += (
                f"✅ 签到成功！获得{reward_data['total_reward'] - 5 if judge_new_user else reward_data['total_reward']}颗纠缠之缘\n"
                f"💎 当前拥有：{user_backpack['weapon']['纠缠之缘']}颗纠缠之缘\n"
                f"📅 当前连续签到{reward_data['streak_count']}天\n"
                f"💡 可以使用[抽武器]来获得强力装备！\n"
            )

            # 幸运奖励消息
            if reward_data["lucky_reward"] > 0:
                message += f"🎁 幸运奖励：额外获得{reward_data['lucky_reward']}颗纠缠之缘！\n\n"
            try:
                # 加成信息
                bonus_messages = ""
                if reward_data["location_bonus"] != 0:
                    bonus_messages += f"📍 位置加成：{reward_data['location_desc']} +({reward_data['location_bonus']:+d})\n"
                if reward_data["house_bonus"] > 0:
                    bonus_messages += f"🏠 房屋加成：+{reward_data['house_bonus']}\n"
                if reward_data["love_bonus"] > 0:
                    bonus_messages += f"💕 {reward_data['spouse_name']}的爱意加成：+{reward_data['love_bonus']}\n"
                if reward_data["streak_bonus"] > 0:
                    bonus_messages += f"🔥 连续签到{reward_data['streak_count']}天加成：+{reward_data['streak_bonus']}\n"
            except Exception as e:
                logger.error(f"构建加成信息失败: {str(e)}")
            if bonus_messages:
                message += bonus_messages

            # 保存数据
            await write_json(self.backpack_path / f"{user_id}.json", user_backpack)
            return message
        except Exception as e:
            logger.error(f"签到失败: {str(e)}")
            return "签到时发生错误，请稍后再试~"

    async def show_my_weapons(self, event: AiocqhttpMessageEvent):
        """展示个人武器库统计信息"""
        try:
            user_data, user_backpack = await self.get_user_data_and_backpack(
                event.get_sender_id()
            )
            weapon_data = user_backpack["weapon"]
            weapon_details = weapon_data["武器详细"]

            # 总武器数量检查
            total_weapons = sum(
                star_data["数量"] for star_data in weapon_details.values()
            )
            if total_weapons == 0:
                return "你还没有任何武器，快去抽卡吧！\n💡 使用[抽武器]开始你的冒险之旅吧！"

            # 基础信息
            location_name = user_data["home"]["place"]
            spouse_name = user_data["home"]["spouse_name"]
            spouse_love = user_data["home"]["love"]
            house_level = user_data["home"]["house_level"]

            # 计算最爱武器
            favorite_weapon = max(
                weapon_data["武器计数"].items(), key=lambda x: x[1], default=(None, 0)
            )
            favorite_weapon_id, favorite_weapon_count = favorite_weapon
            favorite_weapon_name = ""
            rarity = 0
            if favorite_weapon_id:
                try:
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
                except Exception as e:
                    logger.error(f"处理最爱武器时出错: {str(e)}")
                    return "处理最爱武器时出错，请稍后再试~"
            # 计算战斗力和成就
            five_star_count = weapon_details["五星武器"]["数量"]
            four_star_count = weapon_details["四星武器"]["数量"]
            three_star_count = weapon_details["三星武器"]["数量"]
            combat_power = (
                five_star_count * 500 + four_star_count * 100 + three_star_count * 20
            )
            achievements = ""
            if five_star_count >= 10:
                achievements += "🏆 五星武器收藏家"
            if four_star_count >= 50:
                achievements += "💎 四星武器大师"
            if len(weapon_data["武器计数"]) >= 100:
                achievements += "🎖️ 武器收集达人"

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
            message = "\n🗡️ 你的武器图鉴\n"
            message += f"📍 当前位置：{location_name}\n"
            if spouse_name not in ["", None]:
                message += f"💖 伴侣：{spouse_name}（好感度：{spouse_love}）\n"
            else:
                message += "💡 你还没有伴侣，绑定伴侣可提升好感度\n"
            if house_level > 0:
                message += f"🏠 房屋等级：{house_level}\n"
            else:
                message += "💡 你还没有房屋，快去建造吧！\n"
            message += f"💪 战斗力：{combat_power} ({combat_rank})\n\n"

            # 成就展示
            message += "🎖️ 成就徽章\n"
            message += "━━━━━━━━━━━━━━━\n"
            message += f"{', '.join(achievements) if achievements else '暂无成就'}\n"
            message += "━━━━━━━━━━━━━━━\n\n"

            # 武器统计
            message += "📊 武器统计\n"
            message += "━━━━━━━━━━━━━━━\n"
            message += f"🎯 总计：{total_weapons}把武器\n"
            message += f"⭐⭐⭐⭐⭐ 五星：{five_star_count}把\n"
            message += f"⭐⭐⭐⭐ 四星：{four_star_count}把\n"
            message += f"⭐⭐⭐ 三星：{three_star_count}把\n\n"

            # 最爱武器
            message += "💖 你最喜欢的武器是：\n"
            message += "━━━━━━━━━━━━━━━\n"
            message += (
                f"{'⭐' * rarity} {favorite_weapon_name}*{favorite_weapon_count}\n"
            )
            message += "━━━━━━━━━━━━━━━\n\n"

            # 各星级武器列表
            star_to_num = {"三": 3, "四": 4, "五": 5}
            for star in ["五星武器", "四星武器", "三星武器"]:
                stars = "⭐" * int(star_to_num[star[0]])
                details = weapon_details[star]
                if details["数量"] > 0:
                    message += f"{stars} {star}列表：\n"
                    for item in details["详细信息"][:5]:  # 显示前5个
                        count = weapon_data["武器计数"].get(item["id"], 0)
                        message += f"- {item['name']}（{count}把）\n"
                    if len(details["详细信息"]) > 5:
                        message += f"... 还有{len(details['详细信息']) - 5}件未显示\n"

            # 随机伴侣评论
            if spouse_name not in [None, ""] and random.random() < 0.1:
                spouse_comments = [
                    f"{spouse_name}想要试试你的武器",
                    f"{spouse_name}觉得你很有安全感",
                    f"{spouse_name}对你的实力很有信心",
                    f"{spouse_name}想要和你一起战斗",
                    f"你的武器让{spouse_name}也想去冒险了！",
                ]
                message += f"\n💬 {random.choice(spouse_comments)}\n"
            return message
        except Exception as e:
            logger.error(f"展示武器库失败: {str(e)}")
            return "获取武器库信息时出错，请稍后再试~"

    async def handle_cheat_command(self, event: AiocqhttpMessageEvent, input_str: str):
        """处理开挂命令"""
        try:
            to_user_id = None
            amount = None
            parts = input_str.strip().split()
            if not parts:
                return (
                    False,
                    "请指定增加的纠缠之缘数量，使用方法:\n"
                    "/开挂 数量 \n"
                    "或：/开挂 @用户/qq号 数量",
                )
            to_user_ids = get_at_ids(event)
            if isinstance(to_user_ids, list) and to_user_ids:
                to_user_id = to_user_ids[0]
            try:
                if to_user_id:
                    if len(parts) >= 2:
                        amount = int(parts[1])
                    else:
                        return (
                            False,
                            "请指定增加的纠缠之缘数量，使用方法:\n"
                            "/开挂 @用户/qq号 数量",
                        )
                else:
                    if len(parts) >= 2 and parts[0].isdigit():
                        to_user_id = parts[0]
                        amount = int(parts[1])
                    else:
                        amount = int(parts[0])
            except ValueError:
                return (False, "金额必须是整数，请重新输入")
            if not to_user_id:
                to_user_id = str(event.get_sender_id())
            if amount <= 0:
                return False, "增加的金额必须为正整数"
            user_backpack = await self.get_user_data_and_backpack(
                to_user_id, only_data_or_backpack="user_backpack"
            )
            user_backpack["weapon"]["纠缠之缘"] += amount
            await write_json(self.backpack_path / f"{to_user_id}.json", user_backpack)
            return (
                True,
                f"成功为用户{to_user_id}增加 {amount} 颗纠缠之缘\n"
                f"当前纠缠之缘: {user_backpack['weapon']['纠缠之缘']}颗",
            )
        except Exception as e:
            logger.error(f"处理开挂命令失败: {str(e)}")
            return False, "处理开挂命令时发生错误，请稍后再试~"
