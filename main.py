import re

import aiohttp  # noqa: F401
import astrbot.api.message_components as Comp
from aiocqhttp import CQHttp  # noqa: F401
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .core.task import Task
from .core.user import User
from .utils.utils import *


@register(
    "astrbot_plugin_akasha_terminal",
    "Xinhaihai & Xinhaihai/wbndm1234 & MegSopern",
    "一个功能丰富的astrbot插件，提供完整的游戏系统",
    "1.0.0",
)
class AkashaTerminal(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        try:
            # 用户系统
            self.user_system = User()
            # 任务系统
            self.task_system = Task()
            logger.info("Akasha Terminal插件初始化完成")
        except Exception as e:
            logger.error(f"Akasha Terminal插件初始化失败:{str(e)}")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        logo_AATP()

    @filter.command("个人信息", alias="查看信息")
    async def get_user_info(
        self, event: AstrMessageEvent, input_id: int | str | None = None
    ):
        """获取用户信息"""
        try:
            # 获取用户ID，默认为发送者ID
            user_id = event.get_sender_id()
            if at_id := next(
                (
                    str(seg.qq)
                    for seg in event.get_messages()
                    if isinstance(seg, Comp.At)
                ),
                None,
            ):
                user_id = str(at_id)
            elif input_id is not None and str(input_id) != str(user_id):
                user_id = str(input_id)
            else:
                user_id = str(user_id)
            user_data = await self.user_system.get_user(user_id)
            battle_data = await self.user_system.get_battle_data(user_id)
            home_data = await self.user_system.get_home_data(user_id)

            message = (
                f"用户信息:\n"
                f"ID: {user_id}\n"
                f"等级: {user_data.get('level', 1)}\n"
                f"经验: {battle_data.get('experience', 0)}\n"
                f"金钱: {home_data.get('money', 0)}\n"
                f"好感度: {home_data.get('love', 0)}"
            )

            yield event.plain_result(message)
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            yield event.plain_result(f"获取用户信息失败: {str(e)}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("增加金钱", alias="添加金钱")
    async def add_user_money(
        self, event: AstrMessageEvent, input_id: int | str | None = None
    ):
        """增加用户金钱，使用方法: /增加金钱 金额"""
        try:
            user_id = event.get_sender_id()
            # 用正则提取金额（支持中文、空格、@等混合输入）
            if match := re.findall(r"(\d+)", event.message_str):
                amount = int(match[0])
            else:
                yield event.plain_result(
                    "请指定金额，使用方法:/增加金钱 金额 qq 或 /增加金钱 金额 @用户"
                )
                return
            if amount <= 0:
                yield event.plain_result("金额必须为正整数")
                return
            if at_id := next(
                (
                    str(seg.qq)
                    for seg in event.get_messages()
                    if isinstance(seg, Comp.At)
                ),
                None,
            ):
                user_id = str(at_id)
            elif len(match) >= 2:  # 如果有第二个数字，则作为ID
                user_id = str(match[1])
            elif input_id is not None and str(input_id) != str(user_id):
                user_id = str(input_id)
            else:
                user_id = str(user_id)
            # 获取当前家园数据
            home_data = await self.user_system.get_home_data(user_id)
            # 更新金钱
            home_data["money"] = home_data.get("money", 0) + amount
            # 保存数据
            await self.user_system.update_home_data(user_id, home_data)

            yield event.plain_result(
                f"成功增加 {amount} 金钱，当前金钱: {home_data['money']}"
            )
        except ValueError:
            yield event.plain_result("金额必须是数字")
        except Exception as e:
            logger.error(f"增加金钱失败: {str(e)}")
            yield event.plain_result(f"操作失败: {str(e)}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("用户列表")
    async def list_all_users(self, event: AstrMessageEvent):
        """获取所有用户列表"""
        try:
            user_list = await self.user_system.get_user_list()
            if not user_list:
                yield event.plain_result("暂无用户数据")
                return

            message = "用户列表:\n" + "\n".join(user_list)
            yield event.plain_result(message)
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            yield event.plain_result(f"操作失败: {str(e)}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    @filter.command("领取任务", alias="获取任务")
    async def get_daily_task(self, event: AstrMessageEvent):
        """领取日常任务"""
        user_id = str(event.get_sender_id())
        # 检查是否已有活跃的日常任务
        quest_data = await self.user_system.get_quest_data(user_id)
        daily_tasks = quest_data.get("daily", {})
        if daily_tasks:
            for task_id in daily_tasks.keys():
                active_task = await self.task_system.get_task_by_id(task_id)
            if active_task:
                message = (
                    f"你已有一个未完成的日常任务：\n"
                    f"【{active_task['name']}】\n"
                    f"描述：{active_task['description']}\n"
                    f"奖励：{active_task['reward']}\n"
                    f"请完成当前任务后再领取新的任务"
                )
        else:
            # 没有活跃任务，分配新任务
            task = await self.task_system.assign_daily_task(user_id)
            if task:
                message = (
                    f"已为你分配日常任务：\n"
                    f"【{task['name']}】\n"
                    f"描述：{task['description']}\n"
                    f"奖励：{task['reward']}"
                )
            else:
                message = "获取任务失败，请稍后再试"
        yield event.plain_result(message)

    @filter.command("我的任务", alias="查看任务")
    async def check_my_tasks(self, event: AstrMessageEvent):
        """查看当前任务进度"""
        user_id = str(event.get_sender_id())
        quest_data = await self.user_system.get_quest_data(user_id)
        daily_tasks = quest_data.get("daily", {})

        if not daily_tasks:
            yield event.plain_result("你当前没有任务，可使用【领取任务】获取日常任务")
            return

        message = "你的当前任务：\n"
        for task_id, progress in daily_tasks.items():
            task = await self.task_system.get_task_by_id(task_id)
            if task:
                message += (
                    f"【{task['name']}】{progress['current']}/{progress['target']}\n"
                    f"  描述：{task['description']}\n"
                )
        yield event.plain_result(message)

    # 添加任务进度通知处理（在对应的动作处理函数中）
    @filter.command("打工")
    async def work_action(self, event: AstrMessageEvent):
        """处理打工动作并检查任务进度"""
        user_id = str(event.get_sender_id())
        # 检查任务进度
        task_result = await self.task_system.check_task_completion(user_id, "打工")
        if task_result["progress_msg"]:
            yield event.plain_result(task_result["progress_msg"])
        if task_result["completed"]:
            yield event.plain_result(task_result["message"])
            # 获取并发送奖励消息
            success, reward_msg = await self.task_system.grant_reward(
                user_id, task_result["task_id"]
            )
            if success:
                yield event.plain_result(reward_msg)
