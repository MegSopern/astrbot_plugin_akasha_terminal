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
