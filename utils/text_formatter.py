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

    @staticmethod
    def get_relationship_status(love: int) -> str:
        """获取关系状态文本"""
        if love >= 5000:
            return "生死相依"
        if love >= 3000:
            return "海誓山盟"
        if love >= 2000:
            return "情深意重"
        if love >= 1000:
            return "情投意合"
        if love >= 500:
            return "两情相悦"
        if love >= 200:
            return "初见倾心"
        if love >= 100:
            return "好感初生"
        if love >= 50:
            return "略有好感"
        return "初识阶段"
