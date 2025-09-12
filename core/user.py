import json
import os  # noqa: F401
import time
from pathlib import Path
from typing import Any, Dict  # noqa: F401

from astrbot.api import logger

# 导入工具函数
from ..utils.utils import read_json, write_json

# 数据存储路径：插件目录上一层的plugin_data/astrbot_plugin_akasha_terminal
BASE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "plugin_data"
    / "astrbot_plugin_akasha_terminal"
)


class User:
    def __init__(self):
        # 初始化数据目录
        self.data_dir = BASE_DIR
        self.user_data_path = self.data_dir / "user_data"
        self.battle_data_path = self.data_dir / "battle_data.json"
        self.home_data_path = self.data_dir / "home_data.json"
        self.quest_data_path = self.data_dir / "quest_data.json"

        # 创建必要目录
        self._init_dirs()

        # 初始化数据文件
        self._init_data_files()

    def _init_dirs(self):
        """初始化数据目录"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.user_data_path.mkdir(parents=True, exist_ok=True)
            logger.info("用户系统数据目录初始化完成")
        except Exception as e:
            logger.error(f"数据目录初始化失败: {str(e)}")

    def _init_data_files(self):
        """初始化基础数据文件"""
        for file_path in [
            self.battle_data_path,
            self.home_data_path,
            self.quest_data_path,
        ]:
            if not file_path.exists():
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump({}, f, ensure_ascii=False)
                    logger.info(f"初始化数据文件: {file_path}")
                except Exception as e:
                    logger.error(f"初始化数据文件失败 {file_path}: {str(e)}")

    async def get_user(self, user_id):
        """获取用户基础信息"""
        user_file = self.user_data_path / f"{user_id}.json"
        data = await read_json(user_file)

        # 如果用户不存在，初始化默认数据
        if not data:
            data = {
                "id": user_id,
                "nickname": "",
                "level": 1,
                "experience": 0,
                "created_at": time.time(),
            }
            await write_json(user_file, data)

        return data

    async def update_user(self, user_id, data):
        """更新用户基础信息"""
        user_file = self.user_data_path / f"{user_id}.json"
        # 先读取现有数据
        existing_data = await self.get_user(user_id)
        # 合并新数据
        existing_data.update(data)
        # 写入文件
        return await write_json(user_file, existing_data)

    async def get_battle_data(self, user_id):
        """获取用户战斗数据"""
        battle_data = await read_json(self.battle_data_path)

        if user_id not in battle_data:
            battle_data[user_id] = {
                "experience": 0,
                "level": 0,
                "levelname": "无等级",
                "privilege": 0,
            }
            await write_json(self.battle_data_path, battle_data)

        return battle_data[user_id]

    async def update_battle_data(self, user_id, data):
        """更新用户战斗数据"""
        battle_data = await read_json(self.battle_data_path)
        if user_id not in battle_data:
            current_data = await self.get_battle_data(user_id)
        else:
            current_data = battle_data[user_id]

        current_data.update(data)
        battle_data[user_id] = current_data
        return await write_json(self.battle_data_path, battle_data)

    async def get_home_data(self, user_id):
        """获取用户家园数据"""
        home_data = await read_json(self.home_data_path)

        if user_id not in home_data:
            home_data[user_id] = {"s": 0, "wait": 0, "money": 100, "love": 0}
            await write_json(self.home_data_path, home_data)

        return home_data[user_id]

    async def update_home_data(self, user_id, data):
        """更新用户家园数据"""
        home_data = await read_json(self.home_data_path)
        if user_id not in home_data:
            current_data = await self.get_home_data(user_id)
        else:
            current_data = home_data[user_id]

        current_data.update(data)
        home_data[user_id] = current_data
        return await write_json(self.home_data_path, home_data)

    async def get_quest_data(self, user_id, group_id=None):
        """获取用户任务数据"""
        quest_key = f"{user_id}_{group_id}" if group_id else user_id
        quest_data = await read_json(self.quest_data_path)

        if quest_key not in quest_data:
            quest_data[quest_key] = {
                "daily": {},
                "weekly": {},
                "special": {},
                "quest_points": 0,
                "last_daily_reset": "",
                "last_weekly_reset": "",
            }
            await write_json(self.quest_data_path, quest_data)

        return quest_data[quest_key]

    async def update_quest_data(self, user_id, data, group_id=None):
        """更新用户任务数据"""
        quest_key = f"{user_id}_{group_id}" if group_id else user_id
        quest_data = await read_json(self.quest_data_path)

        if quest_key not in quest_data:
            current_data = await self.get_quest_data(user_id, group_id)
        else:
            current_data = quest_data[quest_key]

        current_data.update(data)
        quest_data[quest_key] = current_data
        return await write_json(self.quest_data_path, quest_data)

    async def delete_user(self, user_id):
        """删除用户所有数据"""
        try:
            # 删除用户基础信息
            user_file = self.user_data_path / f"{user_id}.json"
            if user_file.exists():
                user_file.unlink()

            # 删除战斗数据
            battle_data = await read_json(self.battle_data_path)
            if user_id in battle_data:
                del battle_data[user_id]
                await write_json(self.battle_data_path, battle_data)

            # 删除家园数据
            home_data = await read_json(self.home_data_path)
            if user_id in home_data:
                del home_data[user_id]
                await write_json(self.home_data_path, home_data)

            logger.info(f"用户 {user_id} 数据已删除")
            return True
        except Exception as e:
            logger.error(f"删除用户 {user_id} 数据失败: {str(e)}")
            return False

    async def get_user_list(self):
        """获取所有用户ID列表"""
        try:
            return [f.stem for f in self.user_data_path.glob("*.json") if f.is_file()]
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return []
