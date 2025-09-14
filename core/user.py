import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

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

        # 数据配置映射：统一管理各类型数据的路径、默认值和特殊处理
        self._data_config = {
            "user": {
                "path": self.user_data_path,
                "default": lambda uid: {
                    "id": uid,
                    "nickname": "",
                    "level": 1,
                    "experience": 0,
                    "created_at": time.time(),
                },
                "is_independent_file": True,
            },
            "battle": {
                "path": self.battle_data_path,
                "default": lambda uid: {
                    "experience": 0,
                    "level": 0,
                    "levelname": "无等级",
                    "privilege": 0,
                },
                "is_independent_file": False,
            },
            "home": {
                "path": self.home_data_path,
                "default": lambda uid: {
                    "spouse": 0,
                    "wait": 0,
                    "money": 100,
                    "love": 0,
                },
                "is_independent_file": False,
            },
            "quest": {
                "path": self.quest_data_path,
                "default": lambda uid: {
                    "daily": {},
                    "weekly": {},
                    "special": {},
                    "quest_points": 0,
                    "last_daily_reset": "",
                    "last_weekly_reset": "",
                },
                "is_independent_file": False,
            },
        }

        # 创建必要目录和初始化文件
        self._init_dirs()
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
        """初始化基础数据文件（非用户独立文件）"""
        for config in self._data_config.values():
            if not config["is_independent_file"]:
                file_path = config["path"]
                if not file_path.exists():
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump({}, f, ensure_ascii=False)
                        logger.info(f"初始化数据文件: {file_path}")
                    except Exception as e:
                        logger.error(f"初始化数据文件失败 {file_path}: {str(e)}")

    async def _get_data(
        self, data_type: str, user_id: str, group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        通用数据获取方法
        :param data_type: 数据类型（user/battle/home/quest）
        :param user_id: 用户ID
        :param group_id: 群组ID（仅quest类型需要）
        :return: 对应类型的用户数据
        """
        config = self._data_config.get(data_type)
        if not config:
            raise ValueError(f"不支持的数据类型: {data_type}")

        if config["is_independent_file"]:
            # 用户独立文件类型（单用户JSON文件）
            file_path = config["path"] / f"{user_id}.json"
            data = await read_json(file_path)
            if not data:
                data = config["default"](user_id)
                await write_json(file_path, data)
            return data
        else:
            # 共享文件类型（多用户JSON文件）
            all_data = await read_json(config["path"])
            if user_id not in all_data:
                all_data[user_id] = config["default"](user_id)
                await write_json(config["path"], all_data)
            return all_data[user_id]

    async def _update_data(
        self,
        data_type: str,
        user_id: str,
        new_data: Dict[str, Any],
        group_id: Optional[str] = None,
    ) -> bool:
        """
        通用数据更新方法\n
        :param data_type: 数据类型（user/battle/home/quest）
        :param user_id: 用户ID
        :param new_data: 新数据字典
        :param group_id: 群组ID
        :return: 是否更新成功
        """
        config = self._data_config.get(data_type)
        if not config:
            raise ValueError(f"不支持的数据类型: {data_type}")

        try:
            if config["is_independent_file"]:
                # 用户独立文件类型
                file_path = config["path"] / f"{user_id}.json"
                current_data = await read_json(file_path) or config["default"](user_id)
                current_data.update(new_data)
                return await write_json(file_path, current_data)
            else:
                # 共享文件类型
                all_data = await read_json(config["path"])
                current_data = all_data.get(user_id, config["default"](user_id))
                current_data.update(new_data)
                all_data[user_id] = current_data
                return await write_json(config["path"], all_data)
        except Exception as e:
            logger.error(f"更新{data_type}数据失败: {str(e)}")
            return False

    # 以下为对外接口方法（保持原有功能和参数不变）
    async def get_user(self, user_id: str, nickname: str = "") -> Dict[str, Any]:
        """获取用户基础信息"""
        data = await self._get_data("user", user_id)
        if nickname and data.get("nickname") != nickname:
            await self.update_user(user_id, {"nickname": nickname})
            data["nickname"] = nickname
        return data

    async def update_user(self, user_id: str, data: Dict[str, Any]) -> bool:
        """更新用户基础信息"""
        return await self._update_data("user", user_id, data)

    async def get_battle_data(self, user_id: str) -> Dict[str, Any]:
        """获取用户战斗数据"""
        return await self._get_data("battle", user_id)

    async def update_battle_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """更新用户战斗数据"""
        return await self._update_data("battle", user_id, data)

    async def get_home_data(self, user_id: str) -> Dict[str, Any]:
        """获取用户家园数据"""
        return await self._get_data("home", user_id)

    async def update_home_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """更新用户家园数据"""
        return await self._update_data("home", user_id, data)

    async def get_quest_data(
        self, user_id: str, group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取用户任务数据"""
        return await self._get_data("quest", user_id)

    async def update_quest_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """更新用户任务数据"""
        return await self._update_data("quest", user_id, data)

    async def delete_user(self, user_id: str) -> bool:
        """删除用户所有数据"""
        try:
            # 处理独立文件类型数据
            user_file = self._data_config["user"]["path"] / f"{user_id}.json"
            if user_file.exists():
                user_file.unlink()

            # 处理共享文件类型数据
            for data_type in ["battle", "home"]:
                config = self._data_config[data_type]
                all_data = await read_json(config["path"])
                if user_id in all_data:
                    del all_data[user_id]
                    await write_json(config["path"], all_data)

            # 特殊处理quest数据（可能包含group_id）
            quest_data = await read_json(self.quest_data_path)
            keys_to_delete = [
                k for k in quest_data if k.startswith(f"{user_id}_") or k == user_id
            ]
            for key in keys_to_delete:
                del quest_data[key]
            await write_json(self.quest_data_path, quest_data)

            logger.info(f"用户 {user_id} 数据已删除")
            return True
        except Exception as e:
            logger.error(f"删除用户 {user_id} 数据失败: {str(e)}")
            return False

    async def get_user_list(self) -> list[str]:
        """获取所有用户ID列表"""
        try:
            return [f.stem for f in self.user_data_path.glob("*.json") if f.is_file()]
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return []

    async def format_user_info(
        self, user_id: str, nickname: str, input_str: str
    ) -> str:
        """格式化用户信息为字符串"""
        parts = input_str.strip().split()
        if len(parts) >= 1 and parts[0].isdigit():
            user_id = parts[0]
        user_data = await self.get_user(user_id, nickname)
        battle_data = await self.get_battle_data(user_id)
        home_data = await self.get_home_data(user_id)
        return (
            f"用户信息:\n"
            f"昵称：{user_data.get('nickname')}\n"
            f"ID: {user_id}\n"
            f"等级: {user_data.get('level', 1)}\n"
            f"经验: {battle_data.get('experience', 0)}\n"
            f"金钱: {home_data.get('money', 0)}\n"
            f"好感度: {home_data.get('love', 0)}"
        )

    async def add_money(self, user_id: str, input_str: str) -> tuple[bool, str]:
        """增加用户金钱"""
        try:
            parts = input_str.strip().split()
            if len(parts) < 1:
                return (
                    False,
                    "请指定增加的金额，使用方法:/增加金钱 金额 qq\n或：/增加金钱 金额 @用户",
                )
            amount = int(parts[0])
            to_user_id = parts[1] if len(parts) > 1 else user_id

            if amount <= 0:
                return False, "增加的金额必须为正整数"

            home_data = await self.get_home_data(to_user_id)
            home_data["money"] = home_data.get("money", 0) + amount
            await self.update_home_data(to_user_id, home_data)

            return True, f"成功增加 {amount} 金钱\n当前金钱: {home_data['money']}"
        except ValueError:
            return False, "金额必须是整数"
        except Exception as e:
            logger.error(f"增加用户金钱失败: {str(e)}")
            return False, "操作失败，请稍后再试~"

    async def get_all_users_info(self) -> str:
        """获取所有用户详细信息列表"""
        try:
            user_list = await self.get_user_list()
            if not user_list:
                return "暂无用户数据"

            message = "用户列表:\n"
            for user_id in user_list:
                user_data = await self.get_user(user_id)
                nickname = user_data.get("nickname", "未设置")
                message += f"- {nickname}：ID({user_id})\n"

            return message
        except Exception as e:
            logger.error(f"获取所有用户信息失败: {str(e)}")
            return f"操作失败: {str(e)}"
