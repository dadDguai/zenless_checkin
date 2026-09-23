import requests
from loguru import logger

# 米游社绝区零社区签到
# act_id 从官方签到页面 URL 确认: https://act.hoyolab.com/bbs/event/signin/zzz/e202406031448091.html
DEFAULT_ACT_ID = 'e202406031448091'   # 绝区零国服签到活动 ID
DEFAULT_GAME_ID = '4'                 # 绝区零
DEFAULT_REGION = 'prod_gf_cn'         # 国服

class ZenlessTask:
    def __init__(self, cookie, act_id=None, game_id=None, region=None):
        self.cookie = cookie
        self.act_id = act_id or DEFAULT_ACT_ID
        self.game_id = game_id or DEFAULT_GAME_ID
        self.region = region or DEFAULT_REGION
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://act.mihoyo.com/',
            'Origin': 'https://act.mihoyo.com',
            'x-rpc-app_version': '2.11.1',
            'x-rpc-client_type': '5',
            'Cookie': cookie,
        }

    def get_user_info(self):
        """获取米游社用户信息"""
        url = 'https://api-takumi.mihoyo.com/account/auth/api/getUserInfoByUni'
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            res.raise_for_status()
            data = res.json()
            if data.get('retcode') == 0:
                info = data.get('data', {}).get('user_info', {})
                return {
                    'nickname': info.get('nickname'),
                    'uid': info.get('uid'),
                }
            logger.warning(f"获取用户信息失败: {data.get('message')}")
            return None
        except Exception as e:
            logger.error(f"请求用户信息API异常: {e}")
            return None

    def get_game_roles(self):
        """获取绝区零游戏角色（含 uid 和 region）"""
        url = f'https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie?game_biz=zzz_cn&game_region={self.region}'
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
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
        url = 'https://api-takumi.mihoyo.com/event/bbs_sign_reward/info'
        params = {
            'act_id': self.act_id,
            'region': region,
            'uid': uid,
        }
        try:
            res = requests.get(url, headers=self.headers, params=params, timeout=15)
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
        url = 'https://api-takumi.mihoyo.com/event/bbs_sign_reward/sign'
        params = {'act_id': self.act_id, 'region': region, 'uid': uid}
        data = {'act_id': self.act_id}
        try:
            res = requests.post(url, headers=self.headers, params=params, json=data, timeout=15)
            res.raise_for_status()
            resp = res.json()
            retcode = resp.get('retcode')
            message = resp.get('message', '')
            # retcode 0 = 成功, -5003 = 今天已签到, -100 = 需要登录
            if retcode == 0:
                return True, "签到成功"
            if retcode == -5003:
                return False, "今天已经签过到了"
            return False, f"签到失败: {message}"
        except Exception as e:
            return False, f"请求签到API异常: {e}"
