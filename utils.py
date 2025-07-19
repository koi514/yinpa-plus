import json
import os
import random
import time

from hoshino.typing import CQEvent
from .txt2img import txt_to_img
from datetime import datetime, timedelta


class Utils:
    def __init__(self) -> None:
        """初始化数据路径和配置文件"""
        _dir = os.path.dirname(__file__)
        self.data_path: str = os.path.join(_dir, "data/impact")
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        # 初始化群组数据
        self.groupdata = {}
        self.groupdata_file = os.path.join(self.data_path, "groupdata.json")
        if os.path.exists(self.groupdata_file):
            with open(self.groupdata_file, "r", encoding="utf-8") as f:
                self.groupdata = json.load(f)

        # 初始化用户数据
        self.userdata_file = os.path.join(self.data_path, "userdata.json")
        self.userdata = {}
        if os.path.exists(self.userdata_file):
            with open(self.userdata_file, "r", encoding="utf-8") as f:
                self.userdata = json.load(f)

        # 初始化冷却数据
        self.cd_data = {}
        self.pk_cd_data = {}
        self.suo_cd_data = {}
        self.play_hard_cd_data = {}
        # 配置信息
        config_file = os.path.join(_dir, "config.json")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.dj_cd_time: int = config.get("djcdtime", 1800)
        self.pk_cd_time: int = config.get("pkcdtime", 1800)
        self.suo_cd_time: int = config.get("suocdtime", 1800)
        self.play_hard_cd_time = config.get("playhardcdtime", 10800)

        self.not_allow = "群内还未开启银趴游戏, 请管理员或群主发送\"开启银趴\", \"禁止银趴\"以开启/关闭该功能"

    def get_dungeon_release_time(self, hours=3):
        """获取地牢释放时间（当前时间+指定小时）"""
        return datetime.now() + timedelta(hours=hours)

    def get_master_release_time(self, hours=24):
        """获取主人关系解除时间（当前时间+指定小时）"""
        return datetime.now() + timedelta(hours=hours)

    def check_dungeon_time(self, uid, dungeon_data):
        """检查地牢状态是否还在有效期内"""
        if uid in dungeon_data:
            release_time = datetime.fromisoformat(dungeon_data[uid])
            return datetime.now() < release_time
        return False

    def check_master_time(self, uid, master_data):
        """检查主人关系是否还在有效期内"""
        if uid in master_data:
            release_time = datetime.fromisoformat(master_data[uid]["release_time"])
            return datetime.now() < release_time
        return False

    async def play_hard_cd_check(self, uid: str) -> bool:
        """检查使劲玩弄冷却时间"""
        cd = time.time() - self.play_hard_cd_data.get(uid, 0)
        return cd > self.play_hard_cd_time

    def write_user_data(self) -> None:
        """写入用户数据"""
        with open(self.userdata_file, "w", encoding="utf-8") as f:
            json.dump(self.userdata, f, indent=4, ensure_ascii=False)
            
    def write_group_data(self) -> None:
        """写入群配置"""
        with open(f"{self.data_path}/groupdata.json", "w", encoding="utf-8") as f:
            json.dump(self.groupdata, f, indent=4, ensure_ascii=False)

    def get_current_week(self) -> str:
        """获取当前是第几周"""
        return time.strftime("%W", time.localtime())

    def get_today(self) -> str:
        """获取当前年月日 格式: 2023-02-04"""
        return time.strftime("%Y-%m-%d", time.localtime())

    async def get_at(self, event: CQEvent) -> str:
        """获取at的qq号, 不存在则返回'寄'"""
        msg = event.message
        return next(
            (
                "寄" if msg_seg.data["qq"] == "all" else str(msg_seg.data["qq"])
                for msg_seg in msg
                if msg_seg.type == "at"
            ),
            "寄",
        )

    async def check_group_allow(self, gid: str) -> bool:
        """检查群是否允许使用功能"""
        return self.groupdata.get(gid, {}).get("allow", False)

    async def pkcd_check(self, uid: str) -> bool:
        """检查PK冷却时间"""
        cd = time.time() - self.pk_cd_data.get(uid, 0)
        return cd > self.pk_cd_time

    async def suo_cd_check(self, uid: str) -> bool:
        """检查嗦冷却时间"""
        cd = time.time() - self.suo_cd_data.get(uid, 0)
        return cd > self.suo_cd_time

    async def get_user_card(self, bot, group_id: int, qid: int) -> str:
        """获取用户群名片或昵称"""
        user_info: dict = await bot.get_group_member_info(group_id=group_id, user_id=qid)
        return user_info.get("card") or user_info.get("nickname", str(qid))

    async def plugin_usage(self) -> bytes:
        """生成插件使用说明图片"""
        usage = """银趴游戏使用说明:

指令1: 玩援神 (加入impact游戏)
指令2: 强健 @目标 (与目标进行涩涩)
指令3: 鹿 (吉吉专用)
指令4: 扣 (肖雪专用)
指令5: 开嗦 @目标 (对目标进行涩涩)
指令6: 使劲玩弄 (高强度自娱自乐，12小时CD)
指令7: 重开 (重置数据,每周限一次)
指令8: 状态查询/查看状态 @目标 (查询状态)
指令9: 排行榜 (查看排名)
指令10: 开启银趴/关闭银趴 (管理员指令,开关功能)
指令11: 使用玩具/取下玩具 道具名 @目标(使用或取出小道具)
指令12: 黑暗游戏 @目标 (进行黑暗游戏，3天CD，越涩越容易赢)
指令13: 关地牢里 @目标 (将目标关入地牢3小时，60%概率)
指令14: 逃脱地牢 (尝试逃脱地牢，每天限一次)
指令15: 放生 @目标 (放生星怒)"""

        return await txt_to_img.txt_to_img(usage)


utils = Utils()