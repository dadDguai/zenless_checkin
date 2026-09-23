import os
import sys
from loguru import logger
from zenless import ZenlessTask
from push import format_push_message, send_to_email


class BeijingFormatter:
    @staticmethod
    def format(record):
        from datetime import datetime, timedelta, timezone
        dt = datetime.fromtimestamp(record["time"].timestamp(), tz=timezone.utc)
        local_dt = dt + timedelta(hours=8)
        record["extra"]["local_time"] = local_dt.strftime('%H:%M:%S,%f')[:-3]
        return "{time:YYYY-MM-DD HH:mm:ss,SSS}(CST {extra[local_time]}) - {level} - {message}\n"


logger.remove()
logger.add(sys.stdout, format=BeijingFormatter.format, level="INFO", colorize=True)


def mask_string(s):
    if not isinstance(s, str) or len(s) == 0:
        return '*'
    return s[0] + '*' * (len(s) - 1)


def main():
    cookie = os.environ.get('MIHOYO_COOKIE')
    if not cookie:
        logger.error('环境变量 MIHOYO_COOKIE 未设置，程序终止')
        sys.exit(1)

    # 可选配置，均有默认值
    act_id = os.environ.get('ACT_ID') or None
    game_id = os.environ.get('GAME_ID') or None
    region = os.environ.get('REGION') or None

    logger.info("开始执行绝区零社区签到...")
    zzz = ZenlessTask(cookie, act_id=act_id, game_id=game_id, region=region)

    # 1. 获取用户信息
    user_info = zzz.get_user_info()
    if not user_info:
        logger.error('获取用户信息失败，Cookie 可能无效或已过期')
        any_failed = True
        result = {'user_info': None, 'sign_info': None, 'tasks': {'登录检查': (False, 'Cookie失效或网络问题')}}
    else:
        masked_nickname = mask_string(user_info.get('nickname'))
        logger.info(f"米游社昵称: {masked_nickname}")
        any_failed = False
        result = {'user_info': user_info, 'sign_info': None, 'tasks': {}}

        # 2. 获取绝区零游戏角色
        roles = zzz.get_game_roles()
        if not roles:
            logger.error('未找到绝区零游戏角色，请确认该账号已绑定绝区零游戏')
            result['tasks']['获取角色'] = (False, '未绑定绝区零游戏角色')
            any_failed = True
        else:
            role = roles[0]
            uid = role.get('uid')
            role_region = role.get('region') or region or zzz.region
            level = role.get('level', '?')
            nickname = role.get('nickname', '?')
            logger.info(f"绝区零角色: {nickname} (Lv.{level}), UID: {mask_string(str(uid))}, 区服: {role_region}")

            # 3. 查询签到状态
            sign_info = zzz.get_sign_info(uid, role_region)
            result['sign_info'] = sign_info

            # 4. 执行签到
            logger.info("开始签到...")
            success, msg = zzz.sign(uid, role_region)
            if success:
                logger.info(f"[签到] 成功: {msg}")
            else:
                logger.warning(f"[签到] {msg}")
            result['tasks']['社区签到'] = (success, msg)

            # 5. 签到后再次查询状态
            after_sign_info = zzz.get_sign_info(uid, role_region)
            if after_sign_info:
                result['sign_info'] = after_sign_info
                logger.info(f"本月累计签到: {after_sign_info.get('total')} 天")
                if after_sign_info.get('miss', 0) > 0:
                    logger.warning(f"本月漏签: {after_sign_info.get('miss')} 天")

    # 6. 推送 QQ 邮箱
    if os.environ.get('SMTP_QQ_EMAIL') and os.environ.get('SMTP_QQ_AUTHCODE'):
        logger.info('准备发送 QQ 邮箱邮件...')
        title = "米游社绝区零签到通知"
        content = format_push_message(result)
        send_to_email(title, content)
    else:
        logger.info('未配置 SMTP_QQ_EMAIL/SMTP_QQ_AUTHCODE，跳过邮件推送。')

    # 7. 输出结果
    if any_failed:
        logger.error("任务执行失败！")
        sys.exit(1)
    else:
        logger.info("任务执行完成！")
        sys.exit(0)


if __name__ == '__main__':
    main()
