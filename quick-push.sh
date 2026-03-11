#!/bin/bash
# TrailSnap studio 一键推送脚本

echo "========================================"
echo "  TrailSnap studio - GitHub 推送"
echo "========================================"
echo ""
echo "GitHub 用户: gyj-0"
echo "仓库名称: TrailSnap-studio"
echo "仓库地址: https://github.com/gyj-0/TrailSnap-studio"
echo ""

# 检查 gh CLI
if command -v gh &> /dev/null; then
    echo "✓ GitHub CLI 已安装"
    
    # 检查登录状态
    if gh auth status &> /dev/null; then
        echo "✓ 已登录 GitHub"
        echo ""
        read -p "是否创建并推送仓库? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            gh repo create TrailSnap-studio --public --source=. --remote=origin --push
            echo ""
            echo "✓ 推送成功!"
            echo "访问: https://github.com/gyj-0/TrailSnap-studio"
            exit 0
        fi
    else
        echo "✗ 未登录 GitHub"
        echo "运行: gh auth login"
    fi
else
    echo "ℹ GitHub CLI 未安装"
fi

echo ""
echo "========================================"
echo "  手动推送步骤:"
echo "========================================"
echo ""
echo "方法 1 - 使用 HTTPS + Token:"
echo "  1. 访问 https://github.com/settings/tokens 生成 token"
echo "  2. 运行: git push -u origin main"
echo "  3. 用户名: gyj-0"
echo "  4. 密码: 输入你的 Personal Access Token"
echo ""
echo "方法 2 - 先在 GitHub 创建仓库:"
echo "  1. 访问 https://github.com/new"
echo "  2. 填写 Repository name: TrailSnap-studio"
echo "  3. 点击 Create repository"
echo "  4. 运行: git push -u origin main"
echo ""

read -p "是否现在执行 git push? (y/n): " dopush
if [ "$dopush" = "y" ]; then
    git push -u origin main
fi
