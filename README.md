# zenless_checkin

米游社**绝区零（Zenless Zone Zero）社区每日签到**脚本，自动领取菲林等签到奖励。通过 GitHub Actions 定时运行，无需开电脑，签到结果推送到你的 **QQ 邮箱**。

## 功能
- ✅ 米游社**绝区零社区每日签到**，自动领取菲林、丁尼等奖励
- ✅ 自动获取绝区零游戏角色（角色名、UID、区服）
- ✅ 自动查询签到状态、本月累计签到天数
- ✅ 签到时间随机化（避免固定时间被风控）
- ✅ 通过 **QQ 邮箱** 推送签到结果
- ✅ 基于 GitHub Actions 每日定时自动运行（无需开电脑）

## 使用方法

### 1. Fork 本项目到你的 GitHub 仓库

### 2. 配置 GitHub Secrets

在仓库 `Settings -> Secrets and variables -> Actions` 中添加：

| Secret 名称 | 是否必需 | 说明 |
|---|---|---|
| `MIHOYO_COOKIE` | **是** | 米游社 Cookie（获取方法见下方） |
| `SMTP_QQ_EMAIL` | **否** | 发件 QQ 邮箱（用于推送结果） |
| `SMTP_QQ_AUTHCODE` | **否** | QQ 邮箱 SMTP 授权码（16位） |
| `SMTP_TO_EMAIL` | **否** | 收件邮箱（发给自己填同一个） |

可选的高级配置（有默认值，一般无需设置）：

| Secret 名称 | 说明 | 默认值 |
|---|---|---|
| `ACT_ID` | 签到活动 ID | `e202406242138391` |
| `GAME_ID` | 游戏 ID | `nap_cn` |
| `REGION` | 区服 | `prod_gf_cn` |
| `RANDOM_DELAY_MAX` | 随机等待最大分钟数 | `30` |

### 3. 启用 GitHub Actions

Fork 的仓库默认关闭 workflow，需手动开启。手动触发一次后即启用定时任务。

### 4. 定时执行

- 默认每天 **北京时间 10:30 ~ 11:00 之间随机** 自动签到
- workflow 在 10:30 触发，脚本内随机等待 0~30 分钟后执行签到
- 可通过 `RANDOM_DELAY_MAX` 调整随机范围（设为 `0` 则立即执行）
- 如需修改时间，编辑 `.github/workflows/Zenless_DailyCheckin.yml` 中的 cron 表达式（注意是 UTC 时间）

## 米游社 Cookie 获取

1. 浏览器登录 [米游社](https://www.miyoushe.com/)
2. 打开开发者工具（F12）→ 网络（Network）
3. 找到任意请求，查看请求头中的 `Cookie`
4. 复制完整的 Cookie 值，填入 `MIHOYO_COOKIE`

> Cookie 需包含 `account_id` 和 `ltoken`（或 `cookie_token`）字段才有效。

## 执行结果查看
- 在 Actions 页面查看执行日志
- 若配置了 QQ 邮箱推送，签到结果会发到你的邮箱

## 注意事项
- 每日签到奖励一天只能领一次
- Cookie 失效（改密码、退出登录）会导致签到失败，需更新
- 请勿泄露你的 Cookie，以防账号被盗
- 本项目仅供学习交流使用

## 许可证
MIT License
