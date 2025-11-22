FROM ubuntu:20.04

# 设置工作目录
WORKDIR /app

# 安装必要的工具和依赖
RUN apt-get update -y && \
    apt-get install -y gcc python3 python3-pip nodejs npm curl wget && \
    apt-get clean

# 复制前端和后端代码
COPY ./front ./front
COPY ./backend ./backend

# 在前端目录中安装Node.js依赖并构建
WORKDIR /app/front
RUN npm install
RUN npm run build

# 将构建后的dist文件夹移动到后端目录下
WORKDIR /app
RUN mv front/dist backend/dist

# 切换到后端目录，安装Python依赖项
WORKDIR /app/backend
RUN pip3 install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python3", "app.py"]
