# Docker镜像构建命令

## 基本构建命令
docker build -t sql-connecter-app .

## 带详细输出的构建命令
docker build -t sql-connecter-app . --no-cache

## 构建并指定构建上下文
docker build -f Dockerfile -t sql-connecter-app .

## 构建后查看镜像
docker images | grep sql-connecter-app

## 运行容器（示例）
docker run -p 5000:5000 sql-connecter-app
