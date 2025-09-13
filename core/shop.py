import json
from datetime import datetime
from pathlib import Path

from ..utils.utils import read_json, write_json


class Shop:
    def __init__(self):
        # 初始化数据目录和文件
        self.data_dir = Path(__file__).resolve().parent.parent / "data"
        self.shop_data_path = self.data_dir / "shop_data.json"
        self.backpack_path = self.data_dir / "user_backpack.json"
        # 3. 确保目录存在（parents=True 一次性建好，exist_ok=True 已存在不报错）
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化默认数据
        self._init_default_data()

    def _init_default_data(self):
        """初始化默认商店数据和用户背包"""
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
                },
                "daily_items": ["爱心巧克力", "幸运符", "金币袋"],
                "last_refresh": datetime.now().strftime("%Y-%m-%d"),
            }
            with open(self.shop_data_path, "w", encoding="utf-8") as f:
                json.dump(default_shop, f, ensure_ascii=False, indent=2)

        # 初始化用户背包
        if not self.backpack_path.exists():
            self._save_backpack_data({})

    async def _load_shop_data(self):
        """加载商店数据"""
        return await read_json(self.shop_data_path)

    async def _save_shop_data(self, data):
        """保存商店数据"""
        return await write_json(self.shop_data_path, data)

    async def _load_backpack_data(self):
        """加载用户背包数据"""
        return await read_json(self.backpack_path)

    async def _save_backpack_data(self, data):
        """保存用户背包数据"""
        return await write_json(self.backpack_path, data)

    async def get_shop_items(self):
        """获取商店物品列表"""
        shop_data = await self._load_shop_data()

        # 检查是否需要每日刷新
        today = datetime.now().strftime("%Y-%m-%d")
        if shop_data["last_refresh"] != today:
            shop_data["last_refresh"] = today
            await self._save_shop_data(shop_data)

        return shop_data["items"]

    async def get_item_detail(self, item_name: str):
        """获取物品详情"""
        items = await self.get_shop_items()
        return items.get(str(item_name))

    async def buy_item(
        self, user_id: str, item_name: str, user_money, quantity: int = 1
    ):
        """购买物品，支持指定数量"""
        shop_data = await self._load_shop_data()
        items = shop_data["items"]

        # 检查物品是否存在
        if item_name not in items:
            return False, "物品不存在"

        # 检查购买数量有效性
        if quantity <= 0:
            return False, "购买数量必须为正整数"

        target_item = items.get(item_name)

        # 检查库存
        if target_item["stock"] != -1:  # 有限库存
            if target_item["stock"] < quantity:
                return False, f"物品库存不足，当前库存: {target_item['stock']}"

        # 计算总价
        total_price = target_item["price"] * quantity

        # 检查金钱是否足够
        if user_money < total_price:
            return (
                False,
                f"购买{target_item['name']} x {quantity}所需的金币不足\n"
                f"需要{total_price}金币，您当前拥有{user_money}金币",
            )

        # 减少库存
        if target_item["stock"] > 0:
            target_item["stock"] -= quantity
            await self._save_shop_data(shop_data)

        # 添加到背包
        backpack = await self._load_backpack_data()

        if user_id not in backpack:
            backpack[user_id] = {}

        if item_name not in backpack[user_id]:
            backpack[user_id][item_name] = 0

        backpack[user_id][item_name] += quantity
        await self._save_backpack_data(backpack)

        return (
            True,
            f"成功购买{target_item['name']} x {quantity}\n花费{total_price}金币",
        )

    async def get_user_backpack(self, user_id: str):
        """获取用户背包"""
        backpack = await self._load_backpack_data()
        return backpack.get(user_id, {})

    async def use_item(self, user_id, item_name: str, quantity: int = 1):
        """使用物品"""
        backpack = await self._load_backpack_data()

        # 检查背包是否有该物品
        if user_id not in backpack or item_name not in backpack[user_id]:
            return False, "物品不存在"
        elif backpack[user_id][item_name] < quantity:
            return False, f"您所需{item_name}的数量不足\n当前持有数量：{quantity}"

        # 获取物品信息
        item = await self.get_item_detail(item_name)
        if not item:
            return False, "物品信息不存在"

        # 减少物品数量
        backpack[user_id][item_name] -= quantity
        if backpack[user_id][item_name] == 0:
            del backpack[user_id][item_name]
        await self._save_backpack_data(backpack)
        return True, item["effect"]

    async def gift_item(
        self, from_user_id: str, to_user_id: str, item_name: str, amount: int = 1
    ):
        """赠送物品"""
        backpack = await self._load_backpack_data()

        # 检查赠送者是否有该物品
        if (
            from_user_id not in backpack
            or item_name not in backpack[from_user_id]
            or backpack[from_user_id][item_name] < amount
        ):
            return False, "物品不存在或数量不足"

        # 减少赠送者物品
        backpack[from_user_id][item_name] -= amount
        if backpack[from_user_id][item_name] == 0:
            del backpack[from_user_id][item_name]

        # 增加接收者物品
        if to_user_id not in backpack:
            backpack[to_user_id] = {}

        if item_name not in backpack[to_user_id]:
            backpack[to_user_id][item_name] = 0

        backpack[to_user_id][item_name] += amount
        await self._save_backpack_data(backpack)

        return True, f"成功给用户{to_user_id}：\n赠送{item_name} x {amount}"

    async def format_shop_items(self) -> str:
        """格式化商店物品列表为显示文本"""
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
    ) -> tuple[bool, str]:
        """处理购买命令解析和执行"""
        try:
            # 解析输入格式：物品名称 数量
            parts = input_str.strip().split()
            if len(parts) < 1:
                return (
                    False,
                    "请指定物品名称，使用方法: /购买道具 物品名称\n"
                    "或：/购买道具 物品名称 数量",
                )

            item_name = parts[0]
            quantity = int(parts[1]) if len(parts) > 1 else 1

            # 获取用户金钱
            from .user import User  # 避免循环导入

            user_system = User()
            home_data = await user_system.get_home_data(user_id)
            user_money = home_data.get("money", 0)

            # 执行购买
            return await self.buy_item(user_id, item_name, user_money, quantity)
        except ValueError:
            return False, "数量必须是数字"
        except Exception as e:
            return False, f"购买失败: {str(e)}"

    async def format_backpack(self, user_id: str) -> str:
        """格式化用户背包为显示文本"""
        user_backpack = await self.get_user_backpack(user_id)
        if not user_backpack:
            return "你的背包是空的，快去商店买点东西吧~"

        message = "🎒 你的背包\n"
        for item_name, count in user_backpack.items():
            target_item = await self.get_item_detail(item_name)
            if target_item:
                message += f"{item_name} × {count}\n描述:{target_item['description']}\n"
        return message

    async def handle_gift_command(
        self, from_user_id: str, input_str: str
    ) -> tuple[bool, str]:
        """处理赠送命令解析和执行"""
        try:
            # 解析输入格式：@用户 物品名称 数量
            parts = input_str.strip().split()
            if len(parts) < 2:
                return (
                    False,
                    "请指定物品名称及赠送对象，使用方法:\n"
                    "/赠送道具 物品名称 用户ID/@用户\n或：/赠送道具 物品名称 用户ID/@用户 数量",
                )

            # 提取目标用户ID
            item_name = parts[0]
            to_user_id = parts[1]
            if to_user_id == from_user_id:
                return (
                    False,
                    "请选择除了自己之外的人进行赠送，使用方法:\n"
                    "/赠送道具 物品名称 用户ID/@用户\n或：/赠送道具 物品名称 用户ID/@用户 数量",
                )
            amount = parts[2] if len(parts) > 2 else 1
            if amount <= 0:
                return (False, "赠送数量必须为正整数")
            return await self.gift_item(from_user_id, to_user_id, item_name, amount)
        except ValueError:
            return False, "数量必须是数字"
        except Exception as e:
            return False, f"赠送失败: {str(e)}"

    async def handle_use_command(
        self, user_id: str, input_str: str
    ) -> tuple[bool, str]:
        """处理使用物品命令解析和执行"""
        try:
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
                return (False, "使用数量必须为正整数")
            success, effect = await self.use_item(user_id, item_name, quantity)
            if success:
                # 格式化效果描述
                effect_desc = []
                for key, value in effect.items():
                    if key == "love":
                        effect_desc.append(f"好感度+{value}")
                    elif key == "luck_boost":
                        effect_desc.append(f"幸运值提升{value}%")
                    elif key == "money_min":
                        effect_desc.append(f"获得金币{value}-{effect.get('money_max')}")
                return (
                    True,
                    f"成功使用{item_name} ×{quantity}，获得效果:\n {', '.join(effect_desc)}",
                )
            else:
                return False, effect
        except ValueError:
            return False, "数量必须是数字"
        except Exception as e:
            return False, f"使用失败: {str(e)}"
