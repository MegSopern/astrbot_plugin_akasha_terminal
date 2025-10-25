import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

if sys.platform.startswith("win"):
    import msvcrt
else:
    import fcntl

from astrbot.api import logger
from astrbot.api.star import StarTools
from astrbot.core.message.components import At, Reply
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

# 文件路径
PLUGIN_DATA_DIR = Path(StarTools.get_data_dir("astrbot_plugin_akasha_terminal"))
PLUGIN_DIR = Path(__file__).resolve().parent.parent


def logo_AATP():
    """横向拼接 AATP，自动对齐行高"""
    # （原函数内容不变）
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

    blocks = [A1, A2, T, P]
    lines = [b.splitlines() for b in blocks]
    max_rows = max(len(ls) for ls in lines)

    for ls in lines:
        ls += [""] * (max_rows - len(ls))

    colors = ["\033[95m", "\033[96m", "\033[94m", "\033[92m"]
    reset = "\033[0m"

    for row in zip(*lines):
        print("".join(f"{c}{cell:<10}{reset}" for c, cell in zip(colors, row)))

    print("\n\033[95m欢迎使用虚空插件！\033[0m")


def _lock_file(fileno, exclusive=True):
    """跨平台文件锁定"""
    if sys.platform.startswith("win"):
        # Windows锁定：LK_LOCK（排他锁）/ LK_RLCK（共享锁）
        lock_type = msvcrt.LK_LOCK if exclusive else msvcrt.LK_RLCK
        # 锁定整个文件（通过锁定1字节实现，Windows锁定是范围锁定）
        msvcrt.locking(fileno, lock_type, 1)
    else:
        # Unix锁定：LOCK_EX（排他锁）/ LOCK_SH（共享锁）
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(fileno, lock_type)


def _unlock_file(fileno):
    """跨平台文件解锁"""
    if sys.platform.startswith("win"):
        msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1)
    else:
        # Unix下flock在文件关闭时自动解锁，这里显式解锁更安全
        fcntl.flock(fileno, fcntl.LOCK_UN)


def read_json_sync(file_path: Path, encoding_config: str = "utf-8") -> Dict[str, Any]:
    """同步原子读取JSON文件（无.lock文件）"""
    if not file_path.exists():
        return {}

    def read_json_atomic() -> Dict[str, Any]:
        with open(file_path, "r", encoding=encoding_config) as f:
            try:
                # 加共享锁（允许多个读操作同时进行）
                _lock_file(f.fileno(), exclusive=False)
                return json.load(f)
            finally:
                # 确保解锁
                _unlock_file(f.fileno())

    try:
        return read_json_atomic()
    except Exception as e:
        logger.error(f"读取文件 {file_path} 失败: {str(e)}")
        return {}


def write_json_sync(
    file_path: Path, data: Dict[str, Any], encoding_config: str = "utf-8"
) -> bool:
    """同步原子写入JSON文件（无.lock文件）"""

    def write_json_atomic() -> None:
        # 生成临时文件
        with tempfile.NamedTemporaryFile(
            "w",
            dir=file_path.parent,
            delete=False,
            suffix=".json",
            encoding=encoding_config,
        ) as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            temp_name = tmp_file.name

        # 对目标文件加排他锁（防止写入时被读取）
        if file_path.exists():
            with open(file_path, "r+") as f:
                _lock_file(f.fileno(), exclusive=True)

        # 原子替换临时文件到目标文件
        os.replace(temp_name, file_path)

    try:
        write_json_atomic()
        return True
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {str(e)}")
        return False


async def read_json(file_path: Path, encoding_config: str = "utf-8") -> Dict[str, Any]:
    """异步原子读取JSON文件（无.lock文件）"""
    if not file_path.exists():
        return {}

    loop = asyncio.get_running_loop()
    # 复用同步读取逻辑（通过线程池执行）
    return await loop.run_in_executor(None, read_json_sync, file_path, encoding_config)


async def write_json(
    file_path: Path, data: Dict[str, Any], encoding_config: str = "utf-8"
) -> bool:
    """异步原子写入JSON文件（无.lock文件）"""
    loop = asyncio.get_running_loop()
    # 复用同步写入逻辑（通过线程池执行）
    return await loop.run_in_executor(
        None, write_json_sync, file_path, data, encoding_config
    )


# 以下函数内容不变
def get_at_ids(event: AiocqhttpMessageEvent) -> list[str]:
    """获取QQ被at用户的id列表"""
    return [
        str(seg.qq)
        for seg in event.get_messages()
        if (isinstance(seg, At) and str(seg.qq) != event.get_self_id())  # 排除自己
    ]


def seconds_to_duration(seconds) -> str:
    """将秒数转换为友好的时长字符串，如将秒数转换为"1天2小时3分4秒"""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "输入必须是非负的数字"

    units = [
        ("天", 86400),
        ("小时", 3600),
        ("分", 60),
        ("秒", 1),
    ]
    parts = []
    remaining = int(round(seconds))

    for unit_name, unit_seconds in units:
        if remaining >= unit_seconds:
            count = remaining // unit_seconds
            parts.append(f"{count}{unit_name}")
            remaining %= unit_seconds

        if remaining == 0:
            break

    return "".join(parts) if parts else "0秒"


async def create_user_data(user_id: str, user_data_path: Path) -> bool:
    """创建user系统初始数据"""
    try:
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
            "task": {
                "daily": {},
                "weekly": {},
                "special": {},
                "task_points": 0,
                "last_daily_refresh": "",
                "last_weekly_refresh": "",
            },
        }

        user_data_path.mkdir(parents=True, exist_ok=True)
        await write_json(user_data_path / f"{user_id}.json", default_user_data)
        return True
    except Exception as e:
        logger.error(f"创建用户数据失败: {str(e)}")
        return False


async def get_user_data_and_backpack(
    user_id: str, only_data_or_backpack: str | None = None
) -> dict | tuple[dict, dict]:
    """获取用户数据和背包数据（不存在则创建）\n
    如果only_data_or_backpack为"user_data"则仅返回用户数据\n
    如果only_data_or_backpack为"user_backpack"则仅返回背包数据\n
    默认返回(用户数据, 背包数据)元组"""
    user_data_path = PLUGIN_DATA_DIR / "user_data"
    backpack_path = PLUGIN_DATA_DIR / "user_backpack"
    user_data = None
    user_backpack = None
    if only_data_or_backpack in (None, "user_data"):
        user_data_file = user_data_path / f"{user_id}.json"
        if not user_data_file.exists():
            await create_user_data(user_id, user_data_path)
        user_data = await read_json(user_data_file)

    if only_data_or_backpack in (None, "user_backpack"):
        user_backpack = await read_json(backpack_path / f"{user_id}.json") or {}
        if "weapon" not in user_backpack:
            user_backpack["weapon"] = {
                "纠缠之缘": 0,
                "总抽卡次数": 0,
                "武器计数": {},
                "武器详细": {
                    "三星武器": {"数量": 0, "详细信息": []},
                    "四星武器": {"数量": 0, "详细信息": []},
                    "五星武器": {"数量": 0, "详细信息": []},
                },
                "未出五星计数": 0,
                "未出四星计数": 0,
            }
    if only_data_or_backpack == "user_data":
        return user_data
    elif only_data_or_backpack == "user_backpack":
        return user_backpack
    return user_data, user_backpack


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


async def get_cmd_info(event: AiocqhttpMessageEvent) -> list[str]:
    """提取命令及获取去除前缀后的内容"""
    cmd_prefix = event.message_str.split()[0]
    input_str = event.message_str.replace(cmd_prefix, "", 1).strip()
    return input_str.strip().split()
