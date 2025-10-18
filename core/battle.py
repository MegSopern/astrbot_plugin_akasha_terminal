import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.star import StarTools
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

# 导入工具函数
from ..utils.utils import (
    get_at_ids,
    get_nickname,
    get_user_data_and_backpack,
    read_json,
    read_json_sync,
    write_json,
)

# 挑战bot时的反馈语录列表
challenge_bot_text_list = (
    [
        "你想挑战我？大胆！",
        "你什么意思？想挑战神明？举办了！",
        "哈哈哈，来吧，接受我的审判！",
        "就凭你？也配站在我面前叫嚣？",
        "神明的威严岂容尔等放肆！",
        "呵，不知天高地厚的家伙，也敢捋虎须？",
        "挑战我？先掂量掂量自己有几分斤两！",
        "别浪费时间废话，拿出你的全部本事来！",
        "我会让你明白，挑战神明是何等愚蠢的决定！",
        "收起你那可笑的勇气吧，在我面前不值一提！",
        "你这点微末伎俩，也敢称作挑战？简直是天大的笑话！",
        "吾之领域，岂容异类撒野？准备好迎接毁灭吧！",
        "居然敢直视神明的双眼？这份狂妄，会让你付出惨痛代价！",
        "别再做无谓的挣扎了，你的结局从挑战我的那一刻就已注定！",
        "我见过无数狂妄之徒，你不过是其中最不起眼的一个！",
        "拿出你的底牌吧，否则你连让我认真的资格都没有！",
        "神明的怒火，足以焚烧整个天地，你确定要以身试险？",
        "呵，蚍蜉撼树，也不过如此！",
        "今日便折断你的傲骨，让你知晓何为尊卑有序！",
        "挑战我？你怕是还没搞清楚，我们之间的差距如同云泥之别！",
    ],
)

# 自我挑战时的反馈语录列表
challenge_self_text_list = [
    "...好吧，成全你，和自己决斗是吧？",
    "呵，和自己较劲？真是闻所未闻，那就让你尝尝自食其果的滋味",
    "既然你偏要和自己过不去，我不介意当个看客，看你如何困在执念里",
    "和自己决斗？这等荒唐事也做得出来，看来你是真没别的本事了",
    "行啊，你想跟自己斗便斗吧，反正最后倒下的，只会是你那点可怜的自尊",
    "连对手都找不对，偏要和自己死磕？也好，省得我动手清理你这糊涂虫",
    "成全你？可以。但别指望我会手下留情，哪怕你对着的是自己的影子",
    "和自己决斗？说到底不过是不敢面对我的借口罢了，我可没功夫陪你演戏",
    "既然你执意要钻牛角尖，那就尽管去和自己纠缠，我会在终点等着看你的狼狈",
    "呵，自己跟自己斗？真是蠢得可爱，那就让这场闹剧快点收场吧",
    "跟自己决斗？说白了就是自我消耗，等你耗尽力气，连站着的力气都没了",
    "非要和自己拧着来？也好，等你撞得头破血流，就知道这有多可笑了",
    "连对手是谁都分不清，偏要和自己较劲？这股傻劲，倒也算独一份",
    "行，我看着。看你怎么跟自己的影子斗到筋疲力尽，最后连认输都找不到对象",
    "和自己决斗？不过是给自己找罪受罢了，等你疼了，自然就醒了",
    "既然你非要点燃和自己的战火，那我就看着你如何被自己的火焰灼伤",
    "连真正的对手都不敢面对，只会和自己周旋？这种懦弱，真是令人不齿",
    "跟自己斗？斗到最后，怕是连自己是谁都忘了，何必呢",
    "你想和自己分个胜负？呵，赢了又如何，输了又如何，还不是困在原地打转",
    "行，成全你这场独角戏。只是别指望有人为你鼓掌，毕竟和自己打架，实在太难看了",
]


class Battle:
    def __init__(self):
        # 冷却时间存储
        self.duel_cd: Dict[str, float] = {}

        # 数据路径
        PLUGIN_DATA_DIR = Path(StarTools.get_data_dir("astrbot_plugin_akasha_terminal"))
        self.user_data_path = PLUGIN_DATA_DIR / "user_data"
        self.backpack_path = PLUGIN_DATA_DIR / "backpack"
        self.config_file = (
            PLUGIN_DATA_DIR.parent.parent
            / "config"
            / "astrbot_plugin_akasha_terminal_config.json"
        )

        # 配置
        config_data = read_json_sync(self.config_file, "utf-8-sig")
        self.duel_cooldown: int = config_data["battle_system"].get("duel_cooldown", 10)
        self.magnification: float = config_data["battle_system"].get(
            "combat_effectiveness_coefficient", 2
        )
        # 确保数据目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def is_cooling(self, user_id: str) -> tuple[bool, float]:
        """检查用户是否在冷却中"""
        if user_id in self.duel_cd:
            remaining = self.duel_cd[user_id] - time.time()
            if remaining > 0:
                return True, remaining
            del self.duel_cd[user_id]
        return False, 0

    async def set_cooling(self, user_id: str):
        """设置冷却"""
        self.duel_cd[user_id] = time.time() + self.duel_cooldown

    async def load_weapon_count(self, user_id: str) -> tuple[int, int, int]:
        """加载用户武器数量"""
        try:
            backpack = await get_user_data_and_backpack(user_id, "user_backpack")
            weapon_data = backpack.get("weapons", {})
            three_star = weapon_data["武器详细"]["三星武器"]["数量"]
            four_star = weapon_data["武器详细"]["四星武器"]["数量"]
            five_star = weapon_data["武器详细"]["五星武器"]["数量"]
            return three_star, four_star, five_star
        except Exception as e:
            logger.error(f"解析用户武器数据失败 {user_id}: {e}")
            return 0, 0, 0

    async def handle_duel_command(
        self, event: AiocqhttpMessageEvent, input_str: str, admins_id: list[str]
    ) -> Optional[str]:
        """处理决斗命令"""
        try:
            challenger_id = str(event.get_sender_id())
            parts = input_str.strip().split()
            if not parts:
                return event.send(
                    event.plain_result(
                        "不知道你要与谁决斗哦，请@你想决斗的人~\n示例: /决斗 @用户/qq号"
                    )
                )
            to_user_ids = get_at_ids(event)
            if isinstance(to_user_ids, list) and to_user_ids:
                opponent_id = to_user_ids[0]
            else:
                if parts[0].isdigit():
                    opponent_id = parts[0]
                else:
                    return event.send(
                        event.plain_result(
                            "无效的用户ID，请@你想决斗的人~\n示例: /决斗 @用户/qq号"
                        )
                    )

            is_cooling, remaining = await self.is_cooling(challenger_id)
            if is_cooling:
                return event.send(
                    event.plain_result(
                        f"你刚刚发起了一场决斗，请耐心一点，等待{remaining:.1f}秒后再发起决斗吧！"
                    )
                )

            group_id = event.get_group_id()
            message = []
            # 检查是否@自己
            if challenger_id == opponent_id:
                message.append(Comp.At(qq=challenger_id))
                try:
                    await event.bot.set_group_ban(
                        group_id=group_id,
                        user_id=challenger_id,
                        duration=60,
                    )
                    message.append(random.choice(challenge_self_text_list))
                except Exception:
                    message.append("：\n我想禁言你一分钟，但权限不足QAQ")
                await event.send(event.chain_result(message))
                event.stop_event()
            await self.set_cooling(challenger_id)

            # 检查是否@了机器人
            if opponent_id == str(event.get_self_id()):
                message.append(Comp.At(qq=challenger_id))
                if challenger_id not in admins_id:
                    try:
                        await event.bot.set_group_ban(
                            group_id=group_id,
                            user_id=challenger_id,
                            duration=60,
                        )
                        message.append(random.choice(challenge_bot_text_list))
                    except Exception:
                        message.append("：\n我想禁言你一分钟，但权限不足QAQ")
                    await event.send(event.chain_result(message))
                    event.stop_event()
                return
            # 读取用户昵称
            cha_name = await get_nickname(event, challenger_id)
            opp_name = await get_nickname(event, opponent_id)
            # 读取用户数据
            cha_data = await read_json(self.user_data_path / f"{challenger_id}.json")
            opp_data = await read_json(self.user_data_path / f"{opponent_id}.json")

            # 判定双方权限
            is_admin1 = challenger_id in admins_id or (
                cha_data["battle"].get("privilege") == 1
            )
            is_admin2 = opponent_id in admins_id or (
                opp_data["battle"].get("privilege") == 1
            )
            if is_admin1 and is_admin2:
                return await event.send(
                    event.plain_result(
                        "你们两人都是管理员或拥有特权，神仙打架，凡人遭殃，御前决斗无法进行哦！"
                    )
                )
            # 读取用户武器数量
            numcha_3, numcha_4, numcha_5 = await self.load_weapon_count(challenger_id)
            numopp_3, numopp_4, numopp_5 = await self.load_weapon_count(opponent_id)
            # 计算战斗力
            cha_level = cha_data["battle"].get("level", 0)
            opp_level = opp_data["battle"].get("level", 0)
            win_level = cha_level - opp_level
            win_prob = (
                50
                + self.magnification * win_level
                + numcha_3
                + numcha_4 * 2
                + numcha_5 * 3
                - (numopp_3 + numopp_4 * 2 + numopp_5 * 3)
            )
            # 确保概率在合理范围
            win_prob = max(0, min(100, win_prob))

            message.append(Comp.At(qq=challenger_id))
            message_part = (
                f"：\n你的境界为【{cha_data['battle'].get('levelname', '无等级')}】\n"
                f"三星武器: {numcha_3}, 四星武器: {numcha_4}, 五星武器: {numcha_5}\n"
                f"{opp_name}的境界为【{opp_data['battle'].get('levelname', '无等级')}】\n"
                f"三星武器: {numopp_3}, 四星武器: {numopp_4}, 五星武器: {numopp_5}\n"
                f"决斗开始! 战斗力系数: {self.magnification}, 境界差: {win_level}, 你的获胜概率是: {win_prob:.2f}%\n"
                f"提示：挑战失败者将被禁言1~5分钟, 被挑战者失败将被禁言1~3分钟"
            )
            message.append(Comp.Plain(message_part))
            await event.send(event.chain_result(message))
            # 判断结果
            random_value = random.random() * 100
            # 挑战者失败
            random_time_cha = (random.randint(1, 5)) * 60
            # 被挑战者失败
            random_time_opp = (random.randint(1, 3)) * 60
            try:
                message2 = []

                # 自己是管理员直接胜利
                if is_admin1:
                    message2.append(Comp.At(qq=challenger_id))
                    await event.bot.set_group_ban(
                        group_id=group_id,
                        user_id=opponent_id,
                        duration=random_time_opp,
                    )
                    message2_part = (
                        f"不讲武德，使用了管理员之力获得了胜利。"
                        f"恭喜你与{opp_name}决斗成功。"
                        f"{opp_name}接受惩罚，已被禁言{random_time_opp / 60}分钟！"
                    )
                    message2.append(Comp.Plain(message2_part))
                    await event.send(event.chain_result(message2))
                    event.stop_event()

                # 对方是管理员直接胜利
                elif is_admin2:
                    message2.append(Comp.At(qq=challenger_id))
                    await event.bot.set_group_ban(
                        group_id=group_id,
                        user_id=challenger_id,
                        duration=random_time_cha,
                    )
                    message2_part = (
                        f"对方不讲武德，使用了管理员之力获得了胜利。"
                        f"你接受惩罚，已被禁言{random_time_cha / 60}分钟!"
                    )
                    message2.append(Comp.Plain(message2_part))
                    await event.send(event.chain_result(message2))
                    event.stop_event()
                # 挑战者胜利
                elif win_prob > random_value:
                    message2.append(Comp.At(qq=challenger_id))
                    await event.bot.set_group_ban(
                        group_id=group_id,
                        user_id=opponent_id,
                        duration=random_time_opp,
                    )
                    message2_part = (
                        f"恭喜你与{opp_name}决斗成功。"
                        f"{opp_name}接受惩罚，已被禁言{random_time_opp / 60}分钟！"
                    )
                    message2.append(Comp.Plain(message2_part))
                    await event.send(event.chain_result(message2))
                    event.stop_event()
                # 挑战者失败
                else:
                    message2.append(Comp.At(qq=challenger_id))
                    await event.bot.set_group_ban(
                        group_id=group_id,
                        user_id=challenger_id,
                        duration=random_time_cha,
                    )
                    message2_part = (
                        f"你与{opp_name}决斗失败。"
                        f"你接受惩罚，已被禁言{random_time_cha / 60}分钟！"
                    )
                    message2.append(Comp.Plain(message2_part))
                    await event.send(event.chain_result(message2))
                    event.stop_event()
            except Exception:
                await event.send(
                    event.chain_result(
                        "哎呀，禁言失败了，可能是权限不够或者出了点小问题。"
                    )
                )
            # # 保存数据
            # await write_json(self.user_data_path / f"{challenger_id}.json", cha_data)
            # await write_json(self.user_data_path / f"{opponent_id}.json", opp_data)

        except Exception as e:
            logger.error(f"处理决斗命令失败: {e}")
            return
