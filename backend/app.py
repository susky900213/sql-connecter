from flask import Flask, request, jsonify, stream_with_context, Response, send_from_directory
from flask_cors import CORS
from database_manager import DatabaseManager
from langchain_integration import LangChainIntegration
import json
import os
import traceback


app = Flask(__name__)
CORS(app)
db_manager = DatabaseManager()
langchain_integration = LangChainIntegration()

# 静态文件目录设置
frontend_dist_path = os.path.join(os.path.dirname(__file__), 'dist')

@app.route('/api/databases', methods=['GET'])
def list_databases():
    """获取所有数据库连接配置"""
    databases = db_manager.list_databases()
    return jsonify({
        "success": True,
        "data": databases
    })

@app.route('/api/databases', methods=['POST'])
def add_database():
    """添加新的数据库连接配置"""
    data = request.get_json()
    
    # 验证必要的字段
    required_fields = ['name', 'host', 'port', 'database', 'user', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                "success": False,
                "error": f"Missing required field: {field}"
            }), 400

            # 检查MySQL服务器中是否存在指定的数据库，如果不存在则自动创建
    if not db_manager.create_database(data):

        # 创建数据库失败时，抛出异常而不是继续添加配置
        return jsonify({
                    "success": False,
                    "error": "Failed to create database"
                }), 400


    # 测试连接
    if not db_manager.test_connection(data):
        return jsonify({
            "success": False,
            "error": "Failed to connect to database with provided credentials"
        }), 400
    
    # 添加数据库配置
    success = db_manager.add_database(data)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Database added successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Database with this name already exists"
        }), 400

@app.route('/api/databases/<name>', methods=['PUT'])
def update_database(name):
    """更新数据库连接配置"""
    data = request.get_json()
    
    # 验证必要的字段
    required_fields = ['host', 'port', 'database', 'user', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                "success": False,
                "error": f"Missing required field: {field}"
            }), 400
    
    # 测试连接
    if not db_manager.test_connection(data):
        return jsonify({
            "success": False,
            "error": "Failed to connect to database with provided credentials"
        }), 400
    
    # 更新数据库配置
    success = db_manager.update_database(name, data)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Database updated successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Database not found"
        }), 404

@app.route('/api/databases/<name>', methods=['DELETE'])
def remove_database(name):
    """删除数据库连接配置"""
    success = db_manager.remove_database(name)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Database removed successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Database not found"
        }), 404

@app.route('/api/databases/<name>/test', methods=['POST'])
def test_database_connection(name):
    """测试数据库连接"""
    db_config = db_manager.get_database(name)
    
    if not db_config:
        return jsonify({
            "success": False,
            "error": "Database not found"
        }), 404
    
    success = db_manager.test_connection(db_config)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Connection successful"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Failed to connect to database"
        }), 500

@app.route('/api/databases/test', methods=['POST'])
def test_database_connection_v2():
    """测试数据库连接"""
    db_config = request.get_json()

    # 验证必要的字段
    required_fields = ['name', 'host', 'port', 'database', 'user', 'password']
    for field in required_fields:
        if field not in db_config:
            return jsonify({
                "success": False,
                "error": f"Missing required field: {field}"
            }), 400

    success = db_manager.test_connection(db_config)

    if success:
        return jsonify({
            "success": True,
            "message": "Connection successful"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Failed to connect to database"
        }), 500

@app.route('/api/databases/<name>/tables', methods=['GET'])
def get_tables(name):
    """获取数据库中的所有表"""
    tables = db_manager.get_tables(name)
    
    return jsonify({
        "success": True,
        "data": tables
    })

@app.route('/api/databases/<name>/tables/<table_name>', methods=['GET'])
def get_table_structure(name, table_name):
    """获取表结构信息"""
    structure = db_manager.get_table_structure(name, table_name)
    
    if not structure:
        return jsonify({
            "success": False,
            "error": "Table not found or error getting structure"
        }), 404
    
    return jsonify({
        "success": True,
        "data": structure
    })

@app.route('/api/databases/<database>/tables/<table>/structure', methods=['GET'])
def get_table_structure_extended(database, table):
    """获取表的完整结构信息，包括建表语句和索引"""
    table_info = db_manager.get_table_info(database, table)
    
    if not table_info:
        return jsonify({
            "success": False,
            "error": "Table not found or error getting structure"
        }), 404
    
    return jsonify({
        "success": True,
        "data": table_info
    })

@app.route('/api/databases/<name>/tables/structure', methods=['GET'])
def get_all_tables_structure(name):
    """获取数据库中所有表的结构信息"""
    result = db_manager.get_all_tables_structure(name)
    
    if not result["success"]:
        return jsonify({
            "success": False,
            "error": result["error"]
        }), 500
    
    return jsonify({
        "success": True,
        "data": result["data"]
    })

@app.route('/api/databases/<name>/execute', methods=['POST'])
def execute_sql(name):
    """执行SQL语句"""
    data = request.get_json()
    
    if 'sql' not in data:
        return jsonify({
            "success": False,
            "error": "Missing required field: sql"
        }), 400
    
    result = db_manager.execute_sql(name, data['sql'])
    
    if result["success"]:
        return jsonify({
            "success": True,
            "data": result
        })
    else:
        return jsonify({
            "success": False,
            "error": result["error"]
        }), 400

# 新增的AI聊天接口 - 直接返回SQL
@app.route('/api/chat', methods=['POST'])
def chat_with_database():
    """AI聊天接口，根据数据库名和问题返回SQL查询结果"""
    data = request.get_json()
    
    # 验证必要参数
    if 'database_name' not in data:
        return jsonify({
            "success": False,
            "error": "Missing required field: database_name"
        }), 400
        
    if 'question' not in data:
        return jsonify({
            "success": False,
            "error": "Missing required field: question"
        }), 400

    limit_flag = True
    limit = "10"

    if 'limit_flag' in data:
        limit_flag = data['limit_flag']

    if 'limit' in data and data['limit'] != 0:
        limit = data['limit']

    database_name = data['database_name']
    question = data['question']
    
    # 获取数据库中所有表的结构信息
    tables_structure_result = db_manager.get_all_tables_structure(database_name)
    
    if not tables_structure_result["success"]:
        return jsonify({
            "success": False,
            "error": f"Failed to get database structure: {tables_structure_result['error']}"
        }), 500
    
    # 准备用于AI的上下文信息
    context_info = []
    for table_name, table_data in tables_structure_result["data"].items():
        # 获取表的基本结构信息
        structure_info = ""
        if "structure" in table_data:
            structure_info += f"\n表 {table_name} 的字段结构：\n"
            for column in table_data["structure"]:
                structure_info += f"- {column['Field']} ({column['Type']}) "
                if column['Null'] == 'NO':
                    structure_info += "NOT NULL "
                if column['Key'] != '':
                    structure_info += f"KEY({column['Key']}) "
                if column['Default']:
                    structure_info += f"DEFAULT {column['Default']} "
                structure_info += "\n"
        
        # 添加建表语句
        create_sql = table_data.get("create_table_sql", "")
        if create_sql:
            structure_info += f"\n创建语句:\n{create_sql}\n"
            
        context_info.append(structure_info)
    
    # 将上下文信息整合为字符串
    context_str = "\n".join(context_info)

    # 构建提示模板，让AI扮演数据库专家的角色
    if limit_flag:
        prompt_template = (
            "你是一个数据库资深专家。请根据以下数据库表结构和用户问题生成相应的SQL查询语句。\n\n"
            "数据库表结构:\n{context}\n\n"
            "用户问题: {question}\n\n"
            "要求:\n"
            "1. 用中文回答，输出结果包含完整的SQL语句（不带任何额外解释）\n"
            "2. 如果需要连接多个表，请在查询中体现\n"
            "3. 请增加limit " + str(limit) + "\n"
            "4. SQL必须是有效的MySQL语法\n"
            "5. 不要返回任何其他内容，只返回SQL语句本身\n"
        )
    else:
        prompt_template = (
                    "你是一个数据库资深专家。请根据以下数据库表结构和用户问题生成相应的SQL查询语句。\n\n"
                    "数据库表结构:\n{context}\n\n"
                    "用户问题: {question}\n\n"
                    "要求:\n"
                    "1. 用中文回答，输出结果包含完整的SQL语句（不带任何额外解释）\n"
                    "2. 如果需要连接多个表，请在查询中体现\n"
                    "3. SQL必须是有效的MySQL语法\n"
                    "4. 不要返回任何其他内容，只返回SQL语句本身\n"
                )
    
    # 使用LangChain生成回答
    try:
        # 调用LangChain模型生成SQL
        llm_response = langchain_integration.llm.invoke(
            prompt_template.format(context=context_str, question=question)
        )
        
        sql_result = str(llm_response.content).strip()
        
        # 检查是否包含有效的SQL语句
        if not sql_result:
            return jsonify({
                "success": False,
                "error": "AI无法生成有效SQL查询结果"
            }), 500
        else:
            # 直接返回SQL结果
            return jsonify({
                "success": True,
                "sql": sql_result
            })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"生成SQL时出现错误: {str(e)}"
            })



# 新增的API端点：获取LM Studio模型列表
@app.route('/api/models', methods=['GET'])
def get_models():
    """获取本地支持的并且被激活的LM Studio模型"""
    try:
        models = langchain_integration.get_available_models()
        return jsonify({
            "success": True,
            "data": models
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"获取模型列表失败: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(error):
        return jsonify({
            "success": False,
            "error": "Endpoint not found"
        }), 404

@app.route('/api/databases/names', methods=['POST'])
def get_instance_databases():
    """获取指定数据库实例中的所有数据库列表"""
    db_config = request.get_json()

    # 验证必要的字段
    required_fields = ['name', 'host', 'port', 'user', 'password']
    for field in required_fields:
        if field not in db_config:
            return jsonify({
                "success": False,
                "error": f"Missing required field: {field}"
            }), 400

    result = db_manager.get_instance_databases(db_config)
    
    if not result["success"]:
        return jsonify({
            "success": False,
            "error": result["error"]
        }), 500
    
    return jsonify({
        "success": True,
        "data": result["data"]
    })

@app.route('/api/databases/<name>/export', methods=['POST'])
def export_database_data(name):
    """导出数据库数据为INSERT SQL或CSV格式"""
    data = request.get_json()
    
    # 验证必要参数
    if 'format' not in data:
        return jsonify({
            "success": False,
            "error": "Missing required field: format"
        }), 400

    # 验证必要参数
    if 'sql' not in data:
        return jsonify({
            "success": False,
            "error": "Missing required field: sql"
        }), 400
    
    format_type = data['format']
    sql = data['sql']
    table_name = None if 'table_name' not in data else data['table_name']

    # 支持的格式类型
    supported_formats = ['insert_sql', 'csv']
    if format_type not in supported_formats:
        return jsonify({
            "success": False,
            "error": f"Unsupported format type. Supported formats: {supported_formats}"
        }), 400


    
    try:
        result = db_manager.export_sql_data(name, sql, format_type, table_name)
        if not result["success"]:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 500
        
        # 返回导出的内容
        return Response(
            result["content"],
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename="export.{format_type}.sql"' if format_type == 'insert_sql' else f'attachment; filename="export.csv"'
            }
        )
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Export failed: {str(e)}"
        }), 500

# 添加路由：提供前端静态文件
@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serve static files from the dist directory"""
    try:
        return send_from_directory(frontend_dist_path, filename)
    except FileNotFoundError:
        # 如果找不到特定文件，返回index.html（用于单页应用的路由）
        if '.' not in filename and not filename.startswith('api/'):
            return send_from_directory(frontend_dist_path, 'index.html')
        else:
            # 对于API请求或其他404情况
            return jsonify({
                "success": False,
                "error": "File not found"
            }), 404

# 添加路由：根路径返回前端入口文件
@app.route('/')
def serve_index():
    """Serve the main index.html file"""
    return send_from_directory(frontend_dist_path, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
