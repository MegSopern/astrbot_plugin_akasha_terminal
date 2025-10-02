import random
import re
from pathlib import Path
from typing import Any, Dict, Optional

from astrbot.api import logger

from ..core.user import User

# 导入工具函数
from ..utils.utils import read_json, write_json


class Task:
    def __init__(self):
        """初始化任务系统，加载任务配置路径"""
        self.task_file_path = Path(__file__).parent.parent / "data" / "task.json"
        self.task_data: Dict[str, Dict[str, Any]] = {}
        self.user_system = User()  # 关联用户系统

    async def _load_task_data(self) -> None:
        """加载任务配置数据,从JSON文件读取任务定义并初始化"""
        try:
            self.task_data = await read_json(self.task_file_path)
            logger.info(f"成功加载 {len(self.task_data)} 个任务配置")
        except Exception as e:
            logger.error(f"加载任务配置失败: {str(e)}")
            self.task_data = {}

    async def _ensure_task_loaded(self) -> None:
        """确保任务数据已加载，内部调用加载方法"""
        if not self.task_data:
            await self._load_task_data()

    async def get_random_daily_task(self) -> Optional[Dict[str, Any]]:
        """随机获取一个日常任务"""
        await self._ensure_task_loaded()
        # 筛选日常任务并随机返回
        daily_tasks = [
            t for t in self.task_data.values() if t["id"].startswith("daily_")
        ]
        return random.choice(daily_tasks) if daily_tasks else None

    async def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """通过任务ID获取任务详情"""
        await self._ensure_task_loaded()
        return next(
            (task for task in self.task_data.values() if task.get("id") == task_id),
            None,
        )

    async def check_task_completion(self, user_id: str, action: str) -> Dict[str, Any]:
        """检查任务完成情况并返回详细消息"""
        result = {
            "completed": False,
            "task_id": None,
            "message": "",
            "progress_msg": "",
        }

        quest_data = await self.user_system.get_quest_data(user_id)
        current_tasks = quest_data.get("daily", {})

        # 任务类型与动作映射关系
        action_mapping = {
            "daily_work": ["打工", "工作"],
            "daily_shop": ["购买", "购物"],
            "daily_synthesis": ["合成"],
            "weekly_relationship": ["互动", "聊天"],
            "daily_gift": ["赠送", "送礼"],
            "daily_date": ["约会"],
        }

        for task_key, progress in current_tasks.items():
            task = await self.get_task_by_id(task_key)
            if not task:
                continue

            # 检查动作相关性并更新进度
            if action in action_mapping.get(task["id"], []):
                progress["current"] += 1
                quest_data["daily"][task_key] = progress
                await self.user_system.update_quest_data(user_id, quest_data)

                # 构建进度消息
                progress_msg = f"【{task['name']}】进度更新：{progress['current']}/{progress['target']}\n"
                result["progress_msg"] = progress_msg

                if progress["current"] >= progress["target"]:
                    result["completed"] = True
                    result["task_id"] = task_key
                    result["message"] = f"恭喜完成任务【{task['name']}】！\n"
                    break
        return result

    async def grant_reward(self, user_id: str, task_id: str) -> tuple[bool, str]:
        """为用户发放任务奖励并返回结果消息"""
        task = await self.get_task_by_id(task_id)
        if not task or "reward" not in task:
            error_msg = f"任务 {task_id} 奖励配置不存在"
            logger.error(error_msg)
            return False, error_msg

        try:
            # 获取用户数据
            home_data = await self.user_system.get_home_data(user_id)
            quest_data = await self.user_system.get_quest_data(user_id)

            # 奖励处理映射
            reward_handlers = {
                "money": (
                    "home_data",
                    "金币",
                    lambda d, v: d.update({"money": d.get("money", 0) + int(v)}),
                ),
                "love": (
                    "home_data",
                    "好感度",
                    lambda d, v: d.update({"love": d.get("love", 0) + int(v)}),
                ),
                "quest_points": (
                    "quest_data",
                    "任务点数",
                    lambda d, v: d.update(
                        {"quest_points": d.get("quest_points", 0) + int(v)}
                    ),
                ),
            }

            reward_msg = "任务奖励：\n"
            # 处理各类奖励
            for reward_type, value in task["reward"].items():
                if reward_type in reward_handlers:
                    data_name, display_name, handler = reward_handlers[reward_type]
                    handler(globals()[data_name], value)
                    reward_msg += f"  {display_name} +{value}\n"
                elif reward_type == "items":
                    for item_id, count in value.items():
                        reward_msg += f"  物品 {item_id} ×{count}\n"

            # 保存更新后的数据
            await self.user_system.update_home_data(user_id, home_data)
            await self.user_system.update_quest_data(user_id, quest_data)
            reward_msg += f"用户 {user_id} 成功领取任务 {task_id} 奖励\n"
            return True, reward_msg.strip()
        except Exception as e:
            error_msg = f"发放任务奖励失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    async def assign_daily_task(self, user_id: str) -> Optional[Dict[str, Any]]:
        """为用户分配日常任务"""
        task = await self.get_random_daily_task()
        if not task:
            return None

        # 从描述提取目标数量
        match = re.search(r"\d+", task["description"])
        target = int(match.group()) if match else 1

        # 更新用户任务数据
        quest_data = await self.user_system.get_quest_data(user_id)
        quest_data["daily"][task["id"]] = {"current": 0, "target": target}
        await self.user_system.update_quest_data(user_id, quest_data)
        return task

    async def get_user_daily_task(self, user_id: str) -> str:
        """处理用户领取日常任务的逻辑并返回消息"""
        try:
            quest_data = await self.user_system.get_quest_data(user_id)
            daily_tasks = quest_data.get("daily", {})

            # 检查是否有活跃任务
            if daily_tasks:
                task_id = next(iter(daily_tasks.keys()))
                active_task = await self.get_task_by_id(task_id)
                if active_task:
                    return (
                        f"你已有一个未完成的日常任务：\n"
                        f"【{active_task['name']}】\n"
                        f"描述：{active_task['description']}\n"
                        f"奖励：{active_task['reward']}\n"
                        f"请完成当前任务后再领取新的任务\n"
                    )

            # 分配新任务
            task = await self.assign_daily_task(user_id)
            if task:
                return (
                    f"已为你分配日常任务：\n"
                    f"【{task['name']}】\n"
                    f"描述：{task['description']}\n"
                    f"奖励：{task['reward']}\n"
                )
        except Exception as e:
            logger.error(f"处理日常任务领取失败: {str(e)}")
            return "处理任务时发生错误，请稍后再试~"

    async def format_user_tasks(self, user_id: str) -> str:
        """格式化用户当前任务进度为字符串"""
        try:
            quest_data = await self.user_system.get_quest_data(user_id)
            daily_tasks = quest_data.get("daily", {})
            weekly_tasks = quest_data.get("weekly", {})
            special_tasks = quest_data.get("special", {})
            if not any([daily_tasks, weekly_tasks, special_tasks]):
                return "你当前没有任何任务，快去领取新任务吧！"
            msg_parts = ["你的当前任务：\n"]
            # 处理日常任务
            if daily_tasks:
                msg_parts += "【日常任务】\n"
                for task_id, progress in daily_tasks.items():
                    task = await self.get_task_by_id(task_id)
                    if task:
                        msg_parts += (
                            f"{task['name']}：{progress['current']}/{progress['target']}\n"
                            f"({task['description']})\n\n"
                        )
            # 处理周任务
            if weekly_tasks:
                msg_parts += "【周任务】\n"
                for task_id, progress in weekly_tasks.items():
                    task = await self.get_task_by_id(task_id)
                    if task:
                        msg_parts += (
                            f"{task['name']}：{progress['current']}/{progress['target']}\n"
                            f"({task['description']})\n\n"
                        )

            # 处理特殊任务
            if special_tasks:
                msg_parts += "【特殊任务】\n"
                for task_id, progress in special_tasks.items():
                    task = await self.get_task_by_id(task_id)
                    if task:
                        msg_parts += (
                            f"{task['name']}：{progress['current']}/{progress['target']} \n"
                            f"({task['description']})\n\n"
                        )
            return "\n".join(msg_parts)
        except Exception as e:
            logger.error(f"格式化用户任务失败: {str(e)}")
            return "查询任务时发生错误，请稍后再试~"
