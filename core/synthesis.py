import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from zoneinfo import ZoneInfo

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.star import StarTools
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
from .task import Task


class Synthesis:
    def __init__(self):
        """初始化合成系统，设置数据目录和文件路径"""
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.data_dir = BASE_DIR / "data"
        self.synthesis_recipes_path = self.data_dir / "synthesis_recipes.json"
        self.user_workshop_path = (
            BASE_DIR.parent.parent
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_workshop"
        )
        self.user_inventory_path = (
            BASE_DIR.parent.parent
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_inventory"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._init_synthesis_data()

        # 导入用户系统获取金钱
        from .user import User

        self.user = User()
        # 导入任务系统更新任务进度
        self.task = Task()

    def _init_synthesis_data(self) -> None:
        """初始化默认合成数据（仅当文件不存在时）"""
        # 设置「中国标准时间」
        self.CN_TIMEZONE = ZoneInfo("Asia/Shanghai")
        # 初始化合成配方数据
        synthesis_default_data = read_json_sync(self.synthesis_recipes_path, {})
        self.default_recipes = {
            "recipes": {
                "超级幸运符": {
                    "id": "super_luck_charm",
                    "materials": {"2": 3, "5": 1},
                    "result_id": "101",
                    "success_rate": 80,
                    "workshop_level": 2,
                    "description": "提供30%成功率加成,持续5次使用",
                    "category": "增益道具",
                },
                "爱情药水": {
                    "id": "love_potion",
                    "materials": {"1": 2, "4": 1},
                    "result_id": "102",
                    "success_rate": 90,
                    "workshop_level": 1,
                    "description": "约会时额外获得50%好感度",
                    "category": "恋爱道具",
                },
                "黄金锤子": {
                    "id": "golden_hammer",
                    "materials": {"3": 5, "5": 2},
                    "result_id": "103",
                    "success_rate": 60,
                    "workshop_level": 3,
                    "description": "打工收入翻倍,持续7天",
                    "category": "经济道具",
                },
                "时间沙漏": {
                    "id": "time_hourglass",
                    "materials": {"2": 2, "4": 3},
                    "result_id": "104",
                    "success_rate": 70,
                    "workshop_level": 2,
                    "description": "重置所有冷却时间",
                    "category": "功能道具",
                },
                "钻石戒指": {
                    "id": "diamond_ring",
                    "materials": {"5": 3, "1": 5},
                    "result_id": "105",
                    "success_rate": 50,
                    "workshop_level": 4,
                    "description": "求婚成功率100%,获得专属称号",
                    "category": "特殊道具",
                },
                "万能钥匙": {
                    "id": "master_key",
                    "materials": {"3": 3, "2": 3},
                    "result_id": "106",
                    "success_rate": 65,
                    "workshop_level": 3,
                    "description": "解锁所有限制,跳过冷却",
                    "category": "功能道具",
                },
                "复活石": {
                    "id": "revival_stone",
                    "materials": {"5": 5, "4": 5},
                    "result_id": "107",
                    "success_rate": 40,
                    "workshop_level": 5,
                    "description": "死亡时自动复活,保留所有财产",
                    "category": "保护道具",
                },
                "财富符咒": {
                    "id": "wealth_talisman",
                    "materials": {"3": 4, "1": 3},
                    "result_id": "108",
                    "success_rate": 75,
                    "workshop_level": 2,
                    "description": "所有金币获得翻倍,持续3天",
                    "category": "经济道具",
                },
                "传送卷轴": {
                    "id": "teleport_scroll",
                    "materials": {"2": 4, "5": 1},
                    "result_id": "109",
                    "success_rate": 85,
                    "workshop_level": 1,
                    "description": "瞬间传送到任意地点",
                    "category": "功能道具",
                },
                "神级合成石": {
                    "id": "divine_synthesis_stone",
                    "materials": {"101": 1, "103": 1, "105": 1},
                    "result_id": "110",
                    "success_rate": 30,
                    "workshop_level": 6,
                    "description": "终极道具,拥有所有效果的组合",
                    "category": "传说道具",
                },
            },
            "items": {
                "101": {"name": "超级幸运符", "rarity": "稀有", "value": 2000},
                "102": {"name": "爱情药水", "rarity": "普通", "value": 800},
                "103": {"name": "黄金锤子", "rarity": "史诗", "value": 5000},
                "104": {"name": "时间沙漏", "rarity": "稀有", "value": 1500},
                "105": {"name": "钻石戒指", "rarity": "传说", "value": 8000},
                "106": {"name": "万能钥匙", "rarity": "史诗", "value": 3000},
                "107": {"name": "复活石", "rarity": "传说", "value": 10000},
                "108": {"name": "财富符咒", "rarity": "稀有", "value": 2500},
                "109": {"name": "传送卷轴", "rarity": "普通", "value": 600},
                "110": {"name": "神级合成石", "rarity": "神话", "value": 50000},
            },
            "decompose": {
                "101": {"materials": {"2": 2, "5": 1}, "success_rate": 60},
                "102": {"materials": {"1": 1, "4": 1}, "success_rate": 80},
                "103": {"materials": {"3": 3, "5": 1}, "success_rate": 40},
                "104": {"materials": {"2": 1, "4": 2}, "success_rate": 70},
                "105": {"materials": {"5": 2, "1": 3}, "success_rate": 30},
            },
        }
