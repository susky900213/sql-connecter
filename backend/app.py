from flask import Flask, request, jsonify, stream_with_context, Response, send_from_directory
from flask_cors import CORS
from database_manager import DatabaseManager
from sql_agent import SQLAgent
import json
import os
import traceback
import csv


app = Flask(__name__)
CORS(app)
db_manager = DatabaseManager()
sql_agent = SQLAgent()

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

# 修改：从SQL内容导入数据的接口（支持批量语句和事务）
@app.route('/api/databases/<name>/import/sql', methods=['POST'])
def import_sql(name):
    """通过JSON中的SQL内容导入数据到数据库表（支持批量执行和事务）"""
    try:
        # 获取数据库连接信息
        db = db_manager.get_database(name)
        if not db:
            return jsonify({"error": "Database not found"}), 404

        # 检查请求是否包含SQL内容
        if 'sql' not in request.json:
            return jsonify({"error": "Missing SQL content"}), 400

        sql_content = request.json['sql']
        
        # 将SQL内容分割成语句（以分号为分隔符）
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        # 执行批量SQL语句 - 使用新的函数，不再调用execute_sql
        result = db_manager.execute_batch_sql_no_execute_sql(name, sql_statements)
        
        return jsonify(result), 200

    except Exception as e:
        print(f"Error importing SQL: {e}")
        return jsonify({"error": str(e)}), 500

# 新增：从SQL文件导入数据的接口（支持批量语句和事务）
@app.route('/api/databases/<name>/import/sql/file', methods=['POST'])
def import_sql_file(name):
    """通过上传的SQL文件导入数据到数据库表（支持批量执行和事务）"""
    # 检查是否有文件上传
    if 'sql_file' not in request.files:
        return jsonify({
            "success": False,
            "error": "Missing SQL file"
        }), 400
    
    sql_file = request.files['sql_file']
    
    if sql_file.filename == '':
        return jsonify({
            "success": False,
            "error": "No selected SQL file"
        }), 400
    
    # 检查文件扩展名
    if not sql_file.filename.endswith('.sql'):
        return jsonify({
            "success": False,
            "error": "Invalid file type. Please upload a .sql file"
        }), 400
    
    try:
        # 读取SQL文件内容
        sql_content = sql_file.read().decode('utf-8')
        
        # 将SQL内容按分号分割成语句列表（简单处理，不支持复杂语法）
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        # 执行批量SQL语句 - 使用新的函数，不再调用execute_sql
        result = db_manager.execute_batch_sql_no_execute_sql(name, sql_statements)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": f"Successfully imported SQL file. {len(sql_statements)} statements executed."
            })
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to process SQL file: {str(e)}"
        }), 500


# 新增：从CSV文件导入数据的接口
@app.route('/api/databases/<name>/import/csv', methods=['POST'])
def import_csv_file(name):
    """通过上传的CSV文件导入数据到数据库表"""
    # 检查是否有文件上传
    if 'csv_file' not in request.files:
        return jsonify({
            "success": False,
            "error": "Missing CSV file"
        }), 400
    
    csv_file = request.files['csv_file']
    
    if csv_file.filename == '':
        return jsonify({
            "success": False,
            "error": "No selected CSV file"
        }), 400
    
    # 检查文件扩展名
    if not csv_file.filename.endswith('.csv'):
        return jsonify({
            "success": False,
            "error": "Invalid file type. Please upload a .csv file"
        }), 400
    
    try:
        # 获取表名（必须提供）
        if request.content_type == 'application/json' or request.form:
            data = request.get_json() if request.is_json else request.form.to_dict()
        else:
            # 处理 multipart/form-data 格式
            data = {}
            if hasattr(request, 'form'):
                data.update(request.form.to_dict())
        
        table_name = None
        if 'table_name' in data:
            table_name = data['table_name']
        else:
            return jsonify({
                "success": False,
                "error": "Missing required field: table_name"
            }), 400
        
        # 获取可选的字段映射
        field_mapping_str = data.get('field_mapping', None)
        if field_mapping_str:
            field_mapping = json.loads(field_mapping_str)
        else:
            field_mapping = {}
        
        # 如果没有提供字段映射，需要从CSV文件的第一行读取列名
        # if not field_mapping:
        #     # 先读取第一行来获取列名（不消费整个文件流）
        #     csv_content = csv_file.read()
        #     csv_file.seek(0)  # 重新定位到文件开头
            
        #     # 解析CSV内容以获取表头
        #     decoded_content = csv_content.decode('utf-8')
        #     reader = csv.reader(decoded_content.splitlines(), delimiter=',')
            
        #     try:
        #         header_row = next(reader)
        #         # 创建字段映射：将第一行作为目标列名，对应到数据库的字段（需要进一步处理）
        #         field_mapping = {str(i): col.strip() for i, col in enumerate(header_row)}
        #         print(f"Auto-detected field mapping from CSV: {field_mapping}")
        #     except StopIteration:
        #         return jsonify({
        #             "success": False,
        #             "error": "CSV file is empty"
        #         }), 400
        
        # 检查数据库连接配置
        db_config = db_manager.get_database(name)
        if not db_config:
            return jsonify({
                "success": False,
                "error": "Database configuration not found"
            }), 400
            
        # 确保表存在，如果不存在则需要先创建表（这里简单处理）
        tables = db_manager.get_tables(name)
        table_exists = table_name in tables
        
        if not table_exists:
            return jsonify({
                "success": False,
                "error": f"Table {table_name} does not exist"
            }), 400
            
        # 处理CSV数据并插入到数据库中
        csv_file.seek(0)  # 重新定位文件开头
        
        # 创建一个简单的处理函数来插入数据
        import io
        content = csv_file.read().decode('utf-8')
        csv_data = io.StringIO(content)
        reader = csv.reader(csv_data, delimiter=',')
        
        # 获取表结构用于验证列数和类型
        table_structure = db_manager.get_table_structure(name, table_name)
        if not table_structure:
            return jsonify({
                "success": False,
                "error": f"Cannot get structure for table {table_name}"
            }), 400
        
        # 处理数据插入（使用增强版批量导入功能）
        result = db_manager.import_csv_to_table(name, table_name, reader, field_mapping)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": f"Successfully imported CSV file to {table_name}. {result['rows_imported']} rows inserted."
            })
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 400
            
    except Exception as e:
        print(f"Error in import_csv_file: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to process CSV file: {str(e)}"
        }), 500


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

    # 使用LangChain生成回答
    try:
        # 调用LangChain模型生成SQL
        llm_response = sql_agent.get_sql_for_question(database_name, question, limit_flag, limit)
        
        sql_result = str(llm_response).strip()
        
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
