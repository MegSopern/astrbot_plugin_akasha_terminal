import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from astrbot.api import logger
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import At, Plain, Reply
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

# 导入工具函数
from ..utils.utils import get_at_ids, get_nickname, read_json, write_json

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
        self.user_data_path = self.data_dir / "user_data"  # 用户数据统一存储目录

        # 数据配置映射：统一管理各类型数据的默认值
        self._data_config = {
            "user": {
                "default": lambda uid: {
                    "id": uid,
                    "nickname": "",
                    "level": 1,
                    "experience": 0,
                    "created_at": time.time(),
                }
            },
            "battle": {
                "default": lambda uid: {
                    "experience": 0,
                    "level": 0,
                    "levelname": "无等级",
                    "privilege": 0,
                }
            },
            "home": {
                "default": lambda uid: {
                    "spouse_id": "",
                    "spouse_name": "",
                    "love": 0,
                    "wait": 0,
                    "place": "home",
                    "placetime": 0,
                    "money": 100,
                    "house_name": "小破屋",
                    "house_space": 6,
                    "house_price": 500,
                    "house_level": 1,
                }
            },
            "quest": {
                "default": lambda uid: {
                    "daily": {},
                    "weekly": {},
                    "special": {},
                    "quest_points": 0,
                    "last_daily_reset": "",
                    "last_weekly_reset": "",
                }
            },
        }

        # 创建必要目录和初始化文件
        try:
            self.user_data_path.mkdir(parents=True, exist_ok=True)
            logger.info("用户系统数据目录初始化完成")
        except Exception as e:
            logger.error(f"数据目录初始化失败: {str(e)}")

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

        # 所有数据都存储在用户id的独立文件中
        file_path = self.user_data_path / f"{user_id}.json"
        user_data = await read_json(file_path) or {}

        # 初始化该类型数据（如果不存在）
        if data_type not in user_data:
            user_data[data_type] = config["default"](user_id)
            await write_json(file_path, user_data)

        return user_data[data_type]

    async def _update_data(
        self,
        data_type: str,
        user_id: str,
        new_data: Dict[str, Any],
        group_id: Optional[str] = None,
    ) -> bool:
        """
        通用数据更新方法
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
            file_path = self.user_data_path / f"{user_id}.json"
            user_data = await read_json(file_path) or {}

            # 确保基础数据存在
            if data_type not in user_data:
                user_data[data_type] = config["default"](user_id)

            # 更新数据
            user_data[data_type].update(new_data)
            return await write_json(file_path, user_data)
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
            # 删除对应用户id文件
            user_file = self.user_data_path / f"{user_id}.json"
            if user_file.exists():
                user_file.unlink()
                logger.info(f"用户 {user_id} 数据已删除")
                return True
            logger.warning(f"用户 {user_id} 数据文件不存在")
            return False
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
        self, event: AiocqhttpMessageEvent, input_str: str
    ) -> str:
        """格式化用户信息为字符串"""
        try:
            user_id = None
            to_user_ids = get_at_ids(event)
            if isinstance(to_user_ids, list) and to_user_ids:
                user_id = to_user_ids[0]
            else:
                user_id = to_user_ids
            parts = input_str.strip().split()
            if parts and parts[0].isdigit():
                user_id = parts[0]
            if not user_id:
                user_id = str(event.get_sender_id())
            nickname = await get_nickname(event, user_id)
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
        except Exception as e:
            logger.error(f"格式化用户信息失败: {str(e)}")
            return "获取用户信息失败，请稍后再试~"

    async def add_money(
        self, event: AiocqhttpMessageEvent, input_str: str
    ) -> tuple[bool, str]:
        """增加用户金钱"""
        try:
            to_user_id = None
            amount = None
            parts = input_str.strip().split()
            if not parts:
                return (
                    False,
                    "请指定增加的金额，使用方法:/增加金钱 金额 \n或：/增加金钱 @用户/qq号 金额",
                )
            to_user_ids = get_at_ids(event)
            if isinstance(to_user_ids, list) and to_user_ids:
                to_user_id = to_user_ids[0]
            try:
                if to_user_id:
                    if len(parts) >= 2:
                        amount = int(parts[1])
                    else:
                        return (
                            False,
                            "请指定增加的金额，使用方法:\n/增加金钱 @用户/qq号 金额",
                        )
                else:
                    if len(parts) >= 2 and parts[0].isdigit():
                        to_user_id = parts[0]
                        amount = int(parts[1])
                    else:
                        amount = int(parts[0])
            except ValueError:
                return (False, "金额必须是整数，请重新输入")
            if not to_user_id:
                to_user_id = str(event.get_sender_id())
            if amount <= 0:
                return False, "增加的金额必须为正整数"

            home_data = await self.get_home_data(to_user_id)
            home_data["money"] = home_data.get("money", 0) + amount
            await self.update_home_data(to_user_id, home_data)
            return True, f"成功增加 {amount} 金钱\n当前金钱: {home_data['money']}"
        except Exception as e:
            logger.error(f"增加用户金钱失败: {str(e)}")
            return False, "增加用户金钱失败，请稍后再试~"

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
            return "获取用户列表失败，请稍后再试~"
