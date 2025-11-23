# MySQL Management API 接口文档

## 概述

这是一个用于管理多个MySQL数据库连接的后端API服务。该服务允许用户添加、删除和更新数据库连接配置，测试数据库连接，并执行SQL查询操作。

## 基础信息

- **基础URL**: `http://localhost:5000`
- **版本**: v1.0
- **协议**: HTTP/HTTPS
- **响应格式**: JSON

## 认证

该API目前不包含认证机制。所有请求都直接访问服务。

## 数据库连接配置格式

```json
{
  "name": "string",
  "host": "string", 
  "port": integer,
  "database": "string",
  "user": "string",
  "password": "string"
}
```

## API端点列表

### 1. 数据库连接管理

#### 获取所有数据库配置
- **端点**: `GET /api/databases`
- **说明**: 返回系统中所有已配置的数据库连接信息
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "name": "test_xxcrypto_rw",
      "host": "pc-3ns1a723w6903b975.rwlb.rds.aliyuncs.com",
      "port": 3306,
      "database": "xxcrypto",
      "user": "test_xxcrypto_rw",
      "password": "aqNPr__YUWxTEtCJfdSlP8Yw"
    }
  ]
}
```

#### 添加新的数据库连接
- **端点**: `POST /api/databases`
- **说明**: 添加一个新的数据库连接配置
- **请求参数** (JSON):
```json
{
  "name": "string",
  "host": "string", 
  "port": integer,
  "database": "string",
  "user": "string",
  "password": "string"
}
```
- **响应示例**:
```json
{
  "success": true,
  "message": "Database added successfully"
}
```

#### 更新数据库连接配置
- **端点**: `PUT /api/databases/{name}`
- **说明**: 使用指定名称更新数据库连接信息
- **路径参数**:
  - `{name}`: 要更新的数据库连接名称
- **请求参数** (JSON):
```json
{
  "host": "string", 
  "port": integer,
  "database": "string",
  "user": "string",
  "password": "string"
}
```
- **响应示例**:
```json
{
  "success": true,
  "message": "Database updated successfully"
}
```

#### 删除数据库连接配置
- **端点**: `DELETE /api/databases/{name}`
- **说明**: 删除指定名称的数据库连接配置
- **路径参数**:
  - `{name}`: 要删除的数据库连接名称
- **响应示例**:
```json
{
  "success": true,
  "message": "Database removed successfully"
}
```

#### 测试数据库连接
- **端点**: `POST /api/databases/{name}/test`
- **说明**: 测试指定数据库连接配置是否可以正常连接
- **路径参数**:
  - `{name}`: 要测试的数据库连接名称
- **响应示例**:
```json
{
  "success": true,
  "message": "Connection successful"
}
```

### 2. 数据库内容操作

#### 获取数据库中的所有表名
- **端点**: `GET /api/databases/{name}/tables`
- **说明**: 返回指定数据库中所有的表名列表
- **路径参数**:
  - `{name}`: 目标数据库的名称
- **响应示例**:
```json
{
  "success": true,
  "data": [
    "users",
    "orders",
    "products"
  ]
}
```

#### 获取特定表的结构信息
- **端点**: `GET /api/databases/{name}/tables/{table_name}`
- **说明**: 返回指定数据库中特定表的结构信息
- **路径参数**:
  - `{name}`: 目标数据库的名称
  - `{table_name}`: 表名
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "Field": "id",
      "Type": "int(11)",
      "Null": "NO",
      "Key": "PRI",
      "Default": null,
      "Extra": "auto_increment"
    },
    {
      "Field": "name", 
      "Type": "varchar(255)",
      "Null": "YES",
      "Key": "",
      "Default": null,
      "Extra": ""
    }
  ]
}
```

#### 获取表的完整结构信息（包括建表语句和索引）
- **端点**: `GET /api/databases/{database}/tables/{table}/structure`
- **说明**: 返回指定数据库中特定表的完整结构信息，包括创建表的SQL语句和所有索引信息
- **路径参数**:
  - `{database}`: 目标数据库的名称
  - `{table}`: 表名
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "create_table_sql": "CREATE TABLE `users` (\\n  `id` int(11) NOT NULL AUTO_INCREMENT,\\n  `name` varchar(255) DEFAULT NULL,\\n  PRIMARY KEY (`id`)\\n) ENGINE=InnoDB DEFAULT CHARSET=utf8",
    "indexes": [
      {
        "Table": "users",
        "Non_unique": 0,
        "Key_name": "PRIMARY",
        "Seq_in_index": 1,
        "Column_name": "id",
        "Collation": "A",
        "Cardinality": 0,
        "Sub_part": null,
        "Packed": null,
        "Null": "",
        "Index_type": "BTREE",
        "Comment": ""
      }
    ]
  }
}
```

#### 获取数据库中所有表的结构信息
- **端点**: `GET /api/databases/{name}/tables/structure`
- **说明**: 返回指定数据库中所有表的结构信息，包括每个表的列信息、创建语句和索引信息
- **路径参数**:
  - `{name}`: 目标数据库的名称
- **响应示例**:
```json
{
  "success": true,
  "data": {
    "table1": {
      "structure": [
        {
          "Field": "id",
          "Type": "int(11)",
          "Null": "NO",
          "Key": "PRI",
          "Default": null,
          "Extra": "auto_increment"
        }
      ],
      "create_table_sql": "CREATE TABLE `table1` (\\n  `id` int(11) NOT NULL AUTO_INCREMENT,\\n  PRIMARY KEY (`id`)\\n) ENGINE=InnoDB DEFAULT CHARSET=utf8",
      "indexes": [
        {
          "Table": "table1",
          "Non_unique": 0,
          "Key_name": "PRIMARY",
          "Seq_in_index": 1,
          "Column_name": "id",
          "Collation": "A",
          "Cardinality": 0,
          "Sub_part": null,
          "Packed": null,
          "Null": "",
          "Index_type": "BTREE",
          "Comment": ""
        }
      ]
    },
    "table2": {
      "structure": [
        {
          "Field": "id",
          "Type": "int(11)",
          "Null": "NO", 
          "Key": "PRI",
          "Default": null,
          "Extra": "auto_increment"
        },
        {
          "Field": "name",
          "Type": "varchar(255)",
          "Null": "YES",
          "Key": "",
          "Default": null,
          "Extra": ""
        }
      ],
      "create_table_sql": "CREATE TABLE `table2` (\\n  `id` int(11) NOT NULL AUTO_INCREMENT,\\n  `name` varchar(255) DEFAULT NULL,\\n  PRIMARY KEY (`id`)\\n) ENGINE=InnoDB DEFAULT CHARSET=utf8",
      "indexes": [
        {
          "Table": "table2",
          "Non_unique": 0,
          "Key_name": "PRIMARY",
          "Seq_in_index": 1,
          "Column_name": "id",
          "Collation": "A",
          "Cardinality": 0,
          "Sub_part": null,
          "Packed": null,
          "Null": "",
          "Index_type": "BTREE",
          "Comment": ""
        }
      ]
    }
  }
}
```

#### 执行SQL语句
- **端点**: `POST /api/databases/{name}/execute`
- **说明**: 在指定数据库中执行SQL语句
- **路径参数**:
  - `{name}`: 目标数据库的名称
- **请求参数** (JSON):
```json
{
  "sql": "string"
}
```
- **响应示例** (SELECT查询):
```json
{
  "success": true,
  "data": {
    "type": "SELECT",
    "data": [
      {
        "id": 1,
        "name": "John Doe"
      }
    ],
    "row_count": 1
  }
}
```
- **响应示例** (INSERT/UPDATE/DELETE查询):
```json
{
  "success": true,
  "data": {
    "type": "INSERT",
    "affected_rows": 1
  }
}
```

### 导入数据

#### 通过SQL文件导入数据库表数据
- **端点**: `POST /api/databases/{name}/import/sql`
- **说明**: 从上传的SQL文件中读取并执行SQL语句以将数据导入到指定数据库中的表
- **路径参数**:
  - `{name}`: 目标数据库的名称
- **请求方式**: multipart/form-data
- **请求参数**:
  - `sql_file`: 要上传的SQL文件（.sql格式）
- **响应示例**:
```json
{
  "success": true,
  "message": "Data imported successfully from SQL file"
}
```

#### 通过CSV文件导入数据库表数据
- **端点**: `POST /api/databases/{name}/import/csv`
- **说明**: 从上传的CSV文件中读取数据并将其插入到指定数据库中的表。支持字段映射（可选）
- **路径参数**:
  - `{name}`: 目标数据库的名称
- **请求方式**: multipart/form-data
- **请求参数**:
  - `csv_file`: 要上传的CSV文件（.csv格式）
  - `table_name` (可选): CSV数据将被导入到的目标表名。如果未提供，系统会尝试根据文件名推断。
  - `field_mapping` (可选): JSON字符串形式的字段映射，用于指定CSV列与数据库字段之间的对应关系
    ```json
    {
      "csv_column1": "db_field1",
      "csv_column2": "db_field2"
    }
    ```
- **响应示例**:
```json
{
  "success": true,
  "message": "Data imported successfully from CSV file"
}
```

### 导出数据库数据
- **端点**: `POST /api/databases/{name}/export`
- **说明**: 导出指定数据库中的所有表或特定表的数据为INSERT SQL或CSV格式的文件
- **路径参数**:
  - `{name}`: 目标数据库的名称
- **请求参数** (JSON):
```json
{
  "format": "string",
  "sql": "string"
}
```
其中：
- `format` 是必需字段，支持值为 `"insert_sql"` 或 `"csv"`
- `sql` 是必需字段
- **响应**: 返回下载的文件内容（二进制流）

### 获取可用模型列表
- **端点**: `GET /api/models`
- **说明**: 获取本地支持的并且被激活的LM Studio模型列表
- **响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": "model-name",
      "object": "model",
      "created": 1678901234,
      "owned_by": "lm-studio"
    }
  ]
}
```

### AI聊天接口
- **端点**: `POST /api/chat`
- **说明**: 根据数据库名和用户问题生成相应的SQL查询语句。该接口使用AI模型分析数据库结构并生成合适的SQL。
- **请求参数** (JSON):
```json
{
  "database_name": "string",
  "question": "string"
}
```
- **响应示例**:
```json
{
  "success": true,
  "sql": "SELECT * FROM users WHERE id = 1"
}
```

### 获取数据库实例中的所有数据库列表
- **端点**: `POST /api/databases/names`
- **说明**: 根据提供的数据库连接信息，获取该数据库实例中所有用户定义的数据库列表（排除系统数据库）
- **请求参数** (JSON):
```json
{
  "name": "string",
  "host": "string", 
  "port": integer,
  "user": "string",
  "password": "string"
}
```
- **响应示例**:
```json
{
  "success": true,
  "data": [
    "mysql",
    "information_schema",
    "performance_schema",
    "sys",
    "my_database"
  ]
}




所有API端点都返回统一的JSON格式错误信息：

### 标准错误响应格式
```json
{
  "success": false,
  "error": "string"
}
```

### 常见HTTP状态码
- **200 OK**: 请求成功
- **201 Created**: 资源创建成功（POST请求）
- **400 Bad Request**: 请求参数错误或缺失
- **404 Not Found**: 指定资源不存在
- **500 Internal Server Error**: 服务器内部错误

### 常见错误类型
- `Missing required field`: 缺少必要字段
- `Failed to connect to database with provided credentials`: 数据库连接失败
- `Database not found`: 找不到指定数据库
- `Table not found or error getting structure`: 表不存在或获取结构失败

## 使用示例

### 1. 添加数据库连接
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

### 2. 获取所有数据库配置
```bash
curl http://localhost:5000/api/databases
```

### 3. 执行查询语句
```bash
curl -X POST http://localhost:5000/api/databases/mydb/execute \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users LIMIT 10"
  }'
```

## 注意事项

- 密码信息以明文形式存储在配置文件中
- 建议根据实际需要添加认证和安全措施
- 支持的SQL语句包括SELECT、INSERT、UPDATE、DELETE等

