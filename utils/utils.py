import asyncio
import fcntl
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

from astrbot.api import logger
from astrbot.core.message.components import At, BaseMessageComponent, Image, Reply
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)


def logo_AATP():
    """横向拼接 AATP，自动对齐行高"""
    A1 = r"""
 █████╗ 
██╔══██╗ 
███████║ 
██╔══██║ 
██║   ██║ 
╚═╝   ╚═╝ """.strip("\n")

    A2 = r"""
  █████╗  
██╔══██╗ 
███████║ 
██╔══██║ 
 ██║   ██║ 
 ╚═╝   ╚═╝ """.strip("\n")

    T = r"""
  ████████╗ 
╚══██╔══╝ 
    ██║ 
    ██║ 
    ██║ 
    ╚═╝ """.strip("\n")

    P = r"""
██████╗
 ██╔══██╗
   ██████╔╝
   ██╔═══╝
   ██║
   ╚═╝""".strip("\n")

    # 统一行数（取最多行的那段）
    blocks = [A1, A2, T, P]
    lines = [b.splitlines() for b in blocks]
    max_rows = max(len(ls) for ls in lines)

    # 短段用空行补齐，防止 zip 截断
    for ls in lines:
        ls += [""] * (max_rows - len(ls))

    # 彩色序号
    colors = ["\033[95m", "\033[96m", "\033[94m", "\033[92m"]
    reset = "\033[0m"

    # 按行横向拼接
    for row in zip(*lines):
        print("".join(f"{c}{cell:<10}{reset}" for c, cell in zip(colors, row)))

    print("\n\033[95m欢迎使用虚空插件！\033[0m")


# 初始化用户数据的工具函数
async def create_user_data(user_id: str) -> bool:
    """创建user系统初始数据"""
    try:
        # 创建默认用户数据
        user_data_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "plugin_data"
            / "astrbot_plugin_akasha_terminal"
            / "user_data"
        )
        default_user_data = {
            "user": {
                "id": user_id,
                "nickname": "",
                "level": 1,
                "experience": 0,
                "created_at": time.time(),
            },
            "battle": {
                "experience": 0,
                "level": 0,
                "levelname": "无等级",
                "privilege": 0,
            },
            "home": {
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
            },
            "quest": {
                "daily": {},
                "weekly": {},
                "special": {},
                "quest_points": 0,
                "last_daily_reset": "",
                "last_weekly_reset": "",
            },
        }

        # 确保目录存在
        user_data_path.mkdir(parents=True, exist_ok=True)
        # 写入用户数据
        await write_json(user_data_path / f"{user_id}.json", default_user_data)
        return True
    except Exception as e:
        logger.error(f"创建用户数据失败: {str(e)}")
        return False


def read_json_sync(file_path: Path) -> Dict[str, Any]:
    """同步原子读取JSON文件[读取的文件编码为'utf-8-sig']"""
    # 原子读：加共享锁 -> 读 -> 解锁
    if not file_path.exists():
        return {}

    def read_json_atomic() -> Dict[str, Any]:
        fd = os.open(file_path, os.O_RDONLY | os.O_CLOEXEC)
        try:
            # 加共享锁（非阻塞）
            fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            with os.fdopen(fd, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                # 读取完成后，释放锁
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            pass
        return data

    try:
        return read_json_atomic()
    except Exception as e:
        logger.error(f"读取文件 {file_path} 失败: {str(e)}")
        return {}


def write_json_sync(file_path: Path, data: Dict[str, Any]) -> bool:
    """同步原子写入JSON文件[读取的文件编码为'utf-8-sig']"""

    def write_json_atomic() -> None:
        # 生成唯一的临时文件
        with tempfile.NamedTemporaryFile(
            "w",
            dir=file_path.parent,
            delete=False,
            suffix=".json",
            encoding="utf-8-sig",
        ) as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            temp_name = tmp_file.name
        # 原子替换
        os.replace(temp_name, file_path)

    try:
        # 直接调用原子写入方法
        write_json_atomic()
        return True
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {str(e)}")
        return False


def get_at_ids(event: AiocqhttpMessageEvent) -> list[str]:
    """获取QQ被at用户的id列表"""
    return [
        str(seg.qq)
        for seg in event.get_messages()
        if (isinstance(seg, At) and str(seg.qq) != event.get_self_id())
    ]


async def read_json(file_path: Path) -> Dict[str, Any]:
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


async def write_json(file_path: Path, data: Dict[str, Any]) -> bool:
    """异步原子写入JSON文件"""
    loop = asyncio.get_running_loop()

    def write_json_atomic() -> None:
        # 生成唯一的临时文件
        with tempfile.NamedTemporaryFile(
            "w",
            dir=file_path.parent,
            delete=False,
            suffix=".json",
            encoding="utf-8",
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


async def get_referenced_msg_id(event: AiocqhttpMessageEvent) -> str | None:
    """获取被引用消息者的id"""
    for seg in event.get_messages():
        if isinstance(seg, Reply):
            return str(seg.sender_id)


async def get_nickname(event: AiocqhttpMessageEvent, user_id) -> str:
    """获取群用户的群昵称或QQ名"""
    client = event.bot
    group_id = event.get_group_id()
    all_info = await client.get_group_member_info(
        group_id=int(group_id), user_id=int(user_id)
    )
    return all_info.get("card") or all_info.get("nickname")


def seconds_to_duration(seconds) -> str:
    """将秒数转换为友好的时长字符串，如将秒数转换为"1天2小时3分4秒"""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "输入必须是非负的数字"

    # 定义时间单位及其对应的秒数
    units = [
        ("天", 86400),
        ("小时", 3600),
        ("分", 60),
        ("秒", 1),
    ]
    parts = []
    remaining = int(round(seconds))  # 四舍五入到整数

    for unit_name, unit_seconds in units:
        if remaining >= unit_seconds:
            count = remaining // unit_seconds
            parts.append(f"{count}{unit_name}")
            remaining %= unit_seconds

        if remaining == 0:
            break

    # 处理0秒的情况
    return "0秒" if not parts else "".join(parts)
