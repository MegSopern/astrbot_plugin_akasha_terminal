import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..utils.utils import read_json, write_json


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
            / "user_backpack.json"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)  # 确保数据目录存在
        self._init_default_data()

    def _init_default_data(self) -> None:
        """初始化默认商店数据和用户背包（仅当文件不存在时）"""
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
                "last_refresh": datetime.now().strftime("%Y-%m-%d"),
            }
            self._save_data(self.shop_data_path, default_shop)

        # 初始化用户背包
        if not self.backpack_path.exists():
            self._save_data(self.backpack_path, {})

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
        backpack = await self._load_data(self.backpack_path)

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
        user_backpack = backpack.setdefault(user_id, {})
        user_backpack[item_name] = user_backpack.get(item_name, 0) + quantity
        await self._save_data(self.backpack_path, backpack)

        return (
            True,
            f"成功购买{target_item['name']} x {quantity}\n花费{total_price}金币",
        )

    async def get_user_backpack(self, user_id: str) -> Dict[str, int]:
        """获取用户背包物品列表"""
        backpack = await self._load_data(self.backpack_path)
        return backpack.get(user_id, {})

    async def use_item(
        self, user_id: str, item_name: str, quantity: int = 1
    ) -> Tuple[bool, Any]:
        """
        使用背包中的物品
        :param user_id: 用户ID
        :param item_name: 物品名称
        :param quantity: 使用数量（默认1）
        :return: (是否成功, 物品效果或错误消息)
        """
        backpack = await self._load_data(self.backpack_path)

        # 物品存在性与数量校验
        if user_id not in backpack or item_name not in backpack[user_id]:
            return False, "物品不存在"
        if backpack[user_id][item_name] < quantity:
            return (
                False,
                f"您所需{item_name}的数量不足\n当前持有数量：{backpack[user_id][item_name]}",
            )

        # 获取物品效果
        item = await self.get_item_detail(item_name)
        if not item:
            return False, "物品信息不存在"

        # 更新背包
        backpack[user_id][item_name] -= quantity
        if backpack[user_id][item_name] == 0:
            del backpack[user_id][item_name]
        await self._save_data(self.backpack_path, backpack)

        return True, item["effect"]

    async def gift_item(
        self, from_user_id: str, to_user_id: str, item_name: str, amount: int = 1
    ) -> Tuple[bool, str]:
        """
        赠送物品给其他用户
        :param from_user_id: 赠送者ID
        :param to_user_id: 接收者ID
        :param item_name: 物品名称
        :param amount: 赠送数量（默认1）
        :return: (是否成功, 结果消息)
        """
        backpack = await self._load_data(self.backpack_path)

        # 校验赠送者物品
        if (
            from_user_id not in backpack
            or item_name not in backpack[from_user_id]
            or backpack[from_user_id][item_name] < amount
        ):
            return False, "物品不存在或数量不足"

        # 执行赠送逻辑
        # 减少赠送者物品
        backpack[from_user_id][item_name] -= amount
        if backpack[from_user_id][item_name] == 0:
            del backpack[from_user_id][item_name]

        # 增加接收者物品
        to_backpack = backpack.setdefault(to_user_id, {})
        to_backpack[item_name] = to_backpack.get(item_name, 0) + amount

        await self._save_data(self.backpack_path, backpack)
        return True, f"成功给用户{to_user_id}：\n赠送{item_name} x {amount}"

    async def format_shop_items(self) -> str:
        """格式化商店物品列表为展示文本"""
        items = await self.get_shop_items()
        if not items:
            return "商店暂无商品"

        message = "📦 虚空商城\n"
        for item_name, item in items.items():
            stock = "无限" if item["stock"] == -1 else item["stock"]
            message += f"[{item['id']}] {item_name}：{item['price']}金币\n"
            message += f"描述: {item['description']}\n(库存: {stock})\n"
        return message

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
        user_backpack = await self.get_user_backpack(user_id)
        if not user_backpack:
            return "你的背包是空的，快去商店买点东西吧~"

        message = "🎒 你的背包\n"
        for item_name, count in user_backpack.items():
            target_item = await self.get_item_detail(item_name)
            if target_item:
                message += f"- {item_name} x {count}\n  {target_item['description']}\n"
        return message
