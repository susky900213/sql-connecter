#!/bin/bash

# 构建SQL连接器应用的Docker镜像
echo "开始构建Docker镜像..."

# 构建镜像
docker build -t sql-connecter-app .

if [ $? -eq 0 ]; then
    echo "✅ Docker镜像构建成功!"
    echo "镜像名称: sql-connecter-app"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi

# 显示构建的镜像信息
echo ""
echo "已构建的镜像:"
docker images | grep sql-connecter-app
