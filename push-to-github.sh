#!/bin/bash
# TrailSnap studio GitHub 推送脚本

set -e

echo "=========================================="
echo "  TrailSnap studio - GitHub 推送工具"
echo "=========================================="
echo ""

# 检查是否提供了用户名
if [ -z "$1" ]; then
    echo "用法: ./push-to-github.sh <GitHub用户名> [私有仓库y/n]"
    echo ""
    echo "示例:"
    echo "  ./push-to-github.sh johndoe       # 创建公开仓库"
    echo "  ./push-to-github.sh johndoe y     # 创建私有仓库"
    echo ""
    exit 1
fi

USERNAME=$1
PRIVATE=${2:-n}
REPO_NAME="TrailSnap-studio"

if [ "$PRIVATE" = "y" ]; then
    PRIVATE_FLAG="--private"
    VISIBILITY="私有"
else
    PRIVATE_FLAG="--public"
    VISIBILITY="公开"
fi

echo "GitHub 用户名: $USERNAME"
echo "仓库名称: $REPO_NAME"
echo "仓库类型: $VISIBILITY"
echo ""

# 检查 gh CLI 是否安装
if command -v gh &> /dev/null; then
    echo "✓ GitHub CLI 已安装"
    echo ""
    
    # 检查是否已登录
    if ! gh auth status &> /dev/null; then
        echo "请先登录 GitHub CLI:"
        gh auth login
    fi
    
    echo "正在创建仓库并推送..."
    gh repo create "$REPO_NAME" $PRIVATE_FLAG --source=. --remote=origin --push
    
    echo ""
    echo "✓ 推送成功！"
    echo "仓库地址: https://github.com/$USERNAME/$REPO_NAME"
    
else
    echo "ℹ GitHub CLI 未安装，使用手动方式..."
    echo ""
    
    # 设置远程仓库
    REMOTE_URL="https://github.com/$USERNAME/$REPO_NAME.git"
    
    # 检查远程仓库是否已存在
    if git remote get-url origin &> /dev/null; then
        echo "更新远程仓库地址..."
        git remote set-url origin "$REMOTE_URL"
    else
        echo "添加远程仓库..."
        git remote add origin "$REMOTE_URL"
    fi
    
    echo ""
    echo "=========================================="
    echo "  请按以下步骤操作："
    echo "=========================================="
    echo ""
    echo "1. 在浏览器中创建仓库:"
    echo "   https://github.com/new"
    echo ""
    echo "   仓库名称: $REPO_NAME"
    echo "   描述: TrailSnap - 智能照片管理与票据识别系统"
    echo "   类型: $([ "$PRIVATE" = "y" ] && echo '私有' || echo '公开')"
    echo ""
    echo "2. 创建后运行以下命令推送代码:"
    echo ""
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    echo "或者一键推送:"
    echo "   git push -u https://github.com/$USERNAME/$REPO_NAME.git main"
    echo ""
fi
