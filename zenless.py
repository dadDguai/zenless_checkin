import hashlib
import random
import string
import time
import uuid
import requests
from loguru import logger

# ============ 绝区零签到配置（国服） ============
# 参考自 Womsxd/MihoyoBBSTools 开源项目（已验证）
DEFAULT_ACT_ID = 'e202406242138391'      # 绝区零国服签到活动ID
DEFAULT_GAME_ID = 'nap_cn'               # 米游社游戏ID（绝区零）
DEFAULT_REGION = 'prod_gf_cn'            # 国服区
ZZZ_SIGN_BASE = 'https://act-nap-api.mihoyo.com'   # 绝区零专用签到域名

# 米游社 web 版 salt（用于 DS 签名，参考自 MihoyoBBSTools）
MIHOYO_SALT_WEB = 'd9200c846b10886e8c874fc33c8f308b'
# 米游社版本
MIHOYO_VERSION = '2.11.1'


def md5(text):
    return hashlib.md5(text.encode()).hexdigest()


def random_text(num):
    return ''.join(random.sample(string.ascii_lowercase + string.digits, num))


def get_ds(web=True):
    """生成米游社 DS 签名（web 版）"""
    salt = MIHOYO_SALT_WEB
    t = str(int(time.time()))
    r = random_text(6)
    c = md5(f'salt={salt}&t={t}&r={r}')
    return f"{t},{r},{c}"


def get_device_id(cookie):
    """用 cookie 通过 uuid3 生成设备 ID"""
    return str(uuid.uuid3(uuid.NAMESPACE_URL, cookie))


class ZenlessTask:
    def __init__(self, cookie, act_id=None, game_id=None, region=None):
        self.cookie = cookie
        self.act_id = act_id or DEFAULT_ACT_ID
        self.game_id = game_id or DEFAULT_GAME_ID
        self.region = region or DEFAULT_REGION
        self.device_id = get_device_id(cookie)

    def _headers(self, extra=None):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Origin': 'https://act.mihoyo.com',
            'Referer': 'https://act.mihoyo.com/',
            'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          f'(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 miHoYoBBS/{MIHOYO_VERSION}',
            'x-rpc-app_version': MIHOYO_VERSION,
            'x-rpc-client_type': '5',
            'x-rpc-channel': 'miyousheluodi',
            'x-rpc-device_id': self.device_id,
            'X-Rpc-Signgame': 'zzz',
            'DS': get_ds(web=True),
            'Cookie': self.cookie,
        }
        if extra:
            headers.update(extra)
        return headers

    def get_game_roles(self):
        """获取绝区零游戏角色（含 uid 和 region）"""
        url = f'https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie?game_biz={self.game_id}'
        try:
            res = requests.get(url, headers=self._headers(), timeout=15)
            res.raise_for_status()
            data = res.json()
            if data.get('retcode') == 0:
                roles = data.get('data', {}).get('list', [])
                if roles:
                    return roles
            logger.warning(f"获取游戏角色失败: {data.get('message')}")
            return []
        except Exception as e:
            logger.error(f"请求游戏角色API异常: {e}")
            return []

    def get_sign_info(self, uid, region=None):
        """查询本月签到状态"""
        region = region or self.region
        url = f'{ZZZ_SIGN_BASE}/event/luna/zzz/info'
        params = {'lang': 'zh-cn', 'act_id': self.act_id, 'region': region, 'uid': uid}
        try:
            res = requests.get(url, headers=self._headers(), params=params, timeout=15)
            res.raise_for_status()
            data = res.json()
            if data.get('retcode') == 0:
                d = data.get('data', {})
                return {
                    'total': d.get('total_sign_day', 0),
                    'today': d.get('is_sign', False),
                    'month': d.get('month', ''),
                    'miss': d.get('sign_cnt_missed', 0),
                }
            logger.warning(f"查询签到状态失败: {data.get('message')}")
            return None
        except Exception as e:
            logger.error(f"请求签到状态API异常: {e}")
            return None

    def sign(self, uid, region=None):
        """执行签到"""
        region = region or self.region
        url = f'{ZZZ_SIGN_BASE}/event/luna/zzz/sign'
        payload = {'act_id': self.act_id, 'region': region, 'uid': uid}
        try:
            res = requests.post(url, headers=self._headers(), json=payload, timeout=15)
            res.raise_for_status()
            resp = res.json()
            retcode = resp.get('retcode')
            message = resp.get('message', '')
            if retcode == 0:
                return True, "签到成功"
            if retcode == -5003:
                return False, "今天已经签过到了"
            return False, f"签到失败: {message}"
        except Exception as e:
            return False, f"请求签到API异常: {e}"
