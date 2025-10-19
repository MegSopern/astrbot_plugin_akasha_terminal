import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.star import StarTools
from astrbot.core.message.components import At
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from ..utils.utils import (
    get_nickname,
    read_json,
    write_json,
)


class Task:
    def __init__(self):
        # 初始化路径
        PLUGIN_DATA_DIR = Path(StarTools.get_data_dir("astrbot_plugin_akasha_terminal"))
        self.user_data_path = PLUGIN_DATA_DIR / "user_data"
        self.backpack_path = PLUGIN_DATA_DIR / "user_backpack"
        self.task_file = Path(__file__).parent.parent / "data" / "task.json"
        # 设置「中国标准时间」
        self.CN_TIMEZONE = ZoneInfo("Asia/Shanghai")

        # 确保数据目录存在
        self.user_data_path.mkdir(parents=True, exist_ok=True)
        self.backpack_path.mkdir(parents=True, exist_ok=True)
        self.task_file.parent.mkdir(parents=True, exist_ok=True)

    def format_rewards(self, rewards: Dict[str, Any]) -> str:
        """格式化奖励文本"""
        reward_texts = []
        if "money" in rewards:
            reward_texts.append(f"💰{rewards['money']}")
        if "love" in rewards:
            reward_texts.append(f"❤️{rewards['love']}")
        if "task_points" in rewards:
            reward_texts.append(f"🏆{rewards['task_points']}")
        if "items" in rewards:
            for item_name, count in rewards["items"].items():
                reward_texts.append(f"{item_name}×{count}")
        return ", ".join(reward_texts) or "无奖励"

    # 判断记录的数据和今天是否在同一周
    def is_same_week(self, date_str: str) -> bool:
        """判断给定日期是否在本周"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now(self.CN_TIMEZONE)
        return (
            date.isocalendar()[1] == today.isocalendar()[1] and date.year == today.year
        )

    def get_refresh_time(self) -> str:
        """获取每日任务刷新剩余时间（到明天零点）"""
        now = datetime.now()
        # 计算明天零点
        next_reset = datetime(now.year, now.month, now.day) + timedelta(days=1)
        diff = next_reset - now
        # 格式化：小时+分钟
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def get_weekly_refresh_time(self) -> str:
        """获取周常任务刷新剩余时间（到下周一零点）"""
        now = datetime.now()
        current_weekday = now.weekday()  # 0=周一，6=周日
        days_until_monday = 7 - current_weekday
        # 计算下周一零点
        next_reset = datetime(now.year, now.month, now.day) + timedelta(
            days=days_until_monday
        )
        diff = next_reset - now
        # 格式化：天+小时（无天则只显示小时）
        days, hours = diff.days, diff.seconds // 3600
        return f"{days}d {hours}h" if days > 0 else f"{hours}h"

    async def get_task_data(self) -> Dict[str, Any]:
        """获取任务数据，确保数据完整性"""
        try:
            task_data = await read_json(self.task_file)
            # 检查数据完整性
            is_data_complete = task_data and task_data["system_initialized"]

            # 如果数据不完整，尝试重新初始化
            if not is_data_complete:
                task_data = await read_json(self.task_file)
                task_data["last_daily_refresh"] = datetime.now(
                    self.CN_TIMEZONE
                ).strftime("%Y-%m-%d")
                task_data["last_weekly_refresh"] = datetime.now(
                    self.CN_TIMEZONE
                ).strftime("%Y-%m-%d")
                task_data["system_initialized"] = True
                await write_json(self.task_file, task_data)
            return task_data
        except Exception as e:
            logger.error(f"获取任务数据失败: {str(e)}")

    async def get_user_tasks(
        self,
        event: AiocqhttpMessageEvent,
        user_id: str,
        user_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """获取用户任务数据,如果提供了user_data则直接使用"""
        if not (self.user_data_path / f"{user_id}.json").exists():
            await event.send(
                event.plain_result("你的信息不存在，请先进行一次签到来注册信息~")
            )
            return
        today = datetime.now(self.CN_TIMEZONE).strftime("%Y-%m-%d")
        if not user_data:
            user_data = await read_json(self.user_data_path / f"{user_id}.json")
        if (
            not user_data["task"]["last_daily_reset"]
            or not user_data["task"]["last_weekly_refresh"]
        ):
            user_data["task"]["last_daily_reset"] = today
            user_data["task"]["last_weekly_refresh"] = today
            await write_json(self.user_data_path / f"{user_id}.json", user_data)

        # 检查是否需要重置
        new_data = await self.check_task_reset(user_id, user_data, today)
        if new_data:
            user_data = new_data
        return user_data["task"]

    async def check_task_reset(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        today: str,
    ) -> Optional[Dict[str, Any]]:
        """检查并重置过期任务"""
        reset = False
        # 重置每日任务
        if user_data["task"].get("last_daily_reset") != today:
            user_data["task"]["daily"] = {}
            user_data["task"]["last_daily_reset"] = today
            reset = True

        # 重置周常任务
        if not self.is_same_week(user_data["task"].get("last_weekly_reset")):
            user_data["task"]["weekly"] = {}
            user_data["task"]["last_weekly_reset"] = today
            reset = True
        # 保存更新后的任务数据
        if reset:
            await write_json(self.user_data_path / f"{user_id}.json", user_data)
            return user_data
        return None

    async def get_completed_tasks(
        self, user_task_data: Dict[str, Any]
    ) -> Dict[str, int]:
        """获取已完成任务统计"""
        # 统计各类型已完成任务数量
        daily_completed = sum(
            1 for q in user_task_data.get("daily", {}).values() if q.get("claimed")
        )
        weekly_completed = sum(
            1 for q in user_task_data.get("weekly", {}).values() if q.get("claimed")
        )
        special_completed = sum(
            1 for q in user_task_data.get("special", {}).values() if q.get("claimed")
        )

        return {
            "daily": daily_completed,
            "weekly": weekly_completed,
            "special": special_completed,
            "total": daily_completed + weekly_completed + special_completed,
        }

    async def get_user_achievements(
        self, user_task_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """获取用户成就"""
        completed_tasks = await self.get_completed_tasks(user_task_data)

        return [
            {
                "name": "任务新手",
                "description": "完成第一个任务",
                "target": 1,
                "progress": min(1, completed_tasks["total"]),
                "unlocked": completed_tasks["total"] >= 1,
                "type": "count",
            },
            {
                "name": "勤劳工作者",
                "description": "完成10个任务",
                "target": 10,
                "progress": min(10, completed_tasks["total"]),
                "unlocked": completed_tasks["total"] >= 10,
                "type": "count",
            },
            {
                "name": "任务大师",
                "description": "完成50个任务",
                "target": 50,
                "progress": min(50, completed_tasks["total"]),
                "unlocked": completed_tasks["total"] >= 50,
                "type": "count",
            },
            {
                "name": "点数收集者",
                "description": "累计获得1000任务点数",
                "target": 1000,
                "progress": min(1000, user_task_data.get("task_points", 0)),
                "unlocked": (user_task_data.get("task_points", 0) >= 1000),
                "type": "count",
            },
        ], completed_tasks

    async def format_user_tasks(self, event: AiocqhttpMessageEvent) -> str:
        """格式化用户任务信息"""
        user_id = str(event.get_sender_id())
        try:
            user_data = await read_json(self.user_data_path / f"{user_id}.json")
            task_data = await self.get_task_data()
            user_tasks = await self.get_user_tasks(event, user_id, user_data)
            achievements, completed_tasks = await self.get_user_achievements(user_tasks)

            # 确保task_data有正确的结构
            daily_tasks = task_data.get("daily_tasks", {})
            weekly_tasks = task_data.get("weekly_tasks", {})
            special_tasks = task_data.get("special_tasks", {})
            task_shop = task_data.get("task_shop", {})

            # 构建模板数据
            template_data = {
                "user_id": user_id,
                "user_name": get_nickname(event, user_id) or "未知用户",
                "task_points": user_tasks.get("task_points", 0),
                "daily_tasks": [],
                "weekly_tasks": [],
                "special_tasks": [],
                "completed_tasks": completed_tasks,
                "task_shop": [],
                "achievements": [],
            }
            try:
                # 处理每日任务
                for task_id, task in daily_tasks.items():
                    user_daily_task = user_tasks.get("daily", {}).get(
                        task_id, {"progress": 0, "completed": False, "claimed": False}
                    )
                    progress = min(user_daily_task["progress"], task["target"])
                    template_data["daily_tasks"].append(
                        {
                            **task,
                            "status": "✅"
                            if user_daily_task["claimed"]
                            else "🎁"
                            if user_daily_task["completed"]
                            else "⏳",
                            "progressText": f"{progress}/{task['target']}",
                            "progressPercent": math.floor(
                                (progress / task["target"]) * 100
                            ),
                            "rewardsText": self.format_rewards(task["rewards"]),
                        }
                    )

                # 处理周常任务
                for task_id, task in weekly_tasks.items():
                    user_task = user_tasks.get("weekly", {}).get(
                        task_id, {"progress": 0, "completed": False, "claimed": False}
                    )
                    progress = min(user_task["progress"], task["target"])
                    template_data["weekly_tasks"].append(
                        {
                            **task,
                            "status": "✅"
                            if user_task["claimed"]
                            else "🎁"
                            if user_task["completed"]
                            else "⏳",
                            "progressText": f"{progress}/{task['target']}",
                            "progressPercent": math.floor(
                                (progress / task["target"]) * 100
                            ),
                            "rewardsText": self.format_rewards(task["rewards"]),
                        }
                    )

                # 处理特殊任务
                for task_id, task in special_tasks.items():
                    user_task = user_tasks.get("special", {}).get(
                        task_id, {"progress": 0, "completed": False, "claimed": False}
                    )
                    # 跳过已完成的一次性任务
                    if task.get("one_time") and user_task["claimed"]:
                        continue

                    progress = min(user_task["progress"], task["target"])
                    template_data["special_tasks"].append(
                        {
                            **task,
                            "status": "✅"
                            if user_task["claimed"]
                            else "🎁"
                            if user_task["completed"]
                            else "⏳",
                            "progressText": f"{progress}/{task['target']}",
                            "progressPercent": math.floor(
                                (progress / task["target"]) * 100
                            ),
                            "rewardsText": self.format_rewards(task["rewards"]),
                        }
                    )

                # 处理任务商店
                for item_id, item in task_shop.items():
                    template_data["task_shop"].append(
                        {
                            **item,
                            "affordable": (
                                user_tasks.get("quest_points", 0) >= item.get("cost", 0)
                            ),
                        }
                    )
                # 处理成就
                for achievement in achievements:
                    template_data["achievements"].append(
                        {
                            **achievement,
                            "status": "🏆" if achievement["unlocked"] else "🔒",
                            "progressText": f"{achievement['progress']}/{achievement['target']}"
                            if achievement["type"] == "count"
                            else "",
                            "progressPercent": math.floor(
                                (achievement["progress"] / achievement["target"]) * 100
                            )
                            if achievement["type"] == "count"
                            else 0,
                        }
                    )
            except Exception as e:
                logger.error(f"格式化任务数据失败: {str(e)}")
                await event.send(event.plain_result("处理任务数据时出错，请稍后重试"))
                return

            try:
                # 计算统计数据
                daily_completed = len(
                    [q for q in template_data["daily_tasks"] if q["status"] == "✅"]
                )
                weekly_completed = len(
                    [q for q in template_data["weekly_tasks"] if q["status"] == "✅"]
                )
                special_completed = len(
                    [q for q in template_data["special_tasks"] if q["status"] == "✅"]
                )

                total_tasks = (
                    len(template_data["daily_tasks"])
                    + len(template_data["weekly_tasks"])
                    + len(template_data["special_tasks"])
                )
                total_completed = daily_completed + weekly_completed + special_completed
                completion_rate = (
                    math.floor((total_completed / total_tasks) * 100)
                    if total_tasks > 0
                    else 0
                )
            except Exception as e:
                logger.error(f"计算任务统计数据失败: {str(e)}")
                await event.send(
                    event.plain_result("计算任务统计数据时出错，请稍后重试")
                )
                return

            try:
                # 构建最终消息
                message = [Comp.Plain(f"📋 {template_data['user_name']}的任务列表\n")]
                message.append(
                    Comp.Plain(f"🏆 任务点数: {template_data['task_points']}\n")
                )
                message.append(
                    Comp.Plain(
                        f"📊 完成率: {completion_rate}% ({total_completed}/{total_tasks})\n\n"
                    )
                )

                message.append(Comp.Plain("📅 每日任务:\n"))
                for quest in template_data["daily_tasks"][:3]:  # 只显示前3个
                    message.append(
                        Comp.Plain(
                            f"{quest['status']} {quest['name']} - {quest['progressText']}\n"
                        )
                    )

                message.append(Comp.Plain("\n📆 周常任务:\n"))
                for quest in template_data["weekly_tasks"][:3]:  # 只显示前3个
                    message.append(
                        Comp.Plain(
                            f"{quest['status']} {quest['name']} - {quest['progressText']}\n"
                        )
                    )

                message.append(
                    Comp.Plain(f"🔄 每日任务刷新: {self.get_refresh_time()}\n")
                )
                message.append(
                    Comp.Plain(f"🔄 周常任务刷新: {self.get_weekly_refresh_time()}\n")
                )
                await event.send(event.chain_result(message))
                return
            except Exception as e:
                logger.error(f"构建任务消息失败: {str(e)}")
                await event.send(event.plain_result("构建任务消息时出错，请稍后重试"))
                return
        except Exception as e:
            logger.error(f"获取用户任务失败: {str(e)}")
            await event.send(event.plain_result("获取用户任务信息失败，请稍后重试"))
            return
