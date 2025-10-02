import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

from astrbot.api import logger

from ..utils.utils import read_json, read_json_sync, write_json, write_json_sync


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
        self.data_dir.mkdir(parents=True, exist_ok=True)  # 确保数据目录存在
        self._init_default_data()

    def _init_default_data(self) -> None:
        """初始化默认商店数据和用户背包（仅当文件不存在时）"""
        # 设置「中国标准时间」
        CN_TIMEZONE = ZoneInfo("Asia/Shanghai")
        # 初始化商店数据
        if not self.shop_data_path.exists():
            default_shop = {
                "items": {
                    "爱心巧克力": {
                        "id": 1,
                        "name": "爱心巧克力",
                        "description": "增加与老婆的好感度 +200",
                        "price": 500,
                        "type": "consumable",
                        "effect": {"love": 200},
                        "rarity": "common",
                        "stock": -1,  # -1表示无限库存
                    },
                    "幸运符": {
                        "id": 2,
                        "name": "幸运符",
                        "description": "提高娶老婆成功率 +20%（持续3次使用）",
                        "price": 1000,
                        "type": "buff",
                        "effect": {"luck_boost": 20, "duration": 3},
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
                        "description": "免疫一次抢老婆失败的惩罚",
                        "price": 2000,
                        "type": "consumable",
                        "effect": {"protection": True},
                        "rarity": "epic",
                        "stock": 3,
                    },
                    "双倍经验卡": {
                        "id": 6,
                        "name": "双倍经验卡",
                        "description": "打工收入翻倍（持续5次）",
                        "price": 1200,
                        "type": "buff",
                        "effect": {"work_boost": 2, "duration": 5},
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
                "last_refresh": datetime.now(CN_TIMEZONE).strftime("%Y-%m-%d"),
            }
            write_json_sync(self.shop_data_path, default_shop)
        # 初始化用户背包路径文件
        if not self.backpack_path.exists():
            self.backpack_path.mkdir(parents=True, exist_ok=True)

    async def _load_data(self, file_path: Path) -> Dict[str, Any]:
        """通用数据加载方法"""
        return await read_json(file_path)

    async def _save_data(self, file_path: Path, data: Dict[str, Any]) -> None:
        """通用数据保存方法"""
        await write_json(file_path, data)

    async def get_shop_items(self) -> Dict[str, Any]:
        """获取商店物品列表，自动处理每日刷新"""
        shop_data = await self._load_data(self.shop_data_path)
        today = datetime.now().strftime("%Y-%m-%d")

        # 检查并执行每日刷新
        if shop_data["last_refresh"] != today:
            shop_data["last_refresh"] = today
            await self._save_data(self.shop_data_path, shop_data)
        return shop_data["items"]

    async def get_item_detail(self, item_name: str) -> Optional[Dict[str, Any]]:
        """获取指定物品的详细信息"""
        items = await self.get_shop_items()
        return items.get(item_name)

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
        shop_data = await self._load_data(self.shop_data_path)
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
            await self._save_data(self.shop_data_path, shop_data)

        # 更新背包
        if item_name not in backpack:
            backpack[item_name] = 0
        backpack[item_name] += quantity
        await self._save_data(file_path, backpack)

        return (
            True,
            f"成功购买{target_item['name']} x {quantity}\n花费{total_price}金币",
        )

    async def get_user_backpack(self, user_id: str) -> Dict[str, int]:
        """获取用户背包物品列表"""
        file_path = self.backpack_path / f"{user_id}.json"
        backpack = await self._load_data(file_path)
        return backpack or {}

    async def handle_use_command(
        self, user_id: str, input_str: str
    ) -> Tuple[bool, str]:
        """
        使用背包中的物品
        :param user_id: 用户ID
        :param item_name: 物品名称
        :param quantity: 使用数量（默认1）
        :return: (是否成功, 物品效果或错误消息)
        """
        parts = input_str.strip().split()
        if len(parts) < 1:
            return (
                False,
                "请指定物品名称，使用方法: /使用道具 物品名称\n"
                "或：/使用道具 物品名称 数量",
            )
        item_name = parts[0]
        quantity = int(parts[1]) if len(parts) > 1 else 1
        if quantity <= 0:
            return False, "使用数量必须为正整数"
        file_path = self.backpack_path / f"{user_id}.json"
        backpack = await self.get_user_backpack(user_id)
        # 物品存在性与数量校验
        if item_name not in backpack:
            return False, "物品不存在"
        if backpack[item_name] < quantity:
            return (
                False,
                f"您所需{item_name}的数量不足\n当前持有数量：{backpack[item_name]}",
            )

        # 获取物品效果
        item = await self.get_item_detail(item_name)
        if not item:
            return False, "物品信息不存在"

        # 更新背包
        backpack[item_name] -= quantity
        if backpack[item_name] == 0:
            del backpack[item_name]
        await self._save_data(file_path, backpack)

        return True, item["effect"]

    async def handle_gift_command(
        self, from_user_id: str, input_str: str
    ) -> Tuple[bool, str]:
        """
        赠送物品给其他用户
        :param from_user_id: 赠送者ID
        :param to_user_id: 接收者ID
        :param item_name: 物品名称
        :param amount: 赠送数量（默认1）
        :return: (是否成功, 结果消息)
        """
        parts = input_str.strip().split()
        if len(parts) < 2:
            return (
                False,
                "请指定物品名称和接收者，使用方法: /赠送道具 物品名称 @用户\n"
                "或：/赠送道具 物品名称 @用户 数量",
            )
        item_name = parts[0]
        to_user_id = parts[1]
        amount = int(parts[2]) if len(parts) > 2 else 1
        if amount <= 0:
            return False, "赠送数量必须为正整数"
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

        await self._save_data(from_file_path, from_backpack)
        await self._save_data(to_file_path, to_backpack)
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
            return str(e)

    async def handle_buy_command(
        self, user_id: str, input_str: str
    ) -> Tuple[bool, str]:
        """
        处理购买命令解析
        :param user_id: 用户ID
        :param input_str: 命令参数（物品名称 [数量]）
        :return: (是否成功, 结果消息)
        """
        try:
            parts = input_str.strip().split()
            if not parts:
                return (
                    False,
                    "请指定物品名称，使用方法: /购买道具 物品名称\n"
                    "或：/购买道具 物品名称 数量",
                )

            item_name = parts[0]
            quantity = int(parts[1]) if len(parts) > 1 else 1

            # 导入用户系统获取金钱（避免循环导入）
            from .user import User

            user_system = User()
            home_data = await user_system.get_home_data(user_id)
            user_money = home_data.get("money", 0)

            return await self.buy_item(user_id, item_name, user_money, quantity)
        except ValueError:
            return False, "数量必须是数字"
        except Exception as e:
            return False, f"购买失败: {str(e)}"

    async def format_backpack(self, user_id: str) -> str:
        """格式化用户背包为展示文本"""
        try:
            user_backpack = await self.get_user_backpack(user_id)
            if not user_backpack:
                return "你的背包是空的，快去商店买点东西吧~"

            message = "🎒 你的背包\n"
            for item_name, count in user_backpack.items():
                target_item = await self.get_item_detail(item_name)
                if target_item:
                    message += (
                        f"- {item_name} x {count}\n  {target_item['description']}\n"
                    )
            return message
        except Exception as e:
            logger.error(f"格式化背包失败: {str(e)}")
            return "查看背包失败，请稍后再试~"
