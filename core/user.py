import asyncio
import fcntl
import json
import os  # noqa: F401
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

from astrbot.api import logger

# 数据存储路径：插件目录上一层的plugin_data/astrbot_plugin_akasha_terminal
BASE_DIR = (
    Path(__file__).parent.parent.parent.parent
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

    async def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """异步原子读取JSON文件"""
        # 原子读：加共享锁 -> 读 -> 解锁
        if not file_path.exists():
            return {}

        loop = asyncio.get_running_loop()

        def read_json_atomic() -> Dict[str, Any]:
            fd = os.open(file_path, os.O_RDONLY | os.O_CLOEXEC)
            try:
                # 加共享锁（非阻塞）
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                with os.fdopen(fd, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 读取完成后，释放锁
                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                pass
            return data

        try:
            return await loop.run_in_executor(None, read_json_atomic)
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {str(e)}")
            return {}

    async def _write_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """异步原子写入JSON文件"""
        loop = asyncio.get_running_loop()

        def write_json_atomic() -> None:
            # 生成唯一的临时文件
            with tempfile.NamedTemporaryFile(
                "w", dir=file_path.parent, delete=False, suffix=".json"
            ) as tmp_file:
                json.dump(data, tmp_file, ensure_ascii=False)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                temp_name = tmp_file.name
            # 原子替换
            os.replace(temp_name, file_path)

        try:
            # 使用原子写入方法
            await loop.run_in_executor(None, write_json_atomic)
            return True
        except Exception as e:
            logger.error(f"写入文件 {file_path} 失败: {str(e)}")
            return False

    async def get_user(self, user_id):
        """获取用户基础信息"""
        user_file = self.user_data_path / f"{user_id}.json"
        data = await self._read_json(user_file)

        # 如果用户不存在，初始化默认数据
        if not data:
            data = {
                "id": user_id,
                "nickname": "",
                "level": 1,
                "experience": 0,
                "created_at": time.time(),
            }
            await self._write_json(user_file, data)

        return data

    async def update_user(self, user_id, data):
        """更新用户基础信息"""
        user_file = self.user_data_path / f"{user_id}.json"
        # 先读取现有数据
        existing_data = await self.get_user(user_id)
        # 合并新数据
        existing_data.update(data)
        # 写入文件
        return await self._write_json(user_file, existing_data)

    async def get_battle_data(self, user_id):
        """获取用户战斗数据"""
        battle_data = await self._read_json(self.battle_data_path)

        if user_id not in battle_data:
            battle_data[user_id] = {
                "experience": 0,
                "level": 0,
                "levelname": "无等级",
                "privilege": 0,
            }
            await self._write_json(self.battle_data_path, battle_data)

        return battle_data[user_id]

    async def update_battle_data(self, user_id, data):
        """更新用户战斗数据"""
        battle_data = await self._read_json(self.battle_data_path)
        if user_id not in battle_data:
            current_data = await self.get_battle_data(user_id)
        else:
            current_data = battle_data[user_id]

        current_data.update(data)
        battle_data[user_id] = current_data
        return await self._write_json(self.battle_data_path, battle_data)

    async def get_home_data(self, user_id):
        """获取用户家园数据"""
        home_data = await self._read_json(self.home_data_path)

        if user_id not in home_data:
            home_data[user_id] = {"s": 0, "wait": 0, "money": 100, "love": 0}
            await self._write_json(self.home_data_path, home_data)

        return home_data[user_id]

    async def update_home_data(self, user_id, data):
        """更新用户家园数据"""
        home_data = await self._read_json(self.home_data_path)
        if user_id not in home_data:
            current_data = await self.get_home_data(user_id)
        else:
            current_data = home_data[user_id]

        current_data.update(data)
        home_data[user_id] = current_data
        return await self._write_json(self.home_data_path, home_data)

    async def get_quest_data(self, user_id, group_id=None):
        """获取用户任务数据"""
        quest_key = f"{user_id}_{group_id}" if group_id else user_id
        quest_data = await self._read_json(self.quest_data_path)

        if quest_key not in quest_data:
            quest_data[quest_key] = {
                "daily": {},
                "weekly": {},
                "special": {},
                "quest_points": 0,
                "last_daily_reset": "",
                "last_weekly_reset": "",
            }
            await self._write_json(self.quest_data_path, quest_data)

        return quest_data[quest_key]

    async def delete_user(self, user_id):
        """删除用户所有数据"""
        try:
            # 删除用户基础信息
            user_file = self.user_data_path / f"{user_id}.json"
            if user_file.exists():
                user_file.unlink()

            # 删除战斗数据
            battle_data = await self._read_json(self.battle_data_path)
            if user_id in battle_data:
                del battle_data[user_id]
                await self._write_json(self.battle_data_path, battle_data)

            # 删除家园数据
            home_data = await self._read_json(self.home_data_path)
            if user_id in home_data:
                del home_data[user_id]
                await self._write_json(self.home_data_path, home_data)

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
