import hoshino
import os
import json
from hoshino import Service, util, priv
from hoshino.typing import CQEvent, MessageSegment

import asyncio
import random
import time
from random import choice
from typing import Tuple

from .txt2img import txt_to_img
from .utils import utils
from .utils import Utils
from datetime import datetime

sv = Service(
    name="impact",  # 功能名
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    bundle="娱乐",  # 分组归类
    help_="发送【银趴介绍|银趴介绍】了解更多",  # 帮助说明
)


@sv.on_prefix(("强健"))
async def pk(bot, event: CQEvent) -> None:
    """对决的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 检查CD
        allow = await utils.pkcd_check(uid)
        if not allow:
            await bot.finish(
                event,
                f"你已经草不动了喵, 请等待{round(utils.pk_cd_time - (time.time() - utils.pk_cd_data[uid]), 3)}秒后再对决喵",
                at_sender=True
            )

        # 获取目标用户
        at = await utils.get_at(event)
        if at == "寄":
            await bot.finish(event, "请at你要对决的对象哦", at_sender=True)
        if at == uid:
            await bot.finish(event, "你要草自己？", at_sender=True)

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 群隔离的用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        master_data_file = os.path.join(group_data_path, "master_data.json")
        dungeon_data_file = os.path.join(group_data_path, "dungeon_data.json")

        # 读取或初始化群用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        # 读取主人数据
        master_data = {}
        if os.path.exists(master_data_file):
            with open(master_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    master_data = json.loads(content)

        # 读取地牢数据
        dungeon_data = {}
        if os.path.exists(dungeon_data_file):
            with open(dungeon_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    dungeon_data = json.loads(content)

        # 检查双方是否有角色
        if uid not in group_userdata or at not in group_userdata:
            await bot.finish(
                event,
                "你或对方还没有创建角色喵, 发送【玩援神】加入impact~",
                at_sender=True
            )

        # 检查主人/星怒关系
        if utils.check_master_time(uid, master_data):
            # 发起者是星怒
            master_name = await utils.get_user_card(bot, int(gid), int(master_data[uid]["master"]))
            await bot.finish(event, f"你是{master_name}的星怒，不能草别人", at_sender=True)

        if utils.check_master_time(at, master_data):
            # 目标是星怒
            if master_data[at]["master"] != uid:
                # 目标不是发起者的星怒
                master_name = await utils.get_user_card(bot, int(gid), int(master_data[at]["master"]))
                await bot.finish(event, f"对方是{master_name}的星怒，不能被草", at_sender=True)
            # 如果是自己的星怒，则允许继续

        # 检查自己是否在地牢中
        if utils.check_dungeon_time(uid, dungeon_data):
            await bot.finish(event, "你被关在地牢里，无法草别人", at_sender=True)

        # 检查目标是否在地牢中
        if utils.check_dungeon_time(at, dungeon_data):
            await bot.finish(event, "对方被关在地牢里，无法被草", at_sender=True)

        # 获取双方角色类型和当前使用的道具
        attacker_data = group_userdata[uid]
        defender_data = group_userdata[at]
        attacker_type = attacker_data["type"]
        defender_type = defender_data["type"]
        attacker_item = attacker_data.get("play")
        defender_item = defender_data.get("play")

        # 获取双方昵称
        attacker_name = await utils.get_user_card(bot, int(gid), int(uid))
        defender_name = await utils.get_user_card(bot, int(gid), int(at))

        # 检查道具使用情况并进行拦截
        if attacker_type == "吉吉":
            if attacker_item == "飞机杯":
                await bot.finish(event, "你腾不出手了", at_sender=True)
            if defender_item == "紫色心情":
                await bot.finish(event, "她已经满员了，请先拔出道具", at_sender=True)
        elif attacker_type == "肖雪":
            if defender_type == "吉吉":
                if attacker_item == "紫色心情":
                    await bot.finish(event, "你腾不出手了", at_sender=True)
                if defender_item == "飞机杯":
                    await bot.finish(event, "他腾不出手了，先让他放下道具哦", at_sender=True)
            elif defender_type == "肖雪":
                if attacker_item == "紫色心情" or defender_item == "紫色心情":
                    # 双头龙情况，不拦截
                    pass

        # 更新CD时间（只有实际执行对决时才更新）
        utils.pk_cd_data.update({uid: time.time()})

        # 特殊处理：检查注入值
        ejaculation_msg = ""
        if (attacker_type, defender_type) == ("吉吉", "肖雪"):
            if "ejaculation" not in defender_data:
                defender_data["ejaculation"] = 0
            if "ejaculation" not in attacker_data:
                attacker_data["ejaculation"] = 0

            if defender_data["ejaculation"] == 0:
                ejaculation_msg = f"\n你破了{defender_name}的处~"

            # 随机生成注入值(1-10)
            ejaculation_gain = random.randint(1, 10)
            defender_data["ejaculation"] += ejaculation_gain
            attacker_data["ejaculation"] -= ejaculation_gain
            ejaculation_msg += f"\n向{defender_name}的肖雪注入了{ejaculation_gain}ml脱氧核糖核酸"

        elif (attacker_type, defender_type) == ("肖雪", "吉吉"):
            if "ejaculation" not in attacker_data:
                attacker_data["ejaculation"] = 0

            if attacker_data["ejaculation"] == 0:
                ejaculation_msg = f"\n你把第一次献给了{defender_name}"

            ejaculation_gain = random.randint(1, 10)
            attacker_data["ejaculation"] += ejaculation_gain
            ejaculation_msg += f"\n你榨出了{ejaculation_gain}ml"

        # 根据双方角色类型生成不同的对决描述和结果
        type_combinations = {
            ("吉吉", "吉吉"): {
                "action": f"【{attacker_name}】与【{defender_name}】居然在击剑🤺？",
                "win": [
                    f"你更胜一筹，将【{defender_name}】击倒在地",
                ],
                "lose": [
                    f"而你技不如人，被【{defender_name}】击倒在地",
                ]
            },
            ("吉吉", "肖雪"): {
                "action": f"【{attacker_name}】狠狠抽查【{defender_name}】的肖雪",
                "win": [
                    f"【{defender_name}】被你干趴下了，抖个不停",
                ],
                "lose": [
                    f"但【{defender_name}】却牢牢夹住，反过来把你榨了一通",
                ]
            },
            ("肖雪", "吉吉"): {
                "action": f"【{attacker_name}】骑在【{defender_name}】身上开榨",
                "win": [
                    f"你将【{defender_name}】的吉吉完全吞噬，让对方动弹不得",
                ],
                "lose": [
                    f"不料【{defender_name}】突然发力，将你按倒"
                ]
            },
            ("肖雪", "肖雪"): {
                "action": f"【{attacker_name}】与【{defender_name}】磨起了豆腐",
                "win": [
                    f"把对方扣倒在地，【{defender_name}】在地上抽搐，感觉被玩坏了",
                ],
                "lose": [
                    f"却被对方扣倒在地，不堪其辱",
                ]
            }
        }

        # 如果是双头龙情况，修改描述
        if (attacker_type == "肖雪" and defender_type == "肖雪" and
            (attacker_item == "紫色心情" or defender_item == "紫色心情")):
            type_combinations[("肖雪", "肖雪")] = {
                "action": f"【{attacker_name}】与【{defender_name}】磨豆腐，不料双头龙互将二人连接",
                "win": [
                    f"你两玩得浑身发抖，瘫软在地",
                ],
                "lose": [
                    f"你两玩得浑身发抖，瘫软在地",
                ]
            }

        # 获取对决描述和结果模板
        combat_data = type_combinations.get((attacker_type, defender_type), {
            "action": "开超",
            "win": [f"【{attacker_name}】成功战胜了【{defender_name}】"],
            "lose": [f"【{defender_name}】成功反杀了【{attacker_name}】"]
        })

        action_desc = combat_data["action"]

        # 使用涩涩值作为胜率基础
        attacker_silver = attacker_data["silver"]
        defender_silver = defender_data["silver"]

        # 计算胜率 (攻击者胜率 = 攻击者涩涩值 / (攻击者涩涩值 + 防御者涩涩值))
        total_silver = attacker_silver + defender_silver
        attacker_win_rate = attacker_silver / total_silver if total_silver > 0 else 0.5

        # 随机决定胜负
        is_attacker_win = random.random() < attacker_win_rate

        # 随机生成属性增益
        silver_gain = random.randint(1, 10)
        development_gain = random.randint(1, 5)

        # 更新双方数据
        if is_attacker_win:
            # 攻击者胜利
            group_userdata[uid]["silver"] += silver_gain
            group_userdata[uid]["development"] += development_gain
            group_userdata[at]["development"] += development_gain

            result_desc = random.choice(combat_data["win"])
            result_msg = (
                f"{action_desc}，{result_desc}"
                f"{ejaculation_msg}\n"
                f"【{attacker_name}】涩涩值+{silver_gain}，{attacker_type}开发度+{development_gain}\n"
                f"【{defender_name}】{defender_type}开发度+{development_gain}"
            )
        else:
            # 防御者胜利
            group_userdata[at]["silver"] += silver_gain
            group_userdata[at]["development"] += development_gain
            group_userdata[uid]["development"] += development_gain

            result_desc = random.choice(combat_data["lose"])
            result_msg = (
                f"{action_desc}，{result_desc}！"
                f"{ejaculation_msg}\n"
                f"【{defender_name}】涩涩值+{silver_gain}，{defender_type}开发度+{development_gain}\n"
                f"【{attacker_name}】{attacker_type}开发度+{development_gain}"
            )

        # 写入数据
        with open(userdata_file, "w", encoding="utf-8") as f:
            json.dump(group_userdata, f, indent=4, ensure_ascii=False)

        await bot.send(event, result_msg)

    except Exception as e:
        sv.logger.error(f"对决时出错: {type(e).__name__}: {e}")
        return


@sv.on_rex("^(鹿)$")
async def lu(bot, event: CQEvent) -> None:
    """鹿的响应器（根据次数返回不同结果）"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(str(event.group_id))):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 群隔离的用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        daily_count_file = os.path.join(group_data_path, "daily_count.json")
        master_data_file = os.path.join(group_data_path, "master_data.json")

        # 读取主人数据
        master_data = {}
        if os.path.exists(master_data_file):
            with open(master_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    master_data = json.loads(content)

        # 检查自己是否有主人
        if utils.check_master_time(uid, master_data):
            master_name = await utils.get_user_card(bot, int(gid), int(master_data[uid]["master"]))
            await bot.finish(event, f"你是{master_name}的星怒，需要主人允许才能鹿", at_sender=True)

        # 读取或初始化群用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        # 读取或初始化每日计数数据
        daily_data = {}
        if os.path.exists(daily_count_file):
            with open(daily_count_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    daily_data = json.loads(content)

        if uid not in group_userdata:
            await bot.finish(
                event,
                "您还没有吉吉喵！请先使用【玩援神】加入impact~",
                at_sender=False
            )

        if uid in group_userdata and group_userdata[uid].get("type") == "肖雪":
            await bot.finish(event, "你没有吉吉哦，回去扣扣好了", at_sender=False)

        today = utils.get_today()
        if today not in daily_data:
            daily_data[today] = {}
        current_count = daily_data[today].get(uid, 0)

        # 检查CD
        cd_key = f"{gid}_{uid}"
        current_time = time.time()
        if cd_key in utils.cd_data:
            elapsed = current_time - utils.cd_data[cd_key]
            if elapsed < utils.dj_cd_time:
                remaining = utils.dj_cd_time - elapsed
                await bot.finish(event, f"都撸秃了喵，请等待{round(remaining, 1)}秒再撸喵", at_sender=False)

        # 更新CD时间
        utils.cd_data[cd_key] = current_time

        # 获取用户昵称
        user_name = await utils.get_user_card(bot, int(gid), int(uid))

        # 随机生成银值(1-10)和开发度(0-5)
        silver_gain = random.randint(1, 10)
        development_gain = random.randint(1, 5)

        # 初始化用户数据
        if uid not in group_userdata:
            group_userdata[uid] = {
                "type": "吉吉",
                "silver": 0,
                "development": 0,
                "last_update": today
            }

        # 检查是否是同一天
        if group_userdata[uid]["last_update"] != today:
            # 新的一天，重置计数
            current_count = 0

        # 更新计数
        new_count = current_count + 1
        daily_data[today][uid] = new_count

        # 根据次数选择不同反应
        reaction_map = {
            1: "起飞！✈",
            2: "还来？",
            3: "出血了也要继续？",
        }
        reaction = reaction_map.get(new_count, "出血了也要继续？")

        # 更新用户数据
        group_userdata[uid]["silver"] += silver_gain
        group_userdata[uid]["development"] += development_gain
        group_userdata[uid]["last_update"] = today

        # 写入数据
        with open(userdata_file, "w", encoding="utf-8") as f:
            json.dump(group_userdata, f, indent=4, ensure_ascii=False)

        with open(daily_count_file, "w", encoding="utf-8") as f:
            json.dump(daily_data, f, indent=4, ensure_ascii=False)

        # 构造回复消息
        msg = (
            f"{reaction}{user_name}成功鹿了一发\n"
            f"涩涩值+{silver_gain}\n"
            f"吉吉开发度+{development_gain}"
        )

        await bot.send(event, msg)

    except Exception as e:
        sv.logger.error(f"撸鹿时出错: {type(e).__name__}: {e}")
        return


@sv.on_rex("^(扣)$")
async def kou(bot, event: CQEvent) -> None:
    """扣的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(str(event.group_id))):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 群隔离的用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        master_data_file = os.path.join(group_data_path, "master_data.json")

        # 读取主人数据
        master_data = {}
        if os.path.exists(master_data_file):
            with open(master_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    master_data = json.loads(content)

        # 检查自己是否有主人
        if utils.check_master_time(uid, master_data):
            master_name = await utils.get_user_card(bot, int(gid), int(master_data[uid]["master"]))
            await bot.finish(event, f"你是{master_name}的星怒，需要主人允许才能扣", at_sender=True)
        # 读取或初始化群用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        # 检查用户是否有肖雪
        if uid not in group_userdata:
            await bot.finish(
                event,
                "您还没有肖雪喵！请先使用【玩援神】加入impact~",
                at_sender=False
            )

        if group_userdata[uid].get("type") != "肖雪":
            await bot.finish(event, "你没有肖雪哦，回去起飞好了", at_sender=False)

        # 检查CD
        cd_key = f"{gid}_{uid}"
        current_time = time.time()
        if cd_key in utils.cd_data:
            elapsed = current_time - utils.cd_data[cd_key]
            if elapsed < utils.dj_cd_time:
                remaining = utils.dj_cd_time - elapsed
                await bot.finish(event, f"你瘫软在地，请等待{round(remaining, 1)}秒再扣喵", at_sender=False)

        # 更新CD时间
        utils.cd_data[cd_key] = current_time

        # 获取用户昵称
        user_name = await utils.get_user_card(bot, int(gid), int(uid))

        # 随机生成银值(1-10)和开发度(0-5)
        silver_gain = random.randint(1, 10)
        development_gain = random.randint(1, 5)

        # 更新用户数据
        group_userdata[uid]["silver"] += silver_gain
        group_userdata[uid]["development"] += development_gain
        group_userdata[uid]["last_update"] = utils.get_today()

        # 写入数据
        with open(userdata_file, "w", encoding="utf-8") as f:
            json.dump(group_userdata, f, indent=4, ensure_ascii=False)

        # 构造回复消息
        msg = (
            f"{user_name}忍不住扣起欢乐豆\n"
            f"涩涩值+{silver_gain}\n"
            f"肖雪开发度+{development_gain}"
        )

        await bot.send(event, msg)

    except Exception as e:
        sv.logger.error(f"撸鹿时出错: {type(e).__name__}: {e}")
        return


@sv.on_prefix("开嗦")
async def suo(bot, event: CQEvent) -> None:
    """嗦的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 检查CD
        allow = await utils.suo_cd_check(uid)
        if not allow:
            await bot.finish(
                event,
                f"你已经嗦不动了喵, 请等待{round(utils.suo_cd_time - (time.time() - utils.suo_cd_data[uid]), 3)}秒后再嗦喵",
                at_sender=True
            )

        # 获取目标用户
        at = await utils.get_at(event)
        if at == "寄":
            await bot.finish(event, "你要嗦自己么？", at_sender=True)

        target_id = at
        target_name = await utils.get_user_card(bot, int(gid), int(target_id))
        user_name = await utils.get_user_card(bot, int(gid), int(uid))

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 群隔离的用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        master_data_file = os.path.join(group_data_path, "master_data.json")
        dungeon_data_file = os.path.join(group_data_path, "dungeon_data.json")

        # 读取或初始化群用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        # 读取主人数据
        master_data = {}
        if os.path.exists(master_data_file):
            with open(master_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    master_data = json.loads(content)

        # 读取地牢数据
        dungeon_data = {}
        if os.path.exists(dungeon_data_file):
            with open(dungeon_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    dungeon_data = json.loads(content)

        # 检查目标是否有角色
        if target_id not in group_userdata:
            await bot.finish(
                event,
                f"{target_name}还没有创建角色喵！发送【玩援神】加入impact~",
                at_sender=False
            )

        # 检查自己是否有主人 - 如果是星怒则不能开嗦
        if utils.check_master_time(uid, master_data):
            master_name = await utils.get_user_card(bot, int(gid), int(master_data[uid]["master"]))
            await bot.finish(event, f"你是{master_name}的星怒，不能开嗦", at_sender=True)

        # 检查目标是否有主人 - 如果不是自己的星怒则不能嗦
        if utils.check_master_time(target_id, master_data):
            if master_data[target_id]["master"] != uid:
                master_name = await utils.get_user_card(bot, int(gid), int(master_data[target_id]["master"]))
                await bot.finish(event, f"对方是{master_name}的星怒，不能被嗦", at_sender=True)

        # 检查自己是否在地牢中
        if utils.check_dungeon_time(uid, dungeon_data):
            await bot.finish(event, "你被关在地牢里，无法嗦别人", at_sender=True)

        # 检查目标是否在地牢中
        if utils.check_dungeon_time(target_id, dungeon_data):
            await bot.finish(event, "对方被关在地牢里，无法被嗦", at_sender=True)

        # 检查自己是否使用口球道具
        if group_userdata.get(uid, {}).get("play") == "口球":
            await bot.finish(
                event,
                "你戴着口球，无法嗦哦",
                at_sender=True
            )
        if group_userdata.get(target_id, {}).get("play") == "飞机杯":
            await bot.finish(
                event,
                "对方正在使用飞机杯，腾不出手了",
                at_sender=True
            )

        # 更新CD时间（只有通过所有检查后才更新）
        utils.suo_cd_data.update({uid: time.time()})

        # 获取目标角色类型
        target_type = group_userdata[target_id]["type"]

        # 随机生成涩涩值和开发度增益
        silver_gain = random.randint(1, 5)
        development_gain = random.randint(1, 3)

        # 更新用户数据
        group_userdata[target_id]["silver"] += silver_gain
        group_userdata[target_id]["development"] += development_gain
        group_userdata[uid]["silver"] += silver_gain
        group_userdata[uid]["last_update"] = utils.get_today()

        # 写入数据
        with open(userdata_file, "w", encoding="utf-8") as f:
            json.dump(group_userdata, f, indent=4, ensure_ascii=False)

        # 根据目标角色类型生成不同的回应
        responses = {
            "吉吉": [
                f"【{user_name}】娴熟的嗦起【{target_name}】的吉吉，被🐍了一嘴，"
            ],
            "肖雪": [
                f"【{user_name}】娴熟的舔起【{target_name}】的肖雪，被喷了一脸，"
            ]
        }

        # 构造回复消息
        response = random.choice(responses[target_type])
        msg = (
            f"{response}"
            f"【{target_name}】的{target_type}开发度+{development_gain}，"
            f"双方涩涩值+{silver_gain}"
        )

        await bot.send(event, msg)

    except Exception as e:
        sv.logger.error(f"嗦时出错: {type(e).__name__}: {e}")
        return


@sv.on_prefix("使用玩具")
async def use_item(bot, event: CQEvent) -> None:
    """使用玩具的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 获取道具名和目标用户
        msg = event.message.extract_plain_text().strip()
        if not msg:
            await bot.finish(event, "请指定要使用的道具", at_sender=True)

        # 解析道具名和目标用户
        parts = msg.split()
        if not parts:
            await bot.finish(event, "请指定要使用的道具", at_sender=True)

        item_name = parts[0]
        at = await utils.get_at(event)
        target_id = at if at != "寄" else uid

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 群隔离的用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        item_data_file = os.path.join(group_data_path, "item_data.json")
        master_data_file = os.path.join(group_data_path, "master_data.json")
        dungeon_data_file = os.path.join(group_data_path, "dungeon_data.json")

        # 读取或初始化群用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        item_data = {}
        if os.path.exists(item_data_file):
            with open(item_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    item_data = json.loads(content)

        # 读取主人数据
        master_data = {}
        if os.path.exists(master_data_file):
            with open(master_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    master_data = json.loads(content)

        # 检查目标用户是否有角色
        if target_id not in group_userdata:
            await bot.finish(
                event,
                "还没有创建角色喵！发送【玩援神】加入impact~",
                at_sender=False
            )

        # 检查自己是否有主人 - 如果是星怒则不能使用道具
        if utils.check_master_time(uid, master_data):
            master_name = await utils.get_user_card(bot, int(gid), int(master_data[uid]["master"]))
            await bot.finish(event, f"你是{master_name}的星怒，不能使用道具", at_sender=True)

        # 检查目标是否有主人 - 如果不是自己的星怒则不能使用道具
        if utils.check_master_time(target_id, master_data):
            if master_data[target_id]["master"] != uid:
                master_name = await utils.get_user_card(bot, int(gid), int(master_data[target_id]["master"]))
                await bot.finish(event, f"对方是{master_name}的星怒，不能被使用道具", at_sender=True)

        # 获取用户角色类型和昵称
        target_type = group_userdata[target_id]["type"]
        target_name = await utils.get_user_card(bot, int(gid), int(target_id))

        # 检查涩涩值是否达到100
        if group_userdata[target_id]["silver"] < 100:
            await bot.finish(
                event,
                f"{target_name}过于纯洁(涩涩值<100)，使用不了道具哦",
                at_sender=True
            )

        # 检查道具是否可用
        valid_items = {
            "吉吉": ["飞机杯", "口球"],
            "肖雪": ["紫色心情", "跳蛋", "口球"]
        }

        if item_name not in valid_items[target_type]:
            await bot.finish(
                event,
                f"你不能使用{item_name}哦",
                at_sender=True
            )

        # 检查是否已经使用道具
        if group_userdata[target_id].get("play") is not None:
            await bot.finish(
                event,
                f"{target_name}已经在使用{group_userdata[target_id]['play']}了，先取下吧",
                at_sender=True
            )

        # 更新用户数据和道具数据
        group_userdata[target_id]["play"] = item_name
        current_time = time.time()

        if target_id not in item_data:
            item_data[target_id] = {}
        item_data[target_id][item_name] = current_time

        # 写入数据
        with open(userdata_file, "w", encoding="utf-8") as f:
            json.dump(group_userdata, f, indent=4, ensure_ascii=False)

        with open(item_data_file, "w", encoding="utf-8") as f:
            json.dump(item_data, f, indent=4, ensure_ascii=False)

        # 根据不同道具生成不同的回应
        item_responses = {
            "飞机杯": [
                f"【{target_name}】使用飞机杯开始练习手速，快出残影"
            ],
            "口球": [
                f"【{target_name}】塞上了口球，只能发出呜呜的声音"
            ],
            "紫色心情": [
                f"【{target_name}】插上了紫色心情，感觉被狠狠撑开了"
            ],
            "跳蛋": [
                f"【{target_name}】塞入了跳蛋，剧烈震动导致双腿开始发抖"
            ]
        }

        # 构造回复消息
        response = random.choice(item_responses.get(item_name, [f"{target_name}使用了{item_name}"]))

        await bot.send(event, response)

    except Exception as e:
        sv.logger.error(f"使用道具时出错: {type(e).__name__}: {e}")
        return


@sv.on_prefix("取下玩具")
async def remove_item(bot, event: CQEvent) -> None:
    """取下玩具的响应器"""
    gid = str(event.group_id)
    uid = str(event.user_id)

    if not (await utils.check_group_allow(gid)):
        await bot.finish(event, utils.not_allow, at_sender=True)

    # 获取道具名和目标用户
    msg = event.message.extract_plain_text().strip()
    if not msg:
        await bot.finish(event, "请指定要取下的道具", at_sender=True)

    # 解析道具名和目标用户
    parts = msg.split()
    if not parts:
        await bot.finish(event, "请指定要取下的道具", at_sender=True)

    item_name = parts[0]
    at = await utils.get_at(event)
    target_id = at if at != "寄" else uid

    # 初始化群数据目录
    group_data_path = os.path.join(utils.data_path, gid)
    if not os.path.exists(group_data_path):
        os.makedirs(group_data_path)

    # 群隔离的用户数据文件路径
    userdata_file = os.path.join(group_data_path, "userdata.json")
    item_data_file = os.path.join(group_data_path, "item_data.json")

    # 读取或初始化群用户数据
    group_userdata = {}
    if os.path.exists(userdata_file):
        with open(userdata_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                group_userdata = json.loads(content)

    # 读取或初始化道具数据
    item_data = {}
    if os.path.exists(item_data_file):
        with open(item_data_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                item_data = json.loads(content)

    # 检查目标用户是否有角色
    if target_id not in group_userdata:
        await bot.finish(
            event,
            "还没有创建角色喵！发送【玩援神】加入impact~",
            at_sender=False
        )

    # 获取用户昵称
    target_name = await utils.get_user_card(bot, int(gid), int(target_id))

    # 检查是否使用了道具
    if group_userdata[target_id].get("play") is None:
        await bot.finish(
            event,
            f"{target_name}没有使用任何道具",
            at_sender=True
        )

    # 检查是否使用了指定的道具
    current_item = group_userdata[target_id]["play"]
    if current_item != item_name:
        await bot.finish(
            event,
            f"你没有在使用{item_name}",
            at_sender=True
        )

    # 获取使用时间信息
    time_used_msg = ""
    development_gain = 0
    if target_id in item_data and item_name in item_data[target_id]:
        use_time = item_data[target_id][item_name]
        elapsed_seconds = time.time() - use_time
        elapsed_minutes = int(elapsed_seconds // 60)
        elapsed_hours = int(elapsed_seconds // 3600)

        # 生成使用时间描述
        if elapsed_hours > 0:
            remaining_minutes = int((elapsed_seconds % 3600) // 60)
            time_used_msg = f"，已经使用了{elapsed_hours}小时{remaining_minutes}分钟"
        else:
            time_used_msg = f"，已经使用了{elapsed_minutes}分钟"

        # 计算开发度增益
        if item_name in ["飞机杯", "紫色心情", "跳蛋"]:
            development_gain = int(elapsed_hours)

    # 根据不同道具生成不同的取下回应
    item_remove_responses = {
        "飞机杯": [
            f"【{target_name}】放下了已是黏糊糊的飞机杯",
        ],
        "口球": [
            f"【{target_name}】取下了湿漉漉的口球，涩呼呼的哈气"
        ],
        "紫色心情": [
            f"【{target_name}】腿软地取下了紫色心情，站不稳倒在原地"
        ],
        "跳蛋": [
            f"【{target_name}】颤抖着取出了跳蛋，已经泛滥成灾了"
        ]
    }

    response = random.choice(item_remove_responses.get(item_name, [f"{target_name}取下了{item_name}"]))
    msg = response + time_used_msg
    if development_gain > 0:
        msg += f"，{group_userdata[target_id]['type']}开发度+{development_gain}"
    await bot.send(event, msg)

    # 执行数据操作
    group_userdata[target_id]["play"] = None
    if development_gain > 0:
        group_userdata[target_id]["development"] += development_gain

    # 删除道具记录
    if target_id in item_data and item_name in item_data[target_id]:
        del item_data[target_id][item_name]
        if not item_data[target_id]:
            del item_data[target_id]

    # 写入数据
    with open(userdata_file, "w", encoding="utf-8") as f:
        json.dump(group_userdata, f, indent=4, ensure_ascii=False)

    with open(item_data_file, "w", encoding="utf-8") as f:
        json.dump(item_data, f, indent=4, ensure_ascii=False)

@sv.on_fullmatch("重开")
async def restart_life(bot, event: CQEvent) -> None:
    """重开的响应器（每周限一次）"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(str(event.group_id))):
            await bot.finish(event, utils.not_allow, at_sender=True)
        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 群隔离的用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        restart_data_file = os.path.join(group_data_path, "restart_data.json")

        # 读取或初始化群用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        # 读取或初始化重开记录数据
        restart_data = {}
        if os.path.exists(restart_data_file):
            with open(restart_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    restart_data = json.loads(content)

        # 检查用户是否有角色
        if uid not in group_userdata:
            await bot.finish(event, "你还没有加入impact喵，无法重开喵", at_sender=False)

        # 获取当前周数（用于判断是否本周已重开）
        current_week = utils.get_current_week()

        # 检查是否本周已重开
        if uid in restart_data and restart_data[uid]["week"] == current_week:
            await bot.finish(event, "本周你已经重开过了喵，请下周再来喵", at_sender=False)

        # 获取用户昵称
        user_name = await utils.get_user_card(bot, int(gid), int(uid))

        # 保留原来的涩涩值
        current_silver = group_userdata[uid].get("silver", 0)

        # 随机生成新的角色和属性（保留涩涩值）
        new_type = "吉吉" if random.random() > 0.5 else "肖雪"
        new_development = 0  # 开发度重置为0

        # 更新用户数据（保留涩涩值）
        group_userdata[uid] = {
            "type": new_type,
            "silver": current_silver,
            "development": new_development,
            "last_update": utils.get_today(),
            "play": None,
            "ejaculation": 0,
            "ejaculation_history": 0,
            "dungeon": None,
            "master": "无",
        }

        # 更新重开记录
        restart_data[uid] = {
            "week": current_week,
            "last_restart_time": time.time()
        }

        # 写入数据
        with open(userdata_file, "w", encoding="utf-8") as f:
            json.dump(group_userdata, f, indent=4, ensure_ascii=False)

        with open(restart_data_file, "w", encoding="utf-8") as f:
            json.dump(restart_data, f, indent=4, ensure_ascii=False)

        # 构造回复消息
        msg = (
            f"{user_name}重开了，获得了"
            f"{new_type}"
            f"，保留了原有涩涩值{current_silver}"
        )

        await bot.send(event, msg)

    except Exception as e:
        sv.logger.error(f"重开时出错: {type(e).__name__}: {e}")
        return


@sv.on_prefix("玩援神")
async def generate_jj(bot, event: CQEvent):
    """生成JJ或肖雪的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(str(event.group_id))):
            await bot.finish(event, utils.not_allow, at_sender=True)
        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 群隔离的用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")

        # 读取或初始化群用户数据（带错误处理）
        group_userdata = {}
        if os.path.exists(userdata_file):
            try:
                with open(userdata_file, "r", encoding="utf-8") as f:
                    # 检查文件是否为空
                    content = f.read().strip()
                    if content:
                        group_userdata = json.loads(content)
            except (json.JSONDecodeError, IOError) as e:
                sv.logger.error(f"读取用户数据文件失败，将使用空数据: {e}")
                group_userdata = {}

        # 获取用户昵称
        async def get_user_name(qid):
            try:
                user_info = await bot.get_group_member_info(group_id=int(gid), user_id=int(qid))
                return user_info["card"] or user_info["nickname"]
            except:
                return "查无此人"

        # 确定目标用户
        at = await utils.get_at(event)
        target_id = at if at != "寄" else uid
        target_name = await get_user_name(target_id)

        # 检查用户数据是否已存在
        if target_id in group_userdata:
            user_data = group_userdata[target_id]
            await bot.finish(event, f"{target_name}已经拥有{user_data['type']}喵", at_sender=False)

        silver = random.randint(1, 10)
        jj_type = "吉吉" if random.random() > 0.5 else "肖雪"
        msg = f"【{target_name}】获得了{jj_type}喵，开启了应当的一生，初始值涩涩为{silver}喵"

        today = utils.get_today()
        # 更新并写入数据（按照要求的完整格式）
        group_userdata[target_id] = {
            "type": jj_type,
            "silver": silver,
            "development": 0,
            "last_update": today,
            "play": None,
            "ejaculation": 0,
            "ejaculation_history": 0,
            "dungeon": null,
            "master": "无",
        }

        try:
            with open(userdata_file, "w", encoding="utf-8") as f:
                json.dump(group_userdata, f, indent=4, ensure_ascii=False)
        except IOError as e:
            sv.logger.error(f"写入用户数据文件失败: {e}")
            await bot.finish(event, "数据保存失败，请联系管理员", at_sender=False)

        await bot.finish(event, msg, at_sender=False)

    except Exception as e:
        sv.logger.error(f"生成JJ时出错: {type(e).__name__}: {e}")
        return


@sv.on_fullmatch("使劲玩弄")
async def play_hard(bot, event: CQEvent) -> None:
    """使劲玩弄自己的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 检查CD
        if not (await utils.play_hard_cd_check(uid)):
            await bot.finish(event, "你已经被玩坏了，需要休息3小时才能再玩", at_sender=True)

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 群隔离的用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        master_data_file = os.path.join(group_data_path, "master_data.json")

        # 读取或初始化群用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        # 读取主人数据
        master_data = {}
        if os.path.exists(master_data_file):
            with open(master_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    master_data = json.loads(content)

        # 检查用户是否有角色
        if uid not in group_userdata:
            await bot.finish(event, "你还没有加入impact喵，发送【玩援神】加入~", at_sender=True)

        # 新增：检查自己是否是星怒
        if utils.check_master_time(uid, master_data):
            master_name = await utils.get_user_card(bot, int(gid), int(master_data[uid]["master"]))
            await bot.finish(event, f"你是{master_name}的星怒，不能使劲玩弄自己", at_sender=True)

        # 获取用户数据
        user_data = group_userdata[uid]
        user_type = user_data["type"]
        user_name = await utils.get_user_card(bot, int(gid), int(uid))

        # 随机生成属性增益
        silver_gain = random.randint(5, 20)
        development_gain = random.randint(5, 20)

        # 根据角色类型处理
        if user_type == "肖雪":
            # 处理肖雪用户
            ejaculation = user_data.get("ejaculation", 0)
            if ejaculation > 10:  # 只有注入值大于10才会扣除
                ejaculation_loss = random.randint(1, 8)
                user_data["ejaculation"] = max(0, ejaculation - ejaculation_loss)
                msg = (
                    f"【{user_name}】全身发热，扣个不停，直到爽晕过去为止\n"
                    f"肖雪里缓缓流出储存的{ejaculation_loss}ml脱氧核糖核酸\n"
                    f"涩涩值+{silver_gain}，肖雪开发度+{development_gain}"
                )
            elif ejaculation > 0:
                msg = (
                    f"【{user_name}】全身发热，扣个不停，直到爽晕过去为止\n"
                    f"涩涩值+{silver_gain}，肖雪开发度+{development_gain}"
                )
            else:  # 注入值为0
                msg = (
                    f"【{user_name}】全身发热，扣个不停，直到爽晕过去为止\n"
                    f"涩涩值+{silver_gain}，肖雪开发度+{development_gain}"
                )
        else:
            # 处理吉吉用户
            msg = (
                f"【{user_name}】察觉到点了，航班又要起飞咯，不要命似的使劲冲导致昏过去了\n"
                f"涩涩值+{silver_gain}，吉吉开发度+{development_gain}"
            )

        # 更新用户数据
        user_data["silver"] = user_data.get("silver", 0) + silver_gain
        user_data["development"] = user_data.get("development", 0) + development_gain
        user_data["last_update"] = utils.get_today()

        # 更新CD
        utils.play_hard_cd_data[uid] = time.time()

        # 写入数据
        with open(userdata_file, "w", encoding="utf-8") as f:
            json.dump(group_userdata, f, indent=4, ensure_ascii=False)

        await bot.send(event, msg)

    except Exception as e:
        sv.logger.error(f"使劲玩弄时出错: {type(e).__name__}: {e}")
        return

@sv.on_prefix(("黑暗游戏"))
async def dark_game(bot, event: CQEvent):
    """黑暗游戏的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        os.makedirs(group_data_path, exist_ok=True)  # 确保目录存在

        # 文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        master_data_file = os.path.join(group_data_path, "master_data.json")
        dark_game_cd_file = os.path.join(group_data_path, "dark_game_cd.json")

        # 安全的JSON文件读取函数
        def safe_read_json(file_path):
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        return json.loads(content) if content else {}
                except (json.JSONDecodeError, IOError):
                    return {}
            return {}

        # 读取数据
        group_userdata = safe_read_json(userdata_file)
        master_data = safe_read_json(master_data_file)
        dark_game_cd = safe_read_json(dark_game_cd_file)

        # 获取目标用户
        at = await utils.get_at(event)
        if at == "寄":
            await bot.finish(event, "黑暗游戏只能对他人使用喵", at_sender=True)

        target_id = at
        target_name = await utils.get_user_card(bot, int(gid), int(target_id))
        user_name = await utils.get_user_card(bot, int(gid), int(uid))

        # 检查目标用户是否存在
        if target_id not in group_userdata:
            await bot.finish(event, f"查无此人", at_sender=True)

        # 检查CD（3天一次）
        current_time = time.time()
        if uid in dark_game_cd:
            last_use_time = dark_game_cd[uid]
            if current_time - last_use_time < 3 * 24 * 3600:  # 3天
                remaining = 3 * 24 * 3600 - (current_time - last_use_time)
                remaining_hours = int(remaining // 3600)
                remaining_minutes = int((remaining % 3600) // 60)
                await bot.finish(
                    event,
                    f"黑暗游戏冷却中，还需等待{remaining_hours}小时{remaining_minutes}分钟",
                    at_sender=True
                )

        # 检查目标是否已经有主人
        if utils.check_master_time(target_id, master_data):
            await bot.finish(event, f"{target_name}已经有主人了喵", at_sender=True)

        # 检查自己是否已经有主人
        if utils.check_master_time(uid, master_data):
            await bot.finish(event, "你已经有主人了，不能进行黑暗游戏喵", at_sender=True)

        # 计算成功率（基于双方涩涩值）
        attacker_silver = group_userdata[uid]["silver"]
        defender_silver = group_userdata[target_id]["silver"]
        success_rate = attacker_silver / (attacker_silver + defender_silver) if (attacker_silver + defender_silver) > 0 else 0.5

        # 随机决定是否成功
        is_success = random.random() < success_rate

        if is_success:
            # 成功成为对方主人
            group_userdata[target_id]["master"] = uid
            master_data[target_id] = {
                "master": uid,
                "release_time": utils.get_master_release_time().isoformat()
            }

            # 更新CD
            dark_game_cd[uid] = current_time

            # 确保目录存在
            os.makedirs(os.path.dirname(userdata_file), exist_ok=True)
            os.makedirs(os.path.dirname(master_data_file), exist_ok=True)
            os.makedirs(os.path.dirname(dark_game_cd_file), exist_ok=True)

            # 写入数据
            with open(userdata_file, "w", encoding="utf-8") as f:
                json.dump(group_userdata, f, indent=4, ensure_ascii=False)
            with open(master_data_file, "w", encoding="utf-8") as f:
                json.dump(master_data, f, indent=4, ensure_ascii=False)
            with open(dark_game_cd_file, "w", encoding="utf-8") as f:
                json.dump(dark_game_cd, f, indent=4, ensure_ascii=False)

            await bot.send(event, f"【{user_name}】打倒了【{target_name}】，成为了一日主人")
        else:
            # 失败，对方成为自己的主人
            group_userdata[uid]["master"] = target_id
            master_data[uid] = {
                "master": target_id,
                "release_time": utils.get_master_release_time().isoformat()
            }

            # 更新CD
            dark_game_cd[uid] = current_time

            # 确保目录存在
            os.makedirs(os.path.dirname(userdata_file), exist_ok=True)
            os.makedirs(os.path.dirname(master_data_file), exist_ok=True)
            os.makedirs(os.path.dirname(dark_game_cd_file), exist_ok=True)

            # 写入数据
            with open(userdata_file, "w", encoding="utf-8") as f:
                json.dump(group_userdata, f, indent=4, ensure_ascii=False)
            with open(master_data_file, "w", encoding="utf-8") as f:
                json.dump(master_data, f, indent=4, ensure_ascii=False)
            with open(dark_game_cd_file, "w", encoding="utf-8") as f:
                json.dump(dark_game_cd, f, indent=4, ensure_ascii=False)

            await bot.send(event, f"【{user_name}】被打倒，成为了【{target_name}】的一日星怒")

    except Exception as e:
        sv.logger.error(f"黑暗游戏时出错: {type(e).__name__}: {e}")
        return

@sv.on_prefix(("关地牢里"))
async def put_in_dungeon(bot, event: CQEvent):
    """将用户关进地牢的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        os.makedirs(group_data_path, exist_ok=True)

        # 文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        dungeon_data_file = os.path.join(group_data_path, "dungeon_data.json")
        daily_dungeon_file = os.path.join(group_data_path, "daily_dungeon.json")

        # 安全读取JSON文件
        def safe_read_json(file_path):
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        return json.loads(content) if content else {}
                except (json.JSONDecodeError, IOError):
                    return {}
            return {}

        # 读取数据
        group_userdata = safe_read_json(userdata_file)
        dungeon_data = safe_read_json(dungeon_data_file)
        daily_dungeon = safe_read_json(daily_dungeon_file)

        # 获取目标用户
        at = await utils.get_at(event)
        target_id = at if at != "寄" else uid
        target_name = await utils.get_user_card(bot, int(gid), int(target_id))
        user_name = await utils.get_user_card(bot, int(gid), int(uid))

        # 检查目标用户是否存在
        if target_id not in group_userdata:
            await bot.finish(event, f"{target_name}还没有角色喵", at_sender=True)

        # 检查每日使用限制
        today = utils.get_today()
        if today not in daily_dungeon:
            daily_dungeon[today] = {}

        if uid in daily_dungeon[today]:
            await bot.finish(event, "你今天已经使用过地牢了喵", at_sender=True)

        # 如果是自己关自己，直接成功
        if target_id == uid:
            # 更新地牢状态
            group_userdata[uid]["dungeon"] = "被关"
            dungeon_data[uid] = utils.get_dungeon_release_time().isoformat()  # 修改为使用utils实例调用

            # 记录使用
            daily_dungeon[today][uid] = True

            # 写入数据
            with open(userdata_file, "w", encoding="utf-8") as f:
                json.dump(group_userdata, f, indent=4, ensure_ascii=False)
            with open(dungeon_data_file, "w", encoding="utf-8") as f:
                json.dump(dungeon_data, f, indent=4, ensure_ascii=False)
            with open(daily_dungeon_file, "w", encoding="utf-8") as f:
                json.dump(daily_dungeon, f, indent=4, ensure_ascii=False)

            await bot.send(event, f"【{user_name}】把自己关进了地牢，3小时后自动释放")
            return

        # 检查目标是否已经在地牢中
        if utils.check_dungeon_time(target_id, dungeon_data):
            await bot.finish(event, f"{target_name}已经被关在地牢里了喵", at_sender=True)

        # 计算成功率（基于双方涩涩值）
        attacker_silver = group_userdata[uid]["silver"]
        defender_silver = group_userdata[target_id]["silver"]
        success_rate = attacker_silver / (attacker_silver + defender_silver) if (attacker_silver + defender_silver) > 0 else 0.5

        # 随机决定是否成功
        is_success = random.random() < success_rate

        if is_success:
            # 成功关进地牢
            group_userdata[target_id]["dungeon"] = "被关"
            dungeon_data[target_id] = utils.get_dungeon_release_time().isoformat()  # 修改为使用utils实例调用

            # 记录使用
            daily_dungeon[today][uid] = True

            # 写入数据
            with open(userdata_file, "w", encoding="utf-8") as f:
                json.dump(group_userdata, f, indent=4, ensure_ascii=False)
            with open(dungeon_data_file, "w", encoding="utf-8") as f:
                json.dump(dungeon_data, f, indent=4, ensure_ascii=False)
            with open(daily_dungeon_file, "w", encoding="utf-8") as f:
                json.dump(daily_dungeon, f, indent=4, ensure_ascii=False)

            await bot.send(event, f"【{user_name}】成功将【{target_name}】关进了地牢，3小时后自动释放")
        else:
            # 记录使用（即使失败也记录）
            daily_dungeon[today][uid] = True
            with open(daily_dungeon_file, "w", encoding="utf-8") as f:
                json.dump(daily_dungeon, f, indent=4, ensure_ascii=False)

            await bot.send(event, f"【{user_name}】试图将【{target_name}】关进地牢，但是失败了")

    except Exception as e:
        sv.logger.error(f"关地牢时出错: {type(e).__name__}: {e}")
        return


@sv.on_fullmatch("逃脱地牢")
async def escape_dungeon(bot, event: CQEvent):
    """逃脱地牢的响应器（每天限一次）"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        os.makedirs(group_data_path, exist_ok=True)

        # 文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        dungeon_data_file = os.path.join(group_data_path, "dungeon_data.json")
        escape_data_file = os.path.join(group_data_path, "escape_data.json")

        # 安全读取JSON文件
        def safe_read_json(file_path):
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        return json.loads(content) if content else {}
                except (json.JSONDecodeError, IOError):
                    return {}
            return {}

        # 读取数据
        group_userdata = safe_read_json(userdata_file)
        dungeon_data = safe_read_json(dungeon_data_file)
        escape_data = safe_read_json(escape_data_file)  # 读取逃脱记录

        # 检查用户是否有角色
        if uid not in group_userdata:
            await bot.finish(event, "你还没有角色喵", at_sender=True)

        # 检查用户是否在地牢中
        if uid not in dungeon_data or not group_userdata[uid].get("dungeon"):
            await bot.finish(event, "你没有被关在地牢里喵", at_sender=True)

        # 检查今日是否已尝试逃脱
        today = utils.get_today()
        if uid in escape_data and escape_data[uid] == today:
            await bot.finish(event, "你今天已经尝试过逃脱了喵", at_sender=True)

        # 获取用户昵称
        user_name = await utils.get_user_card(bot, int(gid), int(uid))

        # 计算逃脱概率（基于涩涩值）
        silver = group_userdata[uid]["silver"]
        escape_chance = min(0.3 + (silver / 1000), 0.9)  # 基础30% + 涩涩值加成，最高90%

        # 随机决定是否成功
        is_success = random.random() < escape_chance

        if is_success:
            # 逃脱成功
            group_userdata[uid]["dungeon"] = None
            del dungeon_data[uid]

            # 写入数据
            with open(userdata_file, "w", encoding="utf-8") as f:
                json.dump(group_userdata, f, indent=4, ensure_ascii=False)
            with open(dungeon_data_file, "w", encoding="utf-8") as f:
                json.dump(dungeon_data, f, indent=4, ensure_ascii=False)

            # 记录逃脱
            escape_data[uid] = today
            with open(escape_data_file, "w", encoding="utf-8") as f:
                json.dump(escape_data, f, indent=4, ensure_ascii=False)

            await bot.send(event, f"【{user_name}】成功逃脱了地牢！重获自由")
        else:
            # 逃脱失败，但记录尝试
            escape_data[uid] = today
            with open(escape_data_file, "w", encoding="utf-8") as f:
                json.dump(escape_data, f, indent=4, ensure_ascii=False)

            await bot.send(event, f"【{user_name}】试图逃脱地牢，但失败了...今天不能再尝试了")

    except Exception as e:
        sv.logger.error(f"逃脱地牢时出错: {type(e).__name__}: {e}")
        return

@sv.on_prefix("放生")
async def release_slave(bot, event: CQEvent) -> None:
    """主人放生星怒的响应器"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 获取目标用户
        at = await utils.get_at(event)
        if at == "寄":
            await bot.finish(event, "请指定要放生的目标", at_sender=True)
        target_id = at

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")
        master_data_file = os.path.join(group_data_path, "master_data.json")

        # 读取或初始化群用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        # 读取主人数据
        master_data = {}
        if os.path.exists(master_data_file):
            with open(master_data_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    master_data = json.loads(content)

        # 检查目标用户是否有主人关系
        if target_id not in master_data:
            await bot.finish(event, "对方不是任何人的星怒", at_sender=True)

        # 检查发起者是否是目标用户的主人
        if master_data[target_id]["master"] != uid:
            master_name = await utils.get_user_card(bot, int(gid), int(master_data[target_id]["master"]))
            await bot.finish(event, f"你不是她的主人", at_sender=True)

        # 获取用户昵称
        user_name = await utils.get_user_card(bot, int(gid), int(uid))
        target_name = await utils.get_user_card(bot, int(gid), int(target_id))

        # 更新用户数据
        if target_id in group_userdata:
            group_userdata[target_id]["master"] = "无"

        # 删除主人关系
        del master_data[target_id]

        # 写入数据
        with open(userdata_file, "w", encoding="utf-8") as f:
            json.dump(group_userdata, f, indent=4, ensure_ascii=False)

        with open(master_data_file, "w", encoding="utf-8") as f:
            json.dump(master_data, f, indent=4, ensure_ascii=False)

        await bot.send(event, f"【{user_name}】把星怒【{target_name}】放生了")

    except Exception as e:
        sv.logger.error(f"放生时出错: {type(e).__name__}: {e}")
        return

@sv.on_prefix(("状态查询", "查看状态"))
async def query_status(bot, event: CQEvent) -> None:
    """查询用户状态信息（基于涩涩值判断状态）"""
    try:
        if not (await utils.check_group_allow(str(event.group_id))):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 获取目标用户（默认为发送者自己）
        at = await utils.get_at(event)
        gid = str(event.group_id)
        target_id = at if at != "寄" else str(event.user_id)

        # 初始化群数据目录
        group_data_path = os.path.join(utils.data_path, gid)
        os.makedirs(group_data_path, exist_ok=True)

        # 安全读取JSON文件
        def safe_read_json(file_path):
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        return json.loads(content) if content else {}
                except (json.JSONDecodeError, IOError):
                    return {}
            return {}

        # 读取用户数据
        userdata_file = os.path.join(group_data_path, "userdata.json")
        group_userdata = safe_read_json(userdata_file)

        # 检查目标用户是否有角色
        if target_id not in group_userdata:
            # 获取用户昵称
            user_name = await utils.get_user_card(bot, int(gid), int(target_id))
            await bot.finish(event, f"{user_name}还没有加入impact喵，发送【玩援神】加入~", at_sender=True)

        # 获取用户数据
        user_data = group_userdata[target_id]
        user_name = await utils.get_user_card(bot, int(gid), int(target_id))
        user_type = user_data["type"]

        # 根据涩涩值判断状态
        silver = user_data.get("silver", 0)
        if silver == 0:
            status = "纯洁的雏"
        elif 0 < silver <= 100:
            status = "纯洁"
        elif 100 < silver <= 500:
            status = "涩情"
        else:
            status = "应当"

        # 获取当前使用的道具
        current_item = user_data.get("play", "无")

        # 当前地牢状态
        dungeon_status = "自由"
        dungeon_data_file = os.path.join(group_data_path, "dungeon_data.json")
        dungeon_data = safe_read_json(dungeon_data_file)
        if target_id in dungeon_data:
            release_time = datetime.fromisoformat(dungeon_data[target_id])
            if datetime.now() < release_time:
                remaining = release_time - datetime.now()
                remaining_hours = int(remaining.total_seconds() // 3600)
                remaining_minutes = int((remaining.total_seconds() % 3600) // 60)
                dungeon_status = f"地牢中（剩余{remaining_hours}小时{remaining_minutes}分钟）"

        # 检查身份状态（主人/仆从）
        identity_status = "无"
        master_data_file = os.path.join(group_data_path, "master_data.json")
        master_data = safe_read_json(master_data_file)

        # 检查是否是别人的主人
        is_master = any(
            data.get("master") == target_id and
            datetime.now() < datetime.fromisoformat(data["release_time"])
            for data in master_data.values()
        )

        # 检查是否有主人
        if target_id in master_data:
            release_time = datetime.fromisoformat(master_data[target_id]["release_time"])
            if datetime.now() < release_time:
                master_name = await utils.get_user_card(bot, int(gid), int(master_data[target_id]["master"]))
                remaining = release_time - datetime.now()
                remaining_hours = int(remaining.total_seconds() // 3600)
                remaining_minutes = int((remaining.total_seconds() % 3600) // 60)
                identity_status = f"{master_name}的星怒（剩余{remaining_hours}小时{remaining_minutes}分钟）"

        # 如果是别人的主人
        elif is_master:
            # 找出所有仆从
            slaves = [
                await utils.get_user_card(bot, int(gid), int(slave_id))
                for slave_id, data in master_data.items()
                if data.get("master") == target_id and
                   datetime.now() < datetime.fromisoformat(data["release_time"])
            ]
            if slaves:
                identity_status = f"{'、'.join(slaves)}的主人"

        # 处理注入值显示
        ejaculation = user_data.get("ejaculation", 0)
        if user_type == "吉吉":
            ejaculation_display = f"当前射出值: {abs(ejaculation)}ml"
        else:
            ejaculation_display = f"当前注入量: {ejaculation}ml"

        # 构造状态信息文本
        status_text = (
            f"状态: {status}\n"
            f"群友: {user_name}\n"
            f"类型: {user_type}\n"
            f"涩涩值: {silver}\n"
            f"{user_type}开发度: {user_data['development']}\n"
            f"{ejaculation_display}\n"
            f"当前使用道具: {current_item}\n"
            f"地牢状态: {dungeon_status}\n"
            f"身份: {identity_status}\n"
            f"最后更新: {user_data['last_update']}"
        )

        # 生成图片
        img_bytes = await txt_to_img.txt_to_img(status_text)
        await bot.send(event, MessageSegment.image(img_bytes))

    except Exception as e:
        sv.logger.error(f"状态查询时出错: {type(e).__name__}: {e}")
        return


@sv.on_fullmatch(("排行榜"))
async def development_rank(bot, event: CQEvent) -> None:
    """基于开发度的排行榜"""
    try:
        gid = str(event.group_id)
        uid = str(event.user_id)

        if not (await utils.check_group_allow(str(event.group_id))):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 检查群是否允许
        if not (await utils.check_group_allow(gid)):
            await bot.finish(event, utils.not_allow, at_sender=True)

        # 获取群数据路径
        group_data_path = os.path.join(utils.data_path, gid)
        if not os.path.exists(group_data_path):
            os.makedirs(group_data_path)

        # 用户数据文件路径
        userdata_file = os.path.join(group_data_path, "userdata.json")

        # 读取用户数据
        group_userdata = {}
        if os.path.exists(userdata_file):
            with open(userdata_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    group_userdata = json.loads(content)

        # 检查是否有足够数据
        if len(group_userdata) < 3:
            await bot.finish(event, "参与人数不足3人，无法生成排行榜喵", at_sender=True)

        # 按开发度排序
        sorted_users = sorted(
            group_userdata.items(),
            key=lambda x: x[1]["development"],
            reverse=True
        )

        # 获取前5名
        top5 = sorted_users[:5]

        # 获取当前用户排名
        user_rank = next(
            (i + 1 for i, (user_id, _) in enumerate(sorted_users) if user_id == uid),
            None
        )

        # 获取用户昵称
        async def get_user_name(qid):
            try:
                user_info = await bot.get_group_member_info(group_id=int(gid), user_id=int(qid))
                return user_info["card"] or user_info["nickname"]
            except:
                return str(qid)

        # 获取前5名的昵称和开发度
        top5_info = []
        for i, (user_id, data) in enumerate(top5, 1):
            name = await get_user_name(user_id)
            top5_info.append(f"{i}. {name} - {data['type']}开发度: {data['development']}")

        # 构造排行榜文本
        rank_text = "开发度排行榜\n\n"
        rank_text += "前五名:\n" + "\n".join(top5_info) + "\n\n"

        # 添加当前用户排名信息
        if user_rank:
            user_data = group_userdata[uid]
            rank_text += (
                f"你的排名: 第{user_rank}名\n"
                f"当前{user_data['type']}开发度: {user_data['development']}\n"
            )
        else:
            rank_text += "你还没有加入impact喵，发送【玩援神】加入~"

        # 生成图片
        img_bytes = await txt_to_img.txt_to_img(rank_text)
        await bot.send(event, MessageSegment.image(img_bytes))

    except Exception as e:
        sv.logger.error(f"生成开发度排行榜时出错: {type(e).__name__}: {e}")
        return

@sv.on_rex(r"^(开始银趴|关闭银趴|开启淫趴|禁止淫趴|开启银趴|禁止银趴)")
async def open_module(bot, event: CQEvent) -> None:
    """开关"""
    if not priv.check_priv(event, priv.ADMIN):
       await bot.finish(ev, '只有群管理才能开启或禁止银趴哦。', at_sender=True)
       return
    gid = str(event.group_id)
    command: str = event.message.extract_plain_text()
    if "开启" in command or "开始" in command:
        if gid in utils.groupdata:
            utils.groupdata[gid]["allow"] = True
        else:
            utils.groupdata.update({gid: {"allow": True}})
        utils.write_group_data()
        await bot.send(event, "功能已开启喵")
    elif "禁止" in command or "关闭" in command:
        if gid in utils.groupdata:
            utils.groupdata[gid]["allow"] = False
        else:
            utils.groupdata.update({gid: {"allow": False}})
        utils.write_group_data()
        await bot.send(event, "功能已禁用喵")


@sv.on_fullmatch(("淫趴介绍", "银趴介绍"))
async def yinpa_introduce(bot, event: CQEvent) -> None:
    """输出用法"""
    await bot.send(event, MessageSegment.image(await utils.plugin_usage()))

