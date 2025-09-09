import asyncio
import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from astrbot.api import logger


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


async def read_json(self, file_path: Path) -> Dict[str, Any]:
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


async def write_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
    """异步原子写入JSON文件"""
    loop = asyncio.get_running_loop()

    def write_json_atomic() -> None:
        # 生成唯一的临时文件
        with tempfile.NamedTemporaryFile(
            "w", dir=file_path.parent, delete=False, suffix=".json"
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
