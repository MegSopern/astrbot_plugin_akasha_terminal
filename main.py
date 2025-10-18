import re
from pathlib import Path

import aiohttp
import astrbot.api.message_components as Comp
from aiocqhttp import CQHttp
from astrbot.api import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from .core.battle import Battle
from .core.lottery import Lottery
from .core.shop import Shop
from .core.task import Task
from .core.user import User
from .utils.utils import get_cmd_info, logo_AATP


@register(
    "astrbot_plugin_akasha_terminal",
    "MegSopern & Xinhaihai & Xwbndmqaq",
    "一个功能丰富的聚合类娱乐插件，提供完整的游戏系统与JSON存储支持，包含商店、抽卡、情侣、战斗、社交、任务等多样化玩法",
    "2.1.0",
)
class AkashaTerminal(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        # 读取抽卡冷却配置
        try:
            self.admins_id: list[str] = context.get_config().get("admins_id", [])
        except Exception as e:
            logger.error(f"读取冷却配置失败: {str(e)}")
        self.initialize_subsystems()

    # 初始化各个子系统
    def initialize_subsystems(self):
        try:
            # 用户系统
            self.user = User()
            # 任务系统
            self.task = Task()
            # 商店系统
            self.shop = Shop()
            # 抽奖系统
            self.lottery = Lottery(self.config)
            # 战斗系统
            self.battle = Battle()
            logger.info("Akasha Terminal插件初始化完成")
        except Exception as e:
            logger.error(f"Akasha Terminal插件初始化失败:{str(e)}")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        logo_AATP()

    @filter.command("我的信息", alias={"个人信息", "查看信息"})
    async def get_user_info(self, event: AiocqhttpMessageEvent):
        """查看个人信息，使用方法: /我的信息 @用户/qq号"""
        parts = await get_cmd_info(event)
        message = await self.user.format_user_info(event, parts)
        yield event.plain_result(message)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("增加金钱", alias=["添加金钱", "加钱"])
    async def add_user_money(self, event: AiocqhttpMessageEvent):
        """增加用户金钱，使用方法: /增加金钱 金额"""
        parts = await get_cmd_info(event)
        success, message = await self.user.add_money(event, parts)
        yield event.plain_result(message)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("用户列表")
    async def list_all_users(self, event: AiocqhttpMessageEvent):
        """获取所有用户列表"""
        message = await self.user.get_all_users_info()
        yield event.plain_result(message)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""

    ########## 任务系统
    @filter.command("领取任务", alias="获取任务")
    async def get_daily_task(self, event: AiocqhttpMessageEvent):
        """领取日常任务"""
        user_id = str(event.get_sender_id())
        message = await self.task.get_user_daily_task(user_id)
        yield event.plain_result(message)

    @filter.command("我的任务", alias="查看任务")
    async def check_my_tasks(self, event: AiocqhttpMessageEvent):
        """查看当前任务进度"""
        user_id: str = event.get_sender_id()
        message = await self.task.format_user_tasks(user_id)
        yield event.plain_result(message)

    @filter.command("打工")
    async def work_action(self, event: AiocqhttpMessageEvent):
        """处理打工动作并检查任务进度"""
        user_id: str = event.get_sender_id()
        messages = await self.task.handle_work_action(user_id)
        for msg in messages:
            yield event.plain_result(msg)

    ########## 商店、背包系统
    @filter.command("商店", alias={"虚空商店", "商城", "虚空商城"})
    async def show_shop(self, event: AiocqhttpMessageEvent):
        """显示商店物品列表"""
        message = await self.shop.format_shop_items()
        yield event.plain_result(message)

    @filter.command("购买道具", alias={"买道具", "购买物品", "买物品"})
    async def buy_prop(self, event: AiocqhttpMessageEvent):
        """/购买道具 物品名称 数量"""
        # 提取命令后的参数部分
        parts = await get_cmd_info(event)
        success, message = await self.shop.handle_buy_command(event, parts)
        yield event.plain_result(message)

    @filter.command("背包", alias="查看背包")
    async def show_backpack(self, event: AiocqhttpMessageEvent):
        """查看我的背包"""
        message = await self.shop.format_backpack(event)
        yield event.plain_result(message)

    @filter.command("使用道具", alias={"用道具", "使用物品", "用物品"})
    async def use_item(self, event: AiocqhttpMessageEvent):
        """使用道具，使用方法: /使用道具 物品名称"""
        parts = await get_cmd_info(event)
        success, message = await self.shop.handle_use_command(event, parts)
        yield event.plain_result(message)

    @filter.command("赠送道具", alias={"送道具", "赠送物品", "送物品"})
    async def gift_item(self, event: AiocqhttpMessageEvent):
        """赠送道具，使用方法: /赠送道具 物品名称 @用户"""
        parts = await get_cmd_info(event)
        success, message = await self.shop.handle_gift_command(event, parts)
        yield event.plain_result(message)

    @filter.command("抽武器", alias={"单抽武器", "单抽"})
    async def draw_weapon(self, event: AiocqhttpMessageEvent):
        """单抽武器"""
        message, image_path = await self.lottery.weapon_draw(event, count=1)
        if image_path and Path(image_path).exists():
            message = [
                Comp.Plain(message),
                Comp.Image.fromFileSystem(image_path),
            ]
            yield event.chain_result(message)
        else:
            yield event.plain_result(message)

    @filter.command("十连抽武器", alias={"十连武器", "武器十连", "十连抽", "十连"})
    async def draw_ten_weapons(self, event: AiocqhttpMessageEvent):
        """十连抽武器"""
        message, weapon_image_paths = await self.lottery.weapon_draw(event, count=10)
        components = [Comp.Plain(message)]
        # 只在有有效的图片路径列表时才添加图片
        if weapon_image_paths:
            # 添加所有武器图片
            for path in weapon_image_paths:
                path = str(path)
                if path and Path(path).exists():
                    components.append(Comp.Image.fromFileSystem(path))
        yield event.chain_result(components)

    @filter.command("签到", alias={"每日签到"})
    async def sign_in(self, event: AiocqhttpMessageEvent):
        """进行每日签到"""
        message = await self.lottery.daily_sign_in(event)
        yield event.plain_result(message)

    @filter.command("我的武器", alias={"武器库", "查看武器"})
    async def my_weapons(self, event: AiocqhttpMessageEvent):
        """展示背包武器的统计信息"""
        message = await self.lottery.show_my_weapons(event)
        yield event.plain_result(message)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("开挂", alias={"增加纠缠之缘", "添加纠缠之缘"})
    async def cheat(self, event: AiocqhttpMessageEvent):
        """增添纠缠之缘，使用方法: /开挂 数量"""
        parts = await get_cmd_info(event)
        success, message = await self.lottery.handle_cheat_command(event, parts)
        yield event.plain_result(message)

    @filter.command("刷新商城", alias={"刷新商店", "刷新虚空商店", "刷新虚空商城"})
    @filter.permission_type(filter.PermissionType.ADMIN)
    async def refresh_shop(self, event: AiocqhttpMessageEvent):
        """刷新商城物品"""
        message = await self.shop.refresh_shop_manually()
        yield event.plain_result(message)

    @filter.command("道具详情", alias={"道具详细", "物品详情", "物品详细"})
    async def item_detail(self, event: AiocqhttpMessageEvent):
        """查看道具详情，使用方法: /道具详情 物品名称"""
        parts = await get_cmd_info(event)
        message = await self.shop.handle_item_detail_command(parts)
        yield event.plain_result(message)

    @filter.command(
        "决斗", alias={"发起决斗", "开始决斗", "和我决斗", "与我决斗", "御前决斗"}
    )
    async def duel(self, event: AiocqhttpMessageEvent):
        """发起决斗，使用方法: /决斗 @用户/qq号"""
        parts = await get_cmd_info(event)
        await self.battle.handle_duel_command(event, parts, self.admins_id)

    @filter.command("设置战斗力系数", alias={"设置战斗力意义系数"})
    async def set_magnification(self, event: AiocqhttpMessageEvent):
        """设置战斗力系数值，使用方法: /设置战斗力系数 数值"""
        parts = await get_cmd_info(event)
        await self.battle.handle_set_magnification_command(event, parts, self.admins_id)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("测试", alias={"测试用例"})
    async def abcd(self, event: AiocqhttpMessageEvent):
        """测试用例方法"""
        await self.shop.ceshi_command(event)
