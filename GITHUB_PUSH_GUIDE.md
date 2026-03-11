# TrailSnap studio - GitHub 推送指南

## 🚀 快速推送

### 方式 1：使用 GitHub CLI（推荐）

```bash
# 安装 GitHub CLI
# macOS: brew install gh
# Ubuntu: sudo apt install gh

# 登录
gh auth login

# 创建仓库并推送
gh repo create TrailSnap-studio --public --source=. --push
```

### 方式 2：使用 HTTPS + Personal Access Token

```bash
# 1. 生成 Personal Access Token
# 访问: https://github.com/settings/tokens
# 点击 "Generate new token (classic)"
# 选择权限: repo

# 2. 推送（会提示输入 token 作为密码）
git push -u origin main

# 用户名: gyj-0
# 密码: <你的 Personal Access Token>
```

### 方式 3：使用 SSH

```bash
# 1. 生成 SSH 密钥（如果还没有）
ssh-keygen -t ed25519 -C "your@email.com"

# 2. 添加公钥到 GitHub
# 访问: https://github.com/settings/keys
# 点击 "New SSH key"
# 复制 ~/.ssh/id_ed25519.pub 内容

# 3. 修改远程仓库为 SSH
git remote set-url origin git@github.com:gyj-0/TrailSnap-studio.git

# 4. 推送
git push -u origin main
```

## 📋 推送前检查清单

- [ ] GitHub 账号已登录
- [ ] 仓库 `TrailSnap-studio` 已创建（或不存在，会自动创建）
- [ ] 有推送权限
- [ ] 代码已提交

## 🔧 当前状态

```bash
cd /home/gyjgyj/TrailSnap
git status
```

## 📤 一键推送命令

```bash
cd /home/gyjgyj/TrailSnap && git push -u origin main
```

## 🆘 常见问题

### 1. 仓库已存在
```bash
# 如果仓库已存在，直接推送
git push -u origin main
```

### 2. 权限被拒绝
```bash
# 检查远程仓库地址
git remote -v

# 重新设置
git remote set-url origin https://github.com/gyj-0/TrailSnap-studio.git
```

### 3. 需要创建仓库
访问: https://github.com/new
- Repository name: `TrailSnap-studio`
- Description: `TrailSnap - 智能照片管理与票据识别系统`
- Visibility: Public 或 Private
- 不勾选 "Add a README file"（已有 README）

## ✨ 推送后

推送成功后，访问: **https://github.com/gyj-0/TrailSnap-studio**

查看你的项目！
