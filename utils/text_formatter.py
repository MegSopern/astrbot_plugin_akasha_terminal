class TextFormatter:
    """文本格式化工具类"""

    @staticmethod
    def get_item_icon(item_type: str) -> str:
        """获取道具图标"""
        icon_map = {
            "consumable": "🍭",
            "buff": "✨",
            "mystery": "🎁",
            "material": "🔧",
            "weapon": "⚔️",
            "armor": "🛡️",
            "accessory": "💍",
            "food": "🍎",
            "potion": "🧪",
        }
        return icon_map.get(item_type, "📦")

    @staticmethod
    def get_rarity_emoji(rarity: str) -> str:
        """获取稀有度表情符号"""
        rarity_map = {
            "common": "⚪",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟡",
            "mythic": "🔴",
            "普通": "⚪",
            "稀有": "🔵",
            "史诗": "🟣",
            "传说": "🟡",
            "神话": "🔴",
        }
        return rarity_map.get(rarity, "⚪")
