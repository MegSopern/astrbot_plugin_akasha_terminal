import json
import random
import re
import time
from pathlib import Path
from typing import Any, Dict

import aiohttp
import astrbot.api.message_components as Comp
from aiocqhttp import CQHttp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from ..core.user import User

# 导入工具函数
from ..utils.utils import read_json, write_json  # noqa: F401


class Task:
    def __init__(self):
        """初始化任务系统，加载任务配置"""
        # 任务配置的文件路径
        self.task_file_path = Path(__file__).parent.parent / "data" / "task.json"
        self.task_data: Dict[str, Dict[str, Any]] = {}
        self.user_system = User()  # 关联用户系统
        read_json(self.task_file_path)

    async def _load_task_data(self) -> None:
        """加载任务配置数据,从JSON文件读取任务定义并初始化"""
        try:
            self.task_data = await read_json(self.task_file_path)
            logger.info(f"成功加载 {len(self.task_data)} 个任务配置")
        except Exception as e:
            logger.error(f"加载任务配置失败: {str(e)}")
            self.task_data = {}

    async def get_random_daily_task(self) -> Dict[str, Any] | None:
        """
        随机获取一个日常任务
        :return: 任务字典或None（无任务时）
        """
        if not self.task_data:
            await self._load_task_data()  # 尝试重新加载
        # 从self.task_data字典的所有值中，筛选出id以"daily_"开头的任务，组成一个新的列表
        daily_tasks = [
            t for t in self.task_data.values() if t["id"].startswith("daily_")
        ]

        # 如果daily_tasks列表不为空，随机选择一个任务返回
        return random.choice(daily_tasks) if daily_tasks else None

    async def get_task_by_id(self, task_id: str) -> Dict[str, Any] | None:
        """
        通过任务ID获取任务详情\n
        :param task_id: 任务ID（如"daily_work"）
        :return: 任务字典或None
        """
        return next(
            (task for task in self.task_data.values() if task.get("id") == task_id),
            None,
        )

    async def check_task_completion(self, user_id: str, action: str) -> Dict[str, Any]:
        """
        检查任务完成情况并返回详细消息\n
        :param user_id: 用户ID
        :param action: 用户执行的动作（如"打工"、"购买"等）
        :return: 包含完成状态的字典
        """
        result = {
            "completed": False,
            "task_id": None,
            "message": "",
            "progress_msg": "",
        }

        # 获取用户当前任务数据
        quest_data = await self.user_system.get_quest_data(user_id)
        current_tasks = quest_data.get("daily", {})

        # 检查每个任务的完成情况
        for task_key, progress in current_tasks.items():
            task = await self.get_task_by_id(task_key)
            if not task:
                continue

            # 判断动作是否与任务相关
            if self._is_relevant_action(task, action):
                # 更新任务进度
                progress["current"] += 1
                quest_data["daily"][task_key] = progress
                await self.user_system.update_quest_data(user_id, quest_data)

                # 构建进度消息
                progress_msg = f"【{task['name']}】进度更新：{progress['current']}/{progress['target']}"
                result["progress_msg"] = progress_msg

                if progress["current"] >= progress["target"]:
                    result["completed"] = True
                    result["task_id"] = task_key
                    result["message"] = f"恭喜完成任务【{task['name']}】！"
                    break
        return result

    async def grant_reward(self, user_id: str, task_id: str) -> tuple[bool, str]:
        """
        为用户发放任务奖励并返回结果消息\n
        :param user_id: 用户ID\t
        :param task_id: 任务ID\n
        :return: 发放是否成功及返回奖励消息
        """
        task = await self.get_task_by_id(task_id)
        if not task or "reward" not in task:
            error_msg = f"任务 {task_id} 奖励配置不存在"
            logger.error(error_msg)
            return False, error_msg

        try:
            # 获取用户数据
            home_data = await self.user_system.get_home_data(user_id)
            quest_data = await self.user_system.get_quest_data(user_id)

            # 记录原始数据用于计算奖励差值
            old_money = home_data.get("money", 0)
            old_love = home_data.get("love", 0)
            old_points = quest_data.get("quest_points", 0)

            # 处理奖励逻辑及构建奖励消息
            reward_msg = "任务奖励：\n"
            if "money" in task["reward"]:
                home_data["money"] = old_money + int(task["reward"]["money"])
                reward_msg += f"  金币 +{task['reward']['money']}\n"

            if "love" in task["reward"]:
                home_data["love"] = old_love + int(task["reward"]["love"])
                reward_msg += f"  好感度 +{task['reward']['love']}\n"

            if "quest_points" in task["reward"]:
                quest_data["quest_points"] = old_points + int(
                    task["reward"]["quest_points"]
                )
                reward_msg += f"  任务点数 +{task['reward']['quest_points']}\n"

            if "items" in task["reward"]:
                for item_id, count in task["reward"]["items"].items():
                    reward_msg += f"  物品 {item_id} ×{count}\n"

            # 保存更新后的数据
            await self.user_system.update_home_data(user_id, home_data)
            await self.user_system.update_quest_data(user_id, quest_data)

            success_msg = f"用户 {user_id} 成功领取任务 {task_id} 奖励"
            logger.info(success_msg)
            return True, reward_msg.strip()
        except Exception as e:
            error_msg = f"发放任务奖励失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def assign_daily_task(self, user_id: str) -> Dict[str, Any] | None:
        """
        为用户分配日常任务\n
        :param user_id: 用户ID
        :return: 分配的任务或None
        """
        task = await self.get_random_daily_task()
        if not task:
            return None

        # 提取任务目标数量
        target = self._extract_target_count(task["description"])

        # 更新用户任务数据
        quest_data = await self.user_system.get_quest_data(user_id)
        quest_data["daily"][task["id"]] = {"current": 0, "target": target}
        await self.user_system.update_quest_data(user_id, quest_data)

        return task

    def _extract_target_count(self, description: str) -> int:
        """
        从任务描述中提取目标数量\n
        :param description: 任务描述文本
        :return: 目标数量（默认1）
        """
        # 使用正则表达式从任务描述文本中提取第一个数字，如果找到则返回该数字，否则返回默认值1
        match = re.search(r"\d+", description)
        return int(match.group()) if match else 1

    def _is_relevant_action(self, task: Dict[str, Any], action: str) -> bool:
        """
        判断用户动作是否与任务相关\n
        :param task: 任务字典
        :param action: 用户动作
        :return: 是否相关
        """
        action_mapping = {
            "daily_work": ["打工", "工作"],
            "daily_shop": ["购买", "购物"],
            "daily_synthesis": ["合成"],
            "weekly_relationship": ["互动", "聊天"],
            "daily_gift": ["赠送", "送礼"],
            "daily_date": ["约会"],
        }
        return action in action_mapping.get(task["id"], [])
