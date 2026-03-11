# TrailSnap 前端服务 Dockerfile (开发模式)
# 用于开发环境，支持热重载

FROM node:20-alpine

# 设置工作目录
WORKDIR /app

# 安装 pnpm（可选，更快）
RUN npm install -g pnpm

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 3000

# 启动开发服务器
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
