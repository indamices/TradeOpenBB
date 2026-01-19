# ==========================================
# 阶段 1: 构建器
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# 复制包文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# ==========================================
# 阶段 2: 运行时 (nginx)
# ==========================================
FROM nginx:alpine

# 从构建器复制构建资源
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
