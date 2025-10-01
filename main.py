import random
import re

import aiohttp  # noqa: F401
import astrbot.api.message_components as Comp
from aiocqhttp import CQHttp  # noqa: F401
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .core.lottery import Lottery
from .core.shop import Shop
from .core.task import Task
from .core.user import User
from .utils.utils import get_nickname, logo_AATP


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
            # 商店系统
            self.shop_system = Shop()
            # 抽奖系统
            self.lottery_system = Lottery()
            logger.info("Akasha Terminal插件初始化完成")
        except Exception as e:
            logger.error(f"Akasha Terminal插件初始化失败:{str(e)}")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        logo_AATP()

    @filter.command("我的信息", alias={"个人信息", "查看信息"})
    async def get_user_info(self, event: AstrMessageEvent):
        """查看个人信息"""
        try:
            # 获取用户ID，默认为发送者ID
            user_id = str(event.get_sender_id())
            # 获取群用户昵称
            nickname = await get_nickname(event, user_id)
            cmd_prefix = event.message_str.split()[0]
            input_str = event.message_str.replace(cmd_prefix, "", 1).strip()
            message = await self.user_system.format_user_info(
                user_id, nickname, input_str
            )
            yield event.plain_result(message)
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            yield event.plain_result("获取用户信息失败，请稍后再试~")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("增加金钱", alias="添加金钱")
    async def add_user_money(
        self, event: AstrMessageEvent, input_id: int | str | None = None
    ):
        """增加用户金钱，使用方法: /增加金钱 金额"""
        user_id = event.get_sender_id()
        cmd_prefix = event.message_str.split()[0]
        input_str = event.message_str.replace(cmd_prefix, "", 1).strip()
        success, message = await self.user_system.add_money(user_id, input_str)
        yield event.plain_result(message)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("用户列表")
    async def list_all_users(self, event: AstrMessageEvent):
        """获取所有用户列表"""
        message = await self.user_system.get_all_users_info()
        yield event.plain_result(message)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    ########## 任务系统
    @filter.command("领取任务", alias="获取任务")
    async def get_daily_task(self, event: AstrMessageEvent):
        """领取日常任务"""
        user_id = str(event.get_sender_id())
        message = await self.task_system.get_user_daily_task(user_id)
        yield event.plain_result(message)

    @filter.command("我的任务", alias="查看任务")
    async def check_my_tasks(self, event: AstrMessageEvent):
        """查看当前任务进度"""
        user_id: str = event.get_sender_id()
        message = await self.task_system.format_user_tasks(user_id)
        yield event.plain_result(message)

    @filter.command("打工")
    async def work_action(self, event: AstrMessageEvent):
        """处理打工动作并检查任务进度"""
        user_id: str = event.get_sender_id()
        messages = await self.task_system.handle_work_action(user_id)
        for msg in messages:
            yield event.plain_result(msg)

    ########## 商店、背包系统
    @filter.command("商店", alias={"虚空商店", "商城", "虚空商城"})
    async def show_shop(self, event: AstrMessageEvent):
        """显示商店物品列表"""
        try:
            message = await self.shop_system.format_shop_items()
            yield event.plain_result(message)
        except Exception as e:
            logger.error(f"显示商店失败: {str(e)}")
            yield event.plain_result("显示商店失败，请稍后重试")

    @filter.command("购买道具", alias={"买道具", "购买物品", "买物品"})
    async def buy_prop(self, event: AstrMessageEvent):
        """/购买道具 物品名称 数量"""
        user_id = event.get_sender_id()
        # 提取命令后的参数部分
        cmd_prefix = event.message_str.split()[0]
        input_str = event.message_str.replace(cmd_prefix, "", 1).strip()
        success, message = await self.shop_system.handle_buy_command(user_id, input_str)
        yield event.plain_result(message)

    @filter.command("使用道具", alias={"用道具", "使用物品", "用物品"})
    async def use_item(self, event: AstrMessageEvent):
        """使用道具，使用方法: /使用道具 物品名称"""
        user_id = str(event.get_sender_id())
        cmd_prefix = event.message_str.split()[0]
        input_str = event.message_str.replace(cmd_prefix, "", 1).strip()
        success, message = await self.shop_system.handle_use_command(user_id, input_str)
        yield event.plain_result(message)

    @filter.command("背包", alias="我的背包")
    async def show_backpack(self, event: AstrMessageEvent):
        """查看我的背包"""
        try:
            user_id = str(event.get_sender_id())
            message = await self.shop_system.format_backpack(user_id)
            yield event.plain_result(message)
        except Exception as e:
            logger.error(f"查看背包失败: {str(e)}")
            yield event.plain_result("查看背包失败，请稍后重试~")

    @filter.command("赠送道具", alias={"送道具", "赠送物品", "送物品"})
    async def gift_item(self, event: AstrMessageEvent):
        """赠送道具，使用方法: /赠送道具 物品名称 @用户"""
        from_user_id = str(event.get_sender_id())
        cmd_prefix = event.message_str.split()[0]
        input_str = event.message_str.replace(cmd_prefix, "", 1).strip()
        success, message = await self.shop_system.handle_gift_command(
            from_user_id, input_str
        )
        yield event.plain_result(message)

    @filter.command("抽武器", alias={"单抽武器", "单抽"})
    async def draw_weapon(self, event: AstrMessageEvent):
        """单抽武器"""
        try:
            user_id = str(event.get_sender_id())
            message = await self.lottery_system.weapon_draw(user_id, count=1)
            yield event.plain_result(message)
        except Exception as e:
            logger.error(f"抽武器失败: {str(e)}")
            yield event.plain_result("抽武器失败，请稍后再试~")
            return

    @filter.command("十连抽武器", alias={"十连武器", "十连"})
    async def draw_ten_weapons(self, event: AstrMessageEvent):
        """十连抽武器"""
        try:
            user_id = str(event.get_sender_id())
            message = await self.lottery_system.weapon_draw(user_id, count=10)
            yield event.plain_result(message)
        except Exception as e:
            logger.error(f"十连抽武器失败: {str(e)}")
            yield event.plain_result("十连抽武器失败，请稍后再试~")

    @filter.command("签到", alias={"每日签到"})
    async def sign_in(self, event: AstrMessageEvent):
        """进行每日签到"""
        try:
            user_id = str(event.get_sender_id())
            message = await self.lottery_system.daily_sign_in(user_id)
            yield event.plain_result(message)
        except Exception as e:
            logger.error(f"每日签到失败: {str(e)}")
            yield event.plain_result("每日签到失败，请稍后再试~")
