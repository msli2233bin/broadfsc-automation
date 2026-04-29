# Threads OAuth Token 获取指南

## 当前状态
- ✅ Threads App 已创建（App ID: 1479983126925807）
- ✅ 测试帖已发成功（@msli637）
- ✅ 代码已就绪（threads_poster.py 已集成到 social_poster.py）
- ⏳ **待完成：获取长期 Access Token（60天有效期）**

## 为什么需要长期 Token？
- Meta 后台"用户口令生成器"生成的 Token 只有 1-2 小时有效
- 长期 Token 有效 60 天，可通过 API 自动续期
- 自动化系统需要长期 Token 才能稳定运行

## 获取步骤（5分钟完成）

### 第1步：打开授权链接
在浏览器（已登录 @msli637 的 Threads 账号）打开：

```
https://www.threads.net/oauth/authorize?client_id=1479983126925807&redirect_uri=https://www.broadfsc.com/&scope=threads_basic,threads_content_publish&response_type=code
```

### 第2步：点击"授权"
页面会显示授权请求，点击"允许/Authorize"

### 第3步：复制 code
授权后浏览器跳转到 broadfsc.com，地址栏变成：
```
https://www.broadfsc.com/?code=AQXXXXXXXXXX...
```
复制 `code=` 后面的完整字符串

### 第4步：运行 Token 交换脚本
在 PowerShell 运行：
```powershell
cd c:\Users\Administrator\WorkBuddy\20260414140743\broadfsc-automation
python get_threads_token_oauth.py
```
粘贴 code，脚本自动完成：
1. 用 code 换短期 Token
2. 用短期 Token 换长期 Token（60天）
3. 保存到 threads_token.txt 和 .env

### 第5步：设置 GitHub Secrets
获取到长期 Token 后，在 GitHub 仓库设置：
- `THREADS_ACCESS_TOKEN` = 长期 Token 值
- `THREADS_USER_ID` = 35426966120283926

完成后，Threads 自动发帖功能即完全上线！

## Token 续期
长期 Token 每60天需续期一次，运行：
```powershell
cd c:\Users\Administrator\WorkBuddy\20260414140743\broadfsc-automation
python threads_poster.py refresh-token
```

## 故障排除
- 如果授权链接报错"应用编号未发送"：检查 App ID 是否正确
- 如果 code 换 Token 失败：code 只能用一次，需重新授权
- 如果长期 Token 过期：重新从第1步开始
