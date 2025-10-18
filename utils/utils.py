import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

from astrbot.api import logger
from astrbot.core.message.components import At, Reply
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

# 替换fcntl为跨平台的filelock库
from filelock import FileLock


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


def read_json_sync(file_path: Path, encoding_config: str = "utf-8") -> Dict[str, Any]:
    """同步原子读取JSON文件"""
    if not file_path.exists():
        return {}

    def read_json_atomic() -> Dict[str, Any]:
        # 使用文件锁的兼容实现，锁文件为原文件路径加.lock后缀
        lock = FileLock(f"{file_path}.lock", timeout=5)
        with lock:
            with open(file_path, "r", encoding=encoding_config) as f:
                data = json.load(f)
        return data

    try:
        return read_json_atomic()
    except Exception as e:
        logger.error(f"读取文件 {file_path} 失败: {str(e)}")
        return {}


def write_json_sync(
    file_path: Path, data: Dict[str, Any], encoding_config: str = "utf-8"
) -> bool:
    """同步原子写入JSON文件"""

    def write_json_atomic() -> None:
        # 生成唯一的临时文件
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

        # 使用文件锁保证原子替换的安全性
        lock = FileLock(f"{file_path}.lock", timeout=5)
        with lock:
            # 原子替换
            os.replace(temp_name, file_path)

    try:
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
    return "".join(parts) if parts else "0秒"


# 初始化用户数据的工具函数
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


async def get_user_data_and_backpack(
    user_id: str, only_data_or_backpack: str | None = None
) -> dict | tuple[dict, dict]:
    """获取用户数据和背包数据（不存在则创建）"""
    base_dir = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "plugin_data"
        / "astrbot_plugin_akasha_terminal"
    )
    user_data_path = base_dir / "user_data"
    backpack_path = base_dir / "backpack"
    user_data = None
    user_backpack = None
    if only_data_or_backpack in (None, "user_data"):
        user_data_file = user_data_path / f"{user_id}.json"
        if not user_data_file.exists():
            await create_user_data(user_id, user_data_path)
        user_data = await read_json(user_data_file)

    if only_data_or_backpack in (None, "user_backpack"):
        user_backpack = await read_json(backpack_path / f"{user_id}.json") or {}
        # 初始化武器背包结构
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


async def read_json(file_path: Path, encoding_config: str = "utf-8") -> Dict[str, Any]:
    """异步原子读取JSON文件"""
    if not file_path.exists():
        return {}

    loop = asyncio.get_running_loop()

    def read_json_atomic() -> Dict[str, Any]:
        # 使用文件锁的兼容实现
        lock = FileLock(f"{file_path}.lock", timeout=5)
        with lock:
            with open(file_path, "r", encoding=encoding_config) as f:
                return json.load(f)

    try:
        return await loop.run_in_executor(None, read_json_atomic)
    except Exception as e:
        logger.error(f"读取文件 {file_path} 失败: {str(e)}")
        return {}


async def write_json(
    file_path: Path, data: Dict[str, Any], encoding_config: str = "utf-8"
) -> bool:
    """异步原子写入JSON文件"""
    loop = asyncio.get_running_loop()

    def write_json_atomic() -> None:
        # 生成唯一的临时文件
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

        # 使用文件锁保证原子替换的安全性
        lock = FileLock(f"{file_path}.lock", timeout=5)
        with lock:
            # 原子替换
            os.replace(temp_name, file_path)

    try:
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


async def get_cmd_info(event: AiocqhttpMessageEvent) -> list[str]:
    """提取命令及获取去除前缀后的内容"""
    cmd_prefix = event.message_str.split()[0]
    input_str = event.message_str.replace(cmd_prefix, "", 1).strip()
    return input_str.strip().split()
