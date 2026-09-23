import smtplib
import os
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta, timezone
from loguru import logger


def format_push_message(result):
    """格式化签到结果报告（单账号）"""
    content = ["### 米游社绝区零签到报告\n"]

    user_info = result.get('user_info')
    sign_info = result.get('sign_info', {})

    if user_info:
        nickname = user_info.get('nickname')
        level = user_info.get('level')
        uid = user_info.get('uid')
        role_line = f"{nickname}"
        if level:
            role_line += f" (Lv.{level})"
        if uid:
            role_line += f" UID:{uid}"
        content.append(f"- **绝区零角色**: {role_line}")
    if sign_info:
        content.append(f"- **本月累计签到**: {sign_info.get('total', 0)} 天")
        content.append(f"- **今日已签到**: {'是' if sign_info.get('today') else '否'}")

    content.append("")
    for name, (success, message) in result['tasks'].items():
        status_icon = "✅" if success else "❌"
        reason = f" - {message}" if message else ""
        content.append(f"- **{name}**: {status_icon}{reason}")

    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    content.append(f"\n> 报告时间: {beijing_time}")

    return "\n".join(content)


def send_to_email(title, content, sender=None, authcode=None, receiver=None, smtp_server='smtp.qq.com', smtp_port=465):
    """通过 SMTP 发送邮件（默认 QQ 邮箱，支持授权码）。

    配置通过环境变量读取（GitHub Actions Secret）：
      SMTP_QQ_EMAIL     发件邮箱地址
      SMTP_QQ_AUTHCODE  发件邮箱 SMTP 授权码（16位）
      SMTP_TO_EMAIL     收件邮箱地址
      SMTP_SERVER       SMTP 服务器，默认 smtp.qq.com
      SMTP_PORT         SMTP 端口，默认 465
    """
    sender = sender or os.environ.get('SMTP_QQ_EMAIL')
    authcode = authcode or os.environ.get('SMTP_QQ_AUTHCODE')
    receiver = receiver or os.environ.get('SMTP_TO_EMAIL')
    smtp_server = os.environ.get('SMTP_SERVER') or smtp_server
    try:
        smtp_port = int(os.environ.get('SMTP_PORT') or smtp_port)
    except ValueError:
        smtp_port = 465

    if not sender or not authcode or not receiver:
        logger.error("邮件配置不完整：缺少 SMTP_QQ_EMAIL / SMTP_QQ_AUTHCODE / SMTP_TO_EMAIL，跳过邮件发送")
        return False

    plain_content = content.replace('### ', '').replace('#### ', '')
    msg = MIMEText(plain_content, 'plain', 'utf-8')
    msg['From'] = formataddr((str(Header('绝区零签到', 'utf-8')), sender))
    msg['To'] = receiver
    msg['Subject'] = Header(title, 'utf-8')

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=15)
            server.starttls()
        server.login(sender, authcode)
        server.sendmail(sender, [receiver], msg.as_string())
        server.quit()
        logger.info(f'邮件发送成功 → {receiver}')
        return True
    except Exception as e:
        logger.error(f'邮件发送异常: {e}')
        return False
