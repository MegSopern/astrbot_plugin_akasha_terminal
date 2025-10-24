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
    get_user_data_and_backpack,
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
        reward_texts = ""
        if "money" in rewards:
            reward_texts += f"💰{rewards['money']}"
        if "love" in rewards:
            reward_texts += f"，❤️{rewards['love']}"
        if "task_points" in rewards:
            reward_texts += f"，🏆{rewards['task_points']}"
        if "items" in rewards:
            for item_name, count in rewards["items"].items():
                reward_texts += f"，{item_name}×{count}"
        return reward_texts

    def _status_of(self, state: Dict[str, Any]) -> str:
        """获取任务状态符号"""
        return (
            "✅" if state.get("claimed") else ("🎁" if state.get("completed") else "⏳")
        )

    # 判断记录的数据和今天是否在同一周
    def is_same_week(self, date_str: str) -> bool:
        """判断给定日期是否在本周"""
        date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=self.CN_TIMEZONE)
        today = datetime.now(self.CN_TIMEZONE)
        return (
            date.isocalendar()[1] == today.isocalendar()[1] and date.year == today.year
        )

    def get_refresh_time(self) -> str:
        """获取每日任务刷新剩余时间（到明天零点）"""
        now = datetime.now(self.CN_TIMEZONE)
        # 计算明天零点
        next_reset = datetime(
            now.year, now.month, now.day, tzinfo=self.CN_TIMEZONE
        ) + timedelta(days=1)
        diff = next_reset - now
        # 格式化：小时+分钟
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def get_weekly_refresh_time(self) -> str:
        """获取周常任务刷新剩余时间（到下周一零点）"""
        now = datetime.now(self.CN_TIMEZONE)
        current_weekday = now.weekday()  # 0=周一，6=周日
        days_until_monday = (7 - current_weekday) % 7
        # 计算下周一零点
        next_reset = datetime(
            now.year, now.month, now.day, tzinfo=self.CN_TIMEZONE
        ) + timedelta(days=days_until_monday)
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
        is_return_user_data: bool = False,  # 是否返回user_data
    ) -> Dict[str, Any]:
        """获取用户任务数据\n
        如果is_return_user_data为True，则返回(user_data["task"]、user_data)元组\n
        否则默认仅返回user_data["task"]
        """
        if not (self.user_data_path / f"{user_id}.json").exists():
            await event.send(
                event.plain_result("你的信息不存在，请先进行一次签到来注册信息~")
            )
            return
        today = datetime.now(self.CN_TIMEZONE).strftime("%Y-%m-%d")
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

        # 返回任务数据
        if is_return_user_data:
            return user_data["task"], user_data
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
        if not self.is_same_week(user_data["task"].get("last_weekly_refresh")):
            user_data["task"]["weekly"] = {}
            user_data["task"]["last_weekly_refresh"] = today
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
        # 初始化变量为0
        daily_completed = 0
        weekly_completed = 0
        special_completed = 0

        # 统计每日任务已完成数量：收集所有任务的claimed状态，再求和
        daily_tasks = user_task_data.get("daily", {}).values()
        daily_completed = sum(1 for task in daily_tasks if task.get("claimed", False))

        # 统计周常任务已完成数量
        weekly_tasks = user_task_data.get("weekly", {}).values()
        weekly_completed = sum(1 for task in weekly_tasks if task.get("claimed", False))

        # 统计特殊任务已完成数量
        special_tasks = user_task_data.get("special", {}).values()
        special_completed = sum(
            1 for task in special_tasks if task.get("claimed", False)
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
            user_tasks = await self.get_user_tasks(event, user_id)
            task_data = await self.get_task_data()
            achievements, completed_tasks = await self.get_user_achievements(user_tasks)

            # 确保task_data有正确的结构
            daily_tasks = task_data.get("daily_tasks", {})
            weekly_tasks = task_data.get("weekly_tasks", {})
            special_tasks = task_data.get("special_tasks", {})
            task_shop = task_data.get("task_shop", {})

            # 公共工具（仅在本函数内使用，减少重复逻辑）

            def _progress_of(state: Dict[str, Any], target: int) -> Tuple[int, int]:
                progress = min(state.get("progress", 0), target)
                percent = math.floor((progress / target) * 100) if target else 0
                return progress, percent

            def _format_entry(
                task_def: Dict[str, Any], user_state: Dict[str, Any]
            ) -> Dict[str, Any]:
                # 格式化单个任务条目
                p, perc = _progress_of(user_state, task_def["target"])
                return {
                    **task_def,
                    "status": self._status_of(user_state),
                    "progressText": f"{p}/{task_def['target']}",
                    "progressPercent": perc,
                    "rewardsText": self.format_rewards(task_def["rewards"]),
                }

            def _build_section(
                task_defs: Dict[str, Dict[str, Any]],
                user_target_tasks: Dict[str, Dict[str, Any]],
                skip_one_time_claimed: bool = False,
            ) -> List[Dict[str, Any]]:
                # 构建任务部分列表
                result: List[Dict[str, Any]] = []
                for tid, task_item in task_defs.items():
                    state = user_target_tasks.get(
                        tid, {"progress": 0, "completed": False, "claimed": False}
                    )
                    # 特殊任务：跳过已领取的一次性任务
                    if (
                        skip_one_time_claimed or task_item.get("one_time", False)
                    ) and state.get("claimed"):
                        continue
                    result.append(_format_entry(task_item, state))
                return result

            # 构建模板数据
            template_data = {
                "user_id": user_id,
                "user_name": await get_nickname(event, user_id) or "未知用户",
                "task_points": user_tasks.get("task_points", 0),
                "daily_tasks": [],
                "weekly_tasks": [],
                "special_tasks": [],
                "completed_tasks": completed_tasks,
                "task_shop": [],
                "achievements": [],
            }

            try:
                # 统一构建三类任务
                template_data["daily_tasks"] = _build_section(
                    daily_tasks,
                    user_tasks.get("daily", {}),
                    skip_one_time_claimed=False,
                )
                template_data["weekly_tasks"] = _build_section(
                    weekly_tasks,
                    user_tasks.get("weekly", {}),
                    skip_one_time_claimed=False,
                )
                template_data["special_tasks"] = _build_section(
                    special_tasks,
                    user_tasks.get("special", {}),
                    skip_one_time_claimed=True,  # 跳过已领取的特殊任务
                )

                # 任务商店
                for _, item in task_shop.items():
                    template_data["task_shop"].append(
                        {
                            **item,
                            "affordable": (
                                user_tasks.get("task_points", 0) >= item.get("cost", 0)
                            ),
                        }
                    )

                # 成就
                template_data["achievements"] = [
                    {
                        **ach,
                        "status": "🏆" if ach["unlocked"] else "🔒",
                        "progressText": f"{ach['progress']}/{ach['target']}"
                        if ach["type"] == "count"
                        else "",
                        "progressPercent": (
                            math.floor((ach["progress"] / ach["target"]) * 100)
                            if ach["type"] == "count"
                            else 0
                        ),
                    }
                    for ach in achievements
                ]
            except Exception as e:
                logger.error(f"格式化任务数据失败: {str(e)}")
                await event.send(event.plain_result("处理任务数据时出错，请稍后重试"))
                return

            try:
                # 统计数据
                def _count_done(entries: List[Dict[str, Any]]) -> int:
                    return sum(bool(q.get("status") == "✅") for q in entries)

                daily_completed = _count_done(template_data["daily_tasks"])
                weekly_completed = _count_done(template_data["weekly_tasks"])
                special_completed = _count_done(template_data["special_tasks"])

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
                daily_refresh = self.get_refresh_time()
                weekly_refresh = self.get_weekly_refresh_time()

                message = f"📋 {template_data['user_name']}的任务列表\n"
                message += f"🏆 任务点数: {template_data['task_points']}\n"
                message += f"📊 完成率: {completion_rate}% ({total_completed}/{total_tasks})\n\n"
                # 每日任务
                message += "📅 每日任务:\n"
                for task in template_data["daily_tasks"][:3]:
                    message += (
                        f"{task['status']} {task['name']} - {task['progressText']}\n"
                    )

                # 周常任务（按原样在前面插入一个换行）
                message += "\n📆 周常任务:\n"
                for task in template_data["weekly_tasks"][:3]:
                    message += (
                        f"{task['status']} {task['name']} - {task['progressText']}\n"
                    )

                # 刷新提示
                message += f"🔄 每日任务刷新: {daily_refresh}\n"
                message += f"🔄 周常任务刷新: {weekly_refresh}\n"

                await event.send(event.plain_result(message))
                return
            except Exception as e:
                logger.error(f"构建任务消息失败: {str(e)}")
                await event.send(event.plain_result("构建任务消息时出错，请稍后重试"))
                return
        except Exception as e:
            logger.error(f"获取用户任务失败: {str(e)}")
            await event.send(event.plain_result("获取用户任务信息失败，请稍后重试"))
            return

    async def format_user_daily_tasks(self, event: AiocqhttpMessageEvent):
        """格式化用户每日任务信息"""
        user_id = str(event.get_sender_id())
        try:
            user_tasks = await self.get_user_tasks(event, user_id)
            task_data = await self.get_task_data()
            daily_tasks = task_data.get("daily_tasks", {})

            message = "📅 每日任务 📅\n━━━━━━━━━━━━━━━\n"
            for task_id, task in daily_tasks.items():
                user_task = user_tasks.get("daily", {}).get(
                    task_id, {"progress": 0, "completed": False, "claimed": False}
                )
                progress = min(user_task["progress"], task["target"])
                progress_percent = progress / task["target"] * 100
                status = self._status_of(user_task)

                message += f"{status} {task['name']}\n   📝 {task['description']}\n"

                if task.get("requirement"):
                    message += f"   ⚠️ {task['requirement']}\n"
                message += f"   📊 进度: {progress}/{task['target']} ({progress_percent:.1f}%)\n"

                # 显示奖励
                rewards_text = self.format_rewards(task["rewards"])
                message += f"   🎁 奖励: {rewards_text}\n"

                if user_task["completed"] and not user_task["claimed"]:
                    message += f"   💡 使用 #领取奖励 {task['name']} 领取奖励\n"
                message += "──────────────\n"

            # 显示刷新时间
            message += f"\n🔄 任务将在 {self.get_refresh_time()} 后刷新"
            await event.send(event.plain_result(message))

        except Exception as e:
            logger.error(f"显示每日任务失败: {str(e)}")
            await event.send(event.plain_result("每日任务暂时无法访问，请稍后再试"))

    async def format_user_weekly_tasks(self, event: AiocqhttpMessageEvent):
        """格式化用户周常任务信息"""
        user_id = str(event.get_sender_id())
        try:
            user_tasks = await self.get_user_tasks(event, user_id)
            task_data = await self.get_task_data()
            weekly_tasks = task_data.get("weekly_tasks", {})

            message = "📆 周常任务 📆\n"
            message += "━━━━━━━━━━━━━━━\n"

            for task_id, task in weekly_tasks.items():
                user_task = user_tasks.get("weekly", {}).get(
                    task_id, {"progress": 0, "completed": False, "claimed": False}
                )
                progress = min(user_task["progress"], task["target"])
                progress_percent = progress / task["target"] * 100
                status = self._status_of(user_task)

                message += f"{status} {task['name']}\n"
                message += f"   📝 {task['description']}\n"
                if task.get("requirement", ""):
                    message += f"   ⚠️ {task['requirement']}\n"
                message += f"   📊 进度: {progress}/{task['target']} ({progress_percent:.1f}%)\n"

                # 显示奖励
                rewards_text = self.format_rewards(task["rewards"])
                message += f"   🎁 奖励: {rewards_text}\n"

                if user_task["completed"] and not user_task["claimed"]:
                    message += f"   💡 使用 #领取奖励 {task['name']} 领取奖励\n"
                message += "───────────────\n"

            # 显示刷新时间
            message += f"\n🔄 任务将在 {self.get_weekly_refresh_time()} 后刷新"
            await event.send(event.plain_result(message))
        except Exception as e:
            logger.error(f"显示周常任务失败: {str(e)}")
            await event.send(event.plain_result("周常任务暂时无法访问，请稍后再试"))

    async def format_user_special_tasks(self, event: AiocqhttpMessageEvent):
        """格式化用户特殊任务信息"""
        user_id = str(event.get_sender_id())
        try:
            user_tasks = await self.get_user_tasks(event, user_id)
            task_data = await self.get_task_data()
            special_tasks = task_data.get("special_tasks", {})

            message = "⭐ 特殊任务 ⭐\n"
            message += "━━━━━━━━━━━━━━━\n"

            for task_id, task in special_tasks.items():
                user_task = user_tasks.get("special", {}).get(
                    task_id, {"progress": 0, "completed": False, "claimed": False}
                )

                # 跳过已完成的一次性任务
                if task.get("one_time") or user_task["claimed"]:
                    continue

                progress = min(user_task["progress"], task["target"])
                progress_percent = progress / task["target"] * 100
                status = self._status_of(user_task)

                message += f"{status} {task['name']} {'（限时）' if task.get('one_time') else ''}\n"
                message += f"   📝 {task['description']}\n"
                if task.get("requirement"):
                    message += f"   ⚠️ {task['requirement']}\n"
                message += f"   📊 进度: {progress}/{task['target']} ({progress_percent:.1f}%)\n"

                # 显示奖励
                rewards_text = self.format_rewards(task["rewards"])
                message += f"   🎁 奖励: {rewards_text}\n"

                if user_task["completed"] and not user_task["claimed"]:
                    message += f"   💡 使用 #领取奖励 {task['name']} 领取奖励\n"

                message += "───────────────\n"
            await event.send(event.plain_result(message))

        except Exception as e:
            logger.error(f"显示特殊任务失败: {str(e)}")
            await event.send(event.plain_result("特殊任务暂时无法访问，请稍后再试"))

    async def handle_claim_reward(self, event: AiocqhttpMessageEvent, parts: list[str]):
        """处理用户领取任务奖励请求"""
        user_id = str(event.get_sender_id())
        try:
            if not parts:
                await event.send(
                    event.plain_result(
                        "请指定要领取奖励的任务名称！\n使用方法: /领取奖励 [任务名称]"
                    )
                )
                return
            task_name = parts[0]

            try:
                user_tasks, user_data = await self.get_user_tasks(
                    event, user_id, is_return_user_data=True
                )
                backpack = await get_user_data_and_backpack(user_id, "user_backpack")
                task_data = await self.get_task_data()

                # 查找任务
                task = None
                task_type = None
                user_task = None  # 初始化变量为None
                found = False  # 标志位：是否找到任务

                # 检查所有任务类型
                for task_type_key in [
                    "daily_tasks",
                    "weekly_tasks",
                    "special_tasks",
                ]:  # 遍历当前类型下的所有任务
                    for tid, user_task in user_tasks.get(task_type_key, {}).items():
                        if user_task["name"] == task_name:
                            task = task_data[task_type_key].get(tid)
                            task_type = task_type_key.replace("_tasks", "")
                            found = True  # 标记找到任务
                            break  # 跳出内层循环
                    if found:
                        break  # 找到任务后跳出外层循环

                if not user_task:
                    await event.send(
                        event.plain_result(f"你没有名为「{task_name}」的任务！")
                    )
                    return
                if user_task["claimed"]:
                    await event.send(
                        event.plain_result(f"你已经领取过「{task_name}」的奖励！")
                    )
                    return
                if not user_task["completed"]:
                    await event.send(
                        event.plain_result(f"任务 {task_name} 尚未完成，无法领取奖励！")
                    )
                    return
            except Exception as e:
                logger.error(f"查找任务失败: {str(e)}")
                await event.send(event.plain_result("查找任务失败，请稍后再试"))
                return

            try:
                # 处理奖励发放
                rewards = []
                # 金币奖励
                if "money" in task["rewards"]:
                    user_data["home"]["money"] = (
                        user_data["home"].get("money", 0) + task["rewards"]["money"]
                    )
                    rewards.append(f"💰 {task['rewards']['money']} 金币")

                # 好感度奖励
                if "love" in task["rewards"]:
                    user_data["home"]["love"] = (
                        user_data["home"].get("love", 0) + task["rewards"]["love"]
                    )
                    rewards.append(f"❤️ {task['rewards']['love']} 好感度")

                # 道具奖励
                if "items" in task["rewards"]:
                    for item_name, count in task["rewards"]["items"].items():
                        rewards.append(f"{item_name} ×{count}")
                        backpack[item_name] = backpack.get(item_name, 0) + count

                # 任务点数奖励
                if "task_points" in task["rewards"]:
                    user_tasks["task_points"] = (
                        user_tasks.get("task_points", 0)
                        + task["rewards"]["task_points"]
                    )
                    rewards.append(f"🏆 {task['rewards']['task_points']} 任务点数")

                msg_parts = [Comp.Plain("\n".join(rewards))]
                # 构建奖励消息

                message = [
                    Comp.At(qq=user_id),
                    Comp.Plain(
                        "：\n🎉 任务完成！\n"
                        f"📋 {task_name}\n"
                        "🎁 获得奖励:\n"
                        f"{msg_parts}\n"
                        f"💰 当前金币: {user_data.get('money', 0)}\n"
                        f"🏆 任务点数: {user_tasks.get('task_points', 0)}"
                    ),
                ]
                await event.send(event.chain_result(message))

                # 标记为已领取
                user_data["task"][task_type][task["id"]]["claimed"] = True

                # 保存数据
                await write_json(self.user_data_path / f"{user_id}.json", user_data)
                await write_json(self.backpack_path / f"{user_id}.json", backpack)

            except Exception as e:
                logger.error(f"发放任务奖励失败: {str(e)}")
                await event.send(event.plain_result("发放任务奖励失败，请稍后再试"))
                return
        except Exception as e:
            logger.error(f"领取奖励失败: {str(e)}")
            await event.send(event.plain_result("领取奖励失败，请稍后再试"))

    async def format_task_shop_items(self, event: AiocqhttpMessageEvent):
        """格式化任务商店物品列表"""
        user_id = str(event.get_sender_id())
        try:
            user_tasks = await self.get_user_tasks(event, user_id)
            task_data = await self.get_task_data()
            task_shop = task_data.get("task_shop", {})
            message = [
                Comp.Plain(
                    "🏪 任务商店 🏪\n"
                    f"🏆 你的任务点数: {user_tasks.get('task_points', 0)}\n"
                    "━━━━━━━━━━━━━━━━\n"
                )
            ]
            for item_name, item in task_shop.items():
                price = item.get("task_point_price", 0)
                user_points = user_tasks.get("task_points", 0) >= price

                message.append(
                    Comp.Plain(
                        f"[{item_name}]\n"
                        f"   📝 {item['description']}\n"
                        f"   🏆 价格: {price} 任务点数\n"
                        f"   {'✅ 可购买' if user_points else '❌ 点数不足'}\n"
                        f"   💡 使用 #虚空兑换 {item['name']} 进行兑换\n"
                        f"   ────────────────\n"
                    )
                )
            await event.send(event.chain_result(message))
        except Exception as e:
            logger.error(f"显示任务商店失败: {str(e)}")
            await event.send(event.plain_result("任务商店暂时无法访问，请稍后再试"))

    async def handle_task_shop_purchase(
        self, event: AiocqhttpMessageEvent, parts: list[str]
    ):
        """处理任务商店物品购买请求"""
        user_id = str(event.get_sender_id())
        try:
            if not parts:
                await event.send(
                    event.plain_result(
                        "请指定要兑换的物品名称！\n使用方法: /虚空兑换 [物品名称]"
                    )
                )
                return

            item_name = parts[0]
            quantity = 1

            if len(parts) >= 2 and parts[1].isdigit():
                quantity = int(parts[1])
                if quantity <= 0:
                    await event.send(event.plain_result("兑换数量必须为正整数！"))
                    return
            else:
                await event.send(
                    event.plain_result(
                        "请指定要兑换的物品数量！\n使用方法: /虚空兑换 [物品名称] [数量]"
                    )
                )
                return
            try:
                user_tasks, user_data = await self.get_user_tasks(
                    event, user_id, is_return_user_data=True
                )
                backpack = await get_user_data_and_backpack(user_id, "user_backpack")
                task_data = await self.get_task_data()
                task_shop = task_data.get("task_shop", {})
                item = task_shop.get(item_name, {})

                if not item:
                    await event.send(
                        event.plain_result(f"任务商店中没有名为「{item_name}」的物品！")
                    )
                    return

                price = item.get("task_point_price", 0)
                if user_tasks.get("task_points", 0) < price * quantity:
                    await event.send(
                        event.plain_result(
                            f"你的任务点数不足！需要 {price * quantity} 点，你只有 {user_tasks['task_points']} 点"
                        )
                    )
                    return
            except Exception as e:
                logger.error(f"查找商店物品失败: {str(e)}")
                await event.send(event.plain_result("查找商店物品失败，请稍后再试"))
                return

            try:
                # 扣除任务点数
                user_data["task"]["task_points"] -= price * quantity
                # 添加物品到背包
                backpack[item_name] = backpack.get(item_name, 0) + quantity

                message = [
                    Comp.At(qq=user_id),
                    Comp.Plain(
                        f"🛍️ 兑换成功！\n"
                        f"🎁 你获得了: {item_name} × {quantity}\n"
                        f"商品描述：{item['description']}\n"
                        f"💎 消耗: {price} 任务点数\n"
                        f"🏆 剩余任务点数: {user_tasks.get('task_points', 0)}"
                    ),
                ]
                await write_json(self.user_data_path / f"{user_id}.json", user_data)
                await write_json(self.backpack_path / f"{user_id}.json", backpack)
                await event.send(event.chain_result(message))
            except Exception as e:
                logger.error(f"处理兑换失败: {str(e)}")
                await event.send(event.plain_result("处理兑换失败，请稍后再试"))
                return
        except Exception as e:
            logger.error(f"兑换物品失败: {str(e)}")
            await event.send(event.plain_result("兑换物品失败，请稍后再试"))

    async def handle_reset_tasks(self, event: AiocqhttpMessageEvent):
        """重置用户任务"""
        user_id = str(event.get_sender_id())
        try:
            # 检查刷新冷却时间
            refresh_cost = 1000
            user_tasks, user_data = await self.get_user_tasks(
                event, user_id, is_return_user_data=True
            )
            if user_data.get("money", 0) < refresh_cost:
                await event.send(
                    event.plain_result(
                        f"刷新每日任务需要 {refresh_cost} 金币，你的金币不足"
                    )
                )
                return
            user_data["money"] -= refresh_cost
            # 重置每日任务
            today = datetime.now(self.CN_TIMEZONE).strftime("%Y-%m-%d")
            user_data["task"]["daily"] = {}
            user_data["task"]["last_daily_reset"] = today
            await write_json(self.user_data_path / f"{user_id}.json", user_data)

            message = [
                Comp.at(qq=user_id),
                Comp.Plain(
                    "：\n"
                    "✅ 任务刷新成功！\n"
                    f"💰 花费: {refresh_cost} 金币\n"
                    "🔄 每日任务进度已重置\n"
                    "💡 使用 /任务列表 查看新任务"
                ),
            ]
            await event.send(event.chain_result(message))
        except Exception as e:
            logger.error(f"获取刷新冷却时间失败: {str(e)}")
            await event.send(event.plain_result("获取刷新冷却时间失败，请稍后再试"))
            return

    async def update_task_progress(
        self,
        event: AiocqhttpMessageEvent,
        user_id: str,
        track_key: str,
        is_increment: bool = True,
        value: int = 1,
    ) -> bool:
        """
        更新任务进度（供其他系统调用）\n
        user_id: 用户ID\n
        track_key: 任务追踪键\n
        value: 增量值或设置值，默认1\n
        is_increment: 是否为增量更新，False则为设置最大值，默认True
        """
        try:
            user_tasks, user_data = await self.get_user_tasks(
                event, user_id, is_return_user_data=True
            )
            task_data = await self.get_task_data()

            # 确保task_data有正确的结构
            tasks_categories = {
                "daily": task_data.get("daily_tasks", {}),
                "weekly": task_data.get("weekly_tasks", {}),
                "special": task_data.get("special_tasks", {}),
            }
            updated = False
            for task_category, tasks in tasks_categories.items():
                for task_id, task in tasks.items():
                    if track_key == task.get("itrack_key"):
                        if task_category not in user_tasks:
                            user_tasks[task_category] = {}
                        if task_id not in user_tasks[task_category]:
                            user_tasks[task_category][task_id] = {
                                "progress": 0,
                                "completed": False,
                                "claimed": False,
                            }

                        user_task = user_tasks[task_category][task_id]
                        if not user_task.get("completed"):
                            if is_increment:
                                user_task["progress"] += value
                            else:
                                user_task["progress"] = max(
                                    tasks[task_id].get("target", 0), value
                                )

                            if user_task["progress"] >= tasks[task_id].get(
                                "target", float("inf")
                            ):
                                user_task["completed"] = True
                            updated = True
            user_data["task"] = user_tasks
            # 写回用户数据文件
            await write_json(self.user_data_path / f"{user_id}.json", user_data)
            return updated
        except Exception as e:
            logger.error(f"更新用户 {user_id} 任务进度失败: {str(e)}")
