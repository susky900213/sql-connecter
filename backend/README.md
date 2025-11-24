# MySQL Management API

这是一个用于管理多个MySQL数据库连接的后端API服务。

## 功能特性

- 管理多个MySQL数据库连接配置
- 添加、删除、更新数据库连接
- 测试数据库连接
- 查看数据库中的所有表
- 查看特定表的结构信息
- 执行SQL语句（支持SELECT和非SELECT语句）
- CSV文件批量导入数据（支持事务处理，每批最多50条记录）

## 项目结构

```
backend/
├── __init__.py
├── app.py              # Flask应用主入口
├── database_manager.py # 数据库管理逻辑
├── config.json         # 数据库配置文件（JSON格式）
├── requirements.txt    # Python依赖包列表
└── API_DOCUMENTATION.md # API接口文档
```

## 安装和运行

### 1. 环境要求

- Python 3.6+
- pip

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 运行应用

```bash
python app.py
```

服务将运行在 `http://localhost:5000`

## 使用说明

1. 首先添加数据库连接配置：
   ```bash
   curl -X POST http://localhost:5000/api/databases \
     -H "Content-Type: application/json" \
     -d '{
       "name": "mydb",
       "host": "localhost",
       "port": 3306,
       "database": "testdb",
       "user": "root",
       "password": "password"
     }'
   ```

2. 查看所有数据库配置：
   ```bash
   curl http://localhost:5000/api/databases
   ```

3. 获取特定数据库中的表列表：
   ```bash
   curl http://localhost:5000/api/databases/mydb/tables
   ```

4. 执行SQL语句：
   ```bash
   curl -X POST http://localhost:5000/api/databases/mydb/execute \
     -H "Content-Type: application/json" \
     -d '{
       "sql": "SELECT * FROM users LIMIT 10"
     }'
   ```

## API文档

完整的API接口文档请查看 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 配置文件说明

配置信息存储在 `config.json` 文件中，格式如下：
```json
{
  "databases": [
    {
      "name": "string",
      "host": "string",
      "port": integer,
      "database": "string", 
      "user": "string",
      "password": "string"
    }
  ]
}
```

## 注意事项

- 密码信息会以明文形式存储在配置文件中
- 建议根据实际需要添加认证和安全措施

## 调试说明

为了在VSCode中方便地调试此项目，已创建了以下调试配置：

1. 在`.vscode/launch.json`中包含了多种调试配置：
   - "Python: Current File"：用于调试当前打开的Python文件
   - "Python: Flask App"：专门用于调试Flask应用
   - "Python: Debug with Config"：包含环境变量设置的完整调试配置

2. 也可以使用提供的`debug.py`脚本启动调试模式：
   ```bash
   python debug.py
   ```

3. 在VSCode中进行调试时，请确保：
   - 已安装Python扩展
   - 已正确安装所有依赖（运行 `pip install -r requirements.txt`）
   - 当前工作目录为项目根目录

4. 调试配置已经设置好环境变量FLASK_APP和FLASK_ENV，便于开发调试使用。
