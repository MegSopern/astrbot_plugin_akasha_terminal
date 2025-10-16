import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from ..utils.text_formatter import TextFormatter
from ..utils.utils import (
    get_at_ids,
    read_json,
    read_json_sync,
    write_json,
    write_json_sync,
)


class Shop:
    def __init__(self):
        """初始化商店系统，设置数据目录和文件路径"""
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.data_dir = BASE_DIR / "data"
        self.shop_data_path = self.data_dir / "shop_data.json"
        self.backpack_path = (
            BASE_DIR.parent.parent
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_backpack"
        )
        self.user_data_path = (
            BASE_DIR.parent.parent
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_data"
        )
        self.config_path = (
            BASE_DIR.parent.parent
            / "config"
            / "astrbot_plugin_akasha_terminal_config.json"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)  # 确保数据目录存在
        self._init_default_data()

    def _init_default_data(self) -> None:
        """初始化默认商店数据和用户背包（仅当文件不存在时）"""
        # 设置「中国标准时间」
        self.CN_TIMEZONE = ZoneInfo("Asia/Shanghai")
        # 初始化商店数据
        shop_default_data = read_json_sync(self.shop_data_path)
        self.default_shop = {
            "items": {
                "爱心巧克力": {
                    "id": 1,
                    "name": "爱心巧克力",
                    "description": "增加与伴侣的好感度 +200",
                    "price": 500,
                    "type": "consumable",
                    "effect": {"love": 200},
                    "rarity": "common",
                    "stock": -1,  # -1表示无限库存
                },
                "幸运符": {
                    "id": 2,
                    "name": "幸运符",
                    "description": "提高娶伴侣成功率 +20%（持续3次使用）",
                    "price": 1000,
                    "type": "buff",
                    "effect": {"luck_boost": 20, "luck_streak": 3},
                    "rarity": "rare",
                    "stock": 10,
                },
                "金币袋": {
                    "id": 3,
                    "name": "金币袋",
                    "description": "直接获得1000-3000金币",
                    "price": 800,
                    "type": "consumable",
                    "effect": {"money_min": 1000, "money_max": 3000},
                    "rarity": "common",
                    "stock": -1,
                },
                "冷却重置卡": {
                    "id": 4,
                    "name": "冷却重置卡",
                    "description": "重置所有技能冷却时间",
                    "price": 1500,
                    "type": "consumable",
                    "effect": {"reset_cooldown": True},
                    "rarity": "epic",
                    "stock": 5,
                },
                "保护符": {
                    "id": 5,
                    "name": "保护符",
                    "description": "免疫一次抢伴侣失败的惩罚",
                    "price": 2000,
                    "type": "consumable",
                    "effect": {"protection": True, "imm_num": 1},
                    "rarity": "epic",
                    "stock": 3,
                },
                "双倍经验卡": {
                    "id": 6,
                    "name": "双倍经验卡",
                    "description": "打工收入翻倍（持续5次）",
                    "price": 1200,
                    "type": "buff",
                    "effect": {"work_boost": 2, "dbl_exp_num": 5},
                    "rarity": "rare",
                    "stock": 8,
                },
                "神秘礼盒": {
                    "id": 7,
                    "name": "神秘礼盒",
                    "description": "随机获得一个道具",
                    "price": 2500,
                    "type": "mystery",
                    "effect": {"mystery_box": True},
                    "rarity": "legendary",
                    "stock": 2,
                },
            },
            "daily_items": [
                "爱心巧克力",
                "幸运符",
                "金币袋",
                "双倍经验卡",
            ],  # 每日刷新的商品ID
            "last_refresh": datetime.now(self.CN_TIMEZONE).strftime("%Y-%m-%d"),
        }
        if not self.shop_data_path.exists() or not shop_default_data.get("items"):
            write_json_sync(self.shop_data_path, self.default_shop)
        # 初始化用户背包路径文件
        if not self.backpack_path.exists():
            self.backpack_path.mkdir(parents=True, exist_ok=True)

    async def get_shop_items(self) -> Dict[str, Any]:
        """获取商店物品列表，自动处理每日刷新"""
        shop_data = await read_json(self.shop_data_path)
        today = datetime.now(self.CN_TIMEZONE).strftime("%Y-%m-%d")

        # 检查并执行每日刷新
        if shop_data["last_refresh"] != today:
            # 刷新每日商品
            shop_data = self.default_shop
            await write_json(self.shop_data_path, shop_data)
        return shop_data["items"]

    async def get_item_detail(self, item_name: str) -> Optional[Dict[str, Any]]:
        """获取指定物品的详细信息"""
        items = await self.get_shop_items()
        return items.get(item_name)

    async def get_user_backpack(self, user_id: str) -> Dict[str, int]:
        """获取用户背包物品列表"""
        file_path = self.backpack_path / f"{user_id}.json"
        backpack = await read_json(file_path)
        return backpack or {}

    async def handle_use_command(
        self, event: AiocqhttpMessageEvent, input_str: str
    ) -> Tuple[bool, str]:
        """
        使用背包中的物品
        :param user_id: 用户ID
        :param item_name: 物品名称
        :param quantity: 使用数量（默认1）
        :return: (是否成功, 物品效果或错误消息)
        """
        try:
            user_id = str(event.get_sender_id())
            parts = input_str.strip().split()
            if not parts:
                return (
                    False,
                    "请指定物品名称，使用方法: /使用道具 物品名称\n"
                    "或：/使用道具 物品名称 数量",
                )
            item_name = parts[0]
            try:
                quantity = int(parts[1]) if len(parts) >= 2 else 1
            except ValueError:
                return False, "数量必须为整数，请重新输入"
            if quantity <= 0:
                return False, "使用数量必须为正整数"
            file_path = self.backpack_path / f"{user_id}.json"
            backpack = await self.get_user_backpack(user_id)
            # 物品存在性与数量校验
            if item_name not in backpack:
                return False, "❌ 你没有这个道具"
            if backpack[item_name] < quantity:
                return (
                    False,
                    f"❌ 您所需{item_name}的数量不足\n当前持有数量：{backpack[item_name]}",
                )

            # 获取物品效果
            item = await self.get_item_detail(item_name)
            if not item:
                return False, "❌ 道具信息不存在"

            # 更新背包
            backpack[item_name] -= quantity
            if backpack[item_name] == 0:
                del backpack[item_name]
            await write_json(file_path, backpack)

            # 执行道具效果
            result = await self.execute_item_effect(item, user_id, backpack, quantity)
            if not result["success"]:
                return False, f"❌ {result['message']}"
            return True, result["message"]
        except Exception as e:
            logger.error(f"使用物品失败: {str(e)}")
            return False, "使用物品失败，请稍后再试~"

    async def execute_item_effect(
        self, item, user_id, backpack, quantity
    ) -> Dict[str, Any]:
        """执行道具效果，返回执行结果"""
        try:
            target_user_data_path = self.user_data_path / f"{user_id}.json"
            user_data = await read_json(target_user_data_path)
            if "other" not in user_data:
                user_data["other"] = {}
            if item["type"] == "consumable":
                # 好感度道具
                if "love" in item["effect"]:
                    if user_data["home"].get("love", 0) == 0:
                        return {
                            "success": False,
                            "message": "你还没有伴侣，无法使用此道具",
                        }
                    user_data["home"]["love"] = (
                        user_data["home"]["love"] + item["effect"]["love"] * quantity
                    )
                    await write_json(target_user_data_path, user_data)

                    # # 更新任务进度
                    # quest_system = TaskSystem()
                    # await quest_system.update_quest_progress(
                    #     user_id, group_id, "max_love", user_data["home"]["love"]
                    # )
                    return {
                        "success": True,
                        "message": f"💕 好感度增加 {item['effect']['love'] * quantity}，当前好感度: {user_data['home']['love']}",
                    }

                # 金币道具
                elif "money_min" in item["effect"] and "money_max" in item["effect"]:
                    money = 0
                    for _ in range(quantity):
                        money += random.randint(
                            item["effect"]["money_min"], item["effect"]["money_max"]
                        )
                    user_data["home"]["money"] = (
                        user_data["home"].get("money", 0) + money
                    )
                    await write_json(target_user_data_path, user_data)

                    # # 更新任务进度
                    # quest_system = QuestSystem()
                    # await quest_system.update_quest_progress(
                    #     user_id, group_id, "max_money", user_data["home"]["money"]
                    # )
                    return {
                        "success": True,
                        "message": f"💰 获得 {money} 金币，当前余额: {user_data['home']['money']}",
                    }

                # 冷却重置道具
                elif (
                    "reset_cooldown" in item["effect"]
                    and item["effect"]["reset_cooldown"]
                ):
                    if quantity > 1:
                        return {
                            "success": False,
                            "message": "冷却重置卡一次只能使用一张哦~",
                        }
                    return {"success": True, "message": "⏰ 冷却重置道具功能暂未实现"}
                    # keys =
                    # for key in keys:
                    #     await self.context.redis.delete(key)
                    # return {"success": True, "message": "⏰ 所有技能冷却时间已重置！"}

                # 保护符道具
                elif "protection" in item["effect"] and item["effect"]["protection"]:
                    config_data = read_json_sync(self.config_path, "utf-8-sig")
                    protection_duration = config_data.get("protection_duration", 86400)
                    if user_data["other"].get("imm_num", 0) == 0:
                        user_data["other"]["protection"] = user_data["other"].get(
                            "protection", 0
                        ) + int(protection_duration)
                    user_data["other"]["imm_num"] = (
                        user_data["other"].get("imm_num", 0)
                        + item["effect"]["imm_num"] * quantity
                    )
                    await write_json(target_user_data_path, user_data)
                    return {
                        "success": True,
                        "message": f"🛡️ 获得{int(protection_duration / 3600)}小时保护，免疫{user_data['other']['imm_num']}次失败惩罚！",
                    }

            elif item["type"] == "buff":
                # 幸运加成道具
                if item["name"] == "幸运符":
                    if user_data["other"].get("luck_streak", 0) == 0:
                        user_data["other"]["luck_boost"] = user_data["other"].get(
                            "luck_boost", 0
                        ) + int(item["effect"]["luck_boost"])
                    user_data["other"]["luck_streak"] = (
                        user_data["other"].get("luck_streak", 0)
                        + int(item["effect"]["luck_streak"]) * quantity
                    )
                    await write_json(target_user_data_path, user_data)
                    return {
                        "success": True,
                        "message": f"🍀 获得幸运加成 +{item['effect']['luck_boost']}%，持续{item['effect']['luck_streak'] * quantity}次使用",
                    }

                # 打工加成道具
                elif item["effect"]["work_boost"]:
                    if user_data["other"].get("dbl_exp_num", 0) == 0:
                        user_data["other"]["work_boost"] = user_data["other"].get(
                            "work_boost", 0
                        ) + int(item["effect"]["work_boost"])
                    user_data["other"]["dbl_exp_num"] = (
                        user_data["other"].get("dbl_exp_num", 0)
                        + int(item["effect"]["dbl_exp_num"]) * quantity
                    )
                    await write_json(target_user_data_path, user_data)
                    return {
                        "success": True,
                        "message": f"💼 获得打工加成 +{item['effect']['work_boost']}%，持续{item['effect']['dbl_exp_num'] * quantity}次使用",
                    }
            # 神秘礼盒道具
            elif item["type"] == "mystery" and item["effect"]["mystery_box"]:
                shop_data = await read_json(self.shop_data_path)
                current_item_name = str(item["name"])
                # 构建名称到详情的映射（排除当前物品），用于快速查询
                name_to_detail = {
                    name: detail
                    for name, detail in shop_data["items"].items()
                    if name != current_item_name
                }
                # 可用物品名称列表（即映射的键）
                available_names = list(name_to_detail.keys())
                # 随机选择指定数量的物品名称
                selected_names = random.choices(available_names, k=quantity)
                # 统计每个物品的选中次数
                item_count = Counter(selected_names)
                message_parts = []
                for target_name, count in item_count.items():
                    detail = name_to_detail[target_name]
                    rarity_emoji = TextFormatter.get_rarity_emoji(detail["rarity"])
                    backpack[target_name] = backpack.get(target_name, 0) + count
                    # 收集消息片段
                    message_parts.append(f"{rarity_emoji} {target_name} x {count}")
                message = "\n".join(message_parts)
                await write_json(self.backpack_path / f"{user_id}.json", backpack)
                return {
                    "success": True,
                    "message": f"🎁 神秘礼盒开启！获得: \n{message}",
                }
            return {"success": False, "message": "道具效果未定义"}

        except Exception as e:
            logger.error(f"执行道具效果失败：{str(e)}")
            return {"success": False, "message": "道具效果执行失败"}

    async def handle_buy_command(
        self, event: AiocqhttpMessageEvent, input_str: str
    ) -> Tuple[bool, str]:
        """
        处理购买命令解析
        :param user_id: 用户ID
        :param input_str: 命令参数（物品名称 [数量]）
        :return: (是否成功, 结果消息)
        """
        try:
            user_id = str(event.get_sender_id())
            parts = input_str.strip().split()
            if not parts:
                return (
                    False,
                    "请指定物品名称，使用方法: /购买道具 物品名称\n"
                    "或：/购买道具 物品名称 数量",
                )
            item_name = parts[0]
            quantity = int(parts[1]) if len(parts) >= 2 else 1
            if quantity <= 0:
                return False, "购买数量必须为正整数"
            # 导入用户系统获取金钱
            from .user import User

            user_system = User()
            home_data = await user_system.get_home_data(user_id)
            user_money = home_data.get("money", 0)

            return await self.buy_item(user_id, item_name, user_money, quantity)
        except ValueError:
            return False, "数量必须是数字"
        except Exception as e:
            return False, f"购买失败: {str(e)}"

    async def buy_item(
        self, user_id: str, item_name: str, user_money: int, quantity: int = 1
    ) -> Tuple[bool, str]:
        """
        购买物品（支持批量购买）
        :param user_id: 用户ID
        :param item_name: 物品名称
        :param user_money: 用户当前金币数
        :param quantity: 购买数量（默认1）
        :return: (是否成功, 结果消息)
        """
        # 加载数据
        shop_data = await read_json(self.shop_data_path)
        items = shop_data["items"]
        file_path = self.backpack_path / f"{user_id}.json"
        backpack = await self.get_user_backpack(user_id)

        # 基础校验
        if item_name not in items:
            return False, "物品不存在"
        if quantity <= 0:
            return False, "购买数量必须为正整数"

        target_item = items[item_name]
        total_price = target_item["price"] * quantity

        # 库存与金钱校验
        if target_item["stock"] != -1 and target_item["stock"] < quantity:
            return False, f"物品库存不足，当前库存: {target_item['stock']}"
        if user_money < total_price:
            return (
                False,
                f"购买{target_item['name']} x {quantity}所需的金币不足\n"
                f"需要{total_price}金币，您当前拥有{user_money}金币",
            )

        # 更新库存
        if target_item["stock"] != -1:
            target_item["stock"] -= quantity
            await write_json(self.shop_data_path, shop_data)

        # 更新背包
        if item_name not in backpack:
            backpack[item_name] = 0
        backpack[item_name] += quantity
        await write_json(file_path, backpack)

        return (
            True,
            f"成功购买{target_item['name']} x {quantity}\n花费{total_price}金币",
        )

    async def handle_gift_command(
        self, event: AiocqhttpMessageEvent, input_str: str
    ) -> Tuple[bool, str]:
        """
        赠送物品给其他用户
        :param from_user_id: 赠送者ID
        :param to_user_id: 接收者ID
        :param item_name: 物品名称
        :param amount: 赠送数量（默认1）
        :return: (是否成功, 结果消息)
        """
        from_user_id = None
        to_user_id = None
        amount = 1
        parts = input_str.strip().split()
        if len(parts) <= 1:
            return (
                False,
                "请指定物品名称和接收者，使用方法:\n"
                " /赠送道具 物品名称 @用户/qq号\n"
                "或：/赠送道具 物品名称 @用户/qq号 数量",
            )
        item_name = parts[0]
        to_user_ids = get_at_ids(event)
        if isinstance(to_user_ids, list) and to_user_ids:
            to_user_id = to_user_ids[0]
        try:
            if to_user_id:
                if len(parts) >= 3:
                    amount = int(parts[2])
            else:
                if len(parts) >= 3 and parts[1].isdigit():
                    to_user_id = parts[1]
                    amount = int(parts[2])
                else:
                    to_user_id = parts[1]
        except ValueError:
            return False, "赠送数量必须为整数"
        if amount <= 0:
            return False, "赠送数量必须为正整数"
        if not to_user_id:
            return (
                False,
                "请指定接收者，使用@用户或直接输入QQ号\n"
                "使用方法: /赠送道具 物品名称 @用户/qq号\n"
                "或：/赠送道具 物品名称 @用户/qq号 数量",
            )
        from_user_id = str(event.get_sender_id())
        if from_user_id == to_user_id:
            return False, "不能赠送物品给自己"
        from_file_path = self.backpack_path / f"{from_user_id}.json"
        to_file_path = self.backpack_path / f"{to_user_id}.json"
        from_backpack = await self.get_user_backpack(from_user_id)
        to_backpack = await self.get_user_backpack(to_user_id)

        # 校验赠送者物品
        if item_name not in from_backpack or from_backpack[item_name] < amount:
            return False, "物品不存在或数量不足"

        # 执行赠送逻辑,减少赠送者物品
        from_backpack[item_name] -= amount
        if from_backpack[item_name] == 0:
            del from_backpack[item_name]
        # 增加接收者物品
        to_backpack[item_name] = to_backpack.get(item_name, 0) + amount

        await write_json(from_file_path, from_backpack)
        await write_json(to_file_path, to_backpack)
        return True, f"成功给用户{to_user_id}：\n赠送{item_name} x {amount}"

    async def format_shop_items(self) -> str:
        """格式化商店物品列表为展示文本"""
        try:
            items = await self.get_shop_items()
            if not items:
                return "商店暂无商品"
            message = "📦 虚空商城\n"
            for item_name, item in items.items():
                stock = "无限" if item["stock"] == -1 else item["stock"]
                message += f"[{item['id']}] {item_name}：{item['price']}金币\n"
                message += f"描述: {item['description']}\n(库存: {stock})\n"
            return message
        except Exception as e:
            logger.error(f"格式化商店物品失败: {str(e)}")
            return "获取商店物品失败，请稍后再试~"

    async def format_backpack(self, event: AiocqhttpMessageEvent) -> str:
        """格式化用户背包为展示文本"""
        try:
            user_backpack = await self.get_user_backpack(event.get_sender_id())
            if not user_backpack:
                return "你的背包是空的，快去商城购买道具吧！"

            message = "🎒 我的背包 🎒\n━━━━━━━━━━━━━\n"
            for item_name, count in user_backpack.items():
                target_item = await self.get_item_detail(item_name)
                if target_item:
                    rarity_emoji = TextFormatter.get_rarity_emoji(target_item["rarity"])
                    message += f"{rarity_emoji} [{target_item['name']}] x {count}\n"
                    message += f"📝 {target_item['description']}\n"
                    message += "━━━━━━━━━━━━━\n"
            message += "💡 使用 “#使用道具 物品名称” 来使用道具\n"
            message += "💡 使用 “#赠送道具 物品名称 @用户/qq号” 来赠送道具"
            return message
        except Exception as e:
            logger.error(f"格式化背包失败: {str(e)}")
            return "查看背包失败，请稍后再试~"

    async def refresh_shop_manually(self) -> str:
        """管理员手动刷新商店"""
        try:
            shop_data = self.default_shop
            await write_json(self.shop_data_path, shop_data)
            return "🔄 商城已手动刷新！"
        except Exception as e:
            logger.error(f"手动刷新商店失败: {str(e)}")
            return "手动刷新商店失败，请稍后再试~"

    async def handle_item_detail_command(self, input_str: str) -> str:
        """查看物品详情"""
        try:
            parts = input_str.strip().split()
            if not parts:
                return "请指定物品名称，使用方法: /道具详情 物品名称"
            item_name = parts[0]
            item = await self.get_item_detail(item_name)
            if not item:
                return "❌ 道具不存在，请检查道具名称"
            # 构建道具详情
            rarity_map = {
                "common": "普通",
                "rare": "稀有",
                "epic": "史诗",
                "legendary": "传说",
            }
            rarity_emoji = TextFormatter.get_rarity_emoji(item["rarity"])
            rarity_name = rarity_map.get(item["rarity"].lower(), "未知")
            stock_text = "无限" if item["stock"] == -1 else str(item["stock"])
            detail_msg = [
                f"{rarity_emoji} {item['name']}",
                "━━━━━━━━━━━━━",
                f"🏷️ 稀有度: {rarity_name}",
                f"💰 价格: {item['price']}金币",
                f"📦 库存: {stock_text}",
                f"📝 描述: {item['description']}",
                "━━━━━━━━━━━━━",
            ]
            message = "\n".join(detail_msg)
            return message
        except ValueError:
            return "❌ 指令格式错误，请使用 /道具详情 物品名称"
        except Exception as e:
            logger.error(f"查看物品详情失败: {str(e)}")
            return "查看物品详情失败，请稍后再试~"
