import json
import os
import csv
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any
import sql_util


class DatabaseManager:
    def __init__(self, config_path: str = "./config.json"):
        self.config_path = config_path
        self.load_config()
    
    def load_config(self):
        """从JSON文件加载数据库配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {"databases": []}
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {"databases": []}
    
    def save_config(self):
        """保存数据库配置到JSON文件"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def add_database(self, db_config: Dict[str, Any]) -> bool:
        """添加数据库连接配置"""
        # 检查是否已存在相同名称的数据库
        for db in self.config["databases"]:
            if db.get("name") == db_config.get("name"):
                return False
        
        self.config["databases"].append(db_config)
        self.save_config()
        return True
    
    def remove_database(self, name: str) -> bool:
        """删除数据库连接配置"""
        for i, db in enumerate(self.config["databases"]):
            if db.get("name") == name:
                del self.config["databases"][i]
                self.save_config()
                return True
        return False
    
    def update_database(self, old_name: str, new_db_config: Dict[str, Any]) -> bool:
        """更新数据库连接配置"""
        for i, db in enumerate(self.config["databases"]):
            if db.get("name") == old_name:
                self.config["databases"][i] = new_db_config
                self.save_config()
                return True
        return False
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """列出所有数据库连接配置"""
        return self.config["databases"]
    
    def get_database(self, name: str) -> Dict[str, Any]:
        """获取特定的数据库连接配置"""
        for db in self.config["databases"]:
            if db.get("name") == name:
                return db
        return None
    
    def test_connection(self, db_config: Dict[str, Any]) -> bool:
        """测试数据库连接"""
        try:
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            if connection.is_connected():
                connection.close()
                return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
        return False

    def create_database(self, db_config: Dict[str, Any]) -> bool:
        """测试数据库连接"""
        try:
           # 先连接到MySQL服务器（不指定具体数据库）
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )

            if connection.is_connected():
                cursor = connection.cursor()

                # 检查数据库是否存在
                database_name = db_config.get('database', '')
                cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
                result = cursor.fetchone()

                # 如果数据库不存在，则创建它
                if not result:
                    create_db_sql = f"CREATE DATABASE IF NOT EXISTS `{database_name}`"
                    cursor.execute(create_db_sql)

                cursor.close()
                connection.close()
            return True
        except Exception as e:
            return False
    
    def get_tables(self, db_name: str) -> List[str]:
        """获取数据库中的所有表名"""
        db_config = self.get_database(db_name)
        if not db_config:
            return []
        
        try:
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            
            if not connection.is_connected():
                return []
            
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            connection.close()
            
            return tables
            
        except Error as e:
            print(f"Error getting tables: {e}")
            return []
    
    def get_table_structure(self, db_name: str, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构信息"""
        db_config = self.get_database(db_name)
        if not db_config:
            return []
        
        try:
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            
            if not connection.is_connected():
                return []
            
            cursor = connection.cursor()
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            cursor.close()
            connection.close()
            
            # 转换为字典列表
            structure = []
            for column in columns:
                structure.append({
                    "Field": column[0],
                    "Type": column[1],
                    "Null": column[2],
                    "Key": column[3],
                    "Default": column[4],
                    "Extra": column[5]
                })
            
            return structure
            
        except Error as e:
            print(f"Error getting table structure: {e}")
            return []
    
    def get_table_info(self, db_name: str, table_name: str) -> Dict[str, Any]:
        """获取表的完整信息，包括建表语句和索引"""
        db_config = self.get_database(db_name)
        if not db_config:
            return {}
        
        try:
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            
            if not connection.is_connected():
                return {}
            
            cursor = connection.cursor()
            
            # 获取表的创建语句
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_table_result = cursor.fetchone()
            create_table_sql = create_table_result[1] if create_table_result else ""
            
            # 获取索引信息
            cursor.execute(f"SHOW INDEX FROM `{table_name}`")
            indexes = cursor.fetchall()
            
            # 处理索引数据
            index_list = []
            for index in indexes:
                index_info = {
                    "Table": index[0],
                    "Non_unique": index[1], 
                    "Key_name": index[2],
                    "Seq_in_index": index[3],
                    "Column_name": index[4],
                    "Collation": index[5],
                    "Cardinality": index[6],
                    "Sub_part": index[7],
                    "Packed": index[8],
                    "Null": index[9],
                    "Index_type": index[10],
                    "Comment": index[11]
                }
                index_list.append(index_info)
            
            cursor.close()
            connection.close()
            
            # 返回完整的表信息
            return {
                "create_table_sql": create_table_sql,
                "indexes": index_list
            }
            
        except Error as e:
            print(f"Error getting table info: {e}")
    
    
    def get_all_tables_structure(self, db_name: str) -> Dict[str, Any]:
        """获取数据库中所有表的结构信息"""
        db_config = self.get_database(db_name)
        if not db_config:
            return {"success": False, "error": "Database not found"}
        
        try:
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            
            if not connection.is_connected():
                return {"success": False, "error": "Database connection failed"}
            
            # 获取所有表名
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            
            # 为每个表获取结构信息
            all_tables_structure = {}
            for table_name in tables:
                try:
                    cursor = connection.cursor()
                    cursor.execute(f"DESCRIBE `{table_name}`")
                    columns = cursor.fetchall()
                    cursor.close()
                    
                    # 转换为字典列表
                    structure = []
                    for column in columns:
                        structure.append({
                            "Field": column[0],
                            "Type": column[1],
                            "Null": column[2],
                            "Key": column[3],
                            "Default": column[4],
                            "Extra": column[5]
                        })
                    
                    # 获取表的完整信息
                    cursor = connection.cursor()
                    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                    create_table_result = cursor.fetchone()
                    create_table_sql = create_table_result[1] if create_table_result else ""
                    cursor.close()
                    
                    # 获取索引信息
                    cursor = connection.cursor()
                    cursor.execute(f"SHOW INDEX FROM `{table_name}`")
                    indexes = cursor.fetchall()
                    cursor.close()
                    
                    # 处理索引数据
                    index_list = []
                    for index in indexes:
                        index_info = {
                            "Table": index[0],
                            "Non_unique": index[1], 
                            "Key_name": index[2],
                            "Seq_in_index": index[3],
                            "Column_name": index[4],
                            "Collation": index[5],
                            "Cardinality": index[6],
                            "Sub_part": index[7],
                            "Packed": index[8],
                            "Null": index[9],
                            "Index_type": index[10],
                            "Comment": index[11]
                        }
                        index_list.append(index_info)
                    
                    all_tables_structure[table_name] = {
                        "structure": structure,
                        "create_table_sql": create_table_sql,
                        "indexes": index_list
                    }
                except Error as e:
                    print(f"Error getting info for table {table_name}: {e}")
                    # 即使某个表出错，也继续处理其他表
                    all_tables_structure[table_name] = {
                        "error": str(e)
                    }
            
            connection.close()
            
            return {"success": True, "data": all_tables_structure}
            
        except Error as e:
            print(f"Error getting all tables structure: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_sql(self, db_name: str, sql_statement: str) -> Dict[str, Any]:
        """执行SQL语句"""
        db_config = self.get_database(db_name)
        if not db_config:
            return {"success": False, "error": "Database not found"}
        
        try:
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            
            if not connection.is_connected():
                return {"success": False, "error": "Database connection failed"}
            
            cursor = connection.cursor()
            
            # 分析SQL语句类型
            sql_upper = sql_statement.strip().upper()
            
            if sql_upper.startswith("SELECT"):
                cursor.execute(sql_statement)
                results = cursor.fetchall()
                
                # 获取列名
                columns = [desc[0] for desc in cursor.description]
                
#                 # 转换结果为字典列表，保持字段顺序
#                 data = []
#                 for row in results:
#                     # 使用有序字典确保字段顺序与SQL查询中一致
#                     row_dict = OrderedDict()
#                     for i, value in enumerate(row):
#                         row_dict[columns[i]] = value
#                     data.append(row_dict)
                
                cursor.close()
                connection.close()
                return {
                    "success": True,
                    "type": "SELECT",
                    "columns": columns,
                    "results": results,
                    "row_count": len(results)
                }
            elif sql_upper.startswith("WITH"):
                cursor.execute(sql_statement)
                try:
                    results = cursor.fetchall()
                except Error as e:
                    connection.commit()
                    affected_rows = cursor.rowcount
                    cursor.close()
                    connection.close()
                    return {
                        "success": True,
                        "type": sql_upper.split()[0],
                        "affected_rows": affected_rows
                    }
            else:
                # 非SELECT语句
                affected_rows_list = []
                for result in cursor.execute(sql_statement, multi=True):
                    affected_rows_list.append(result.rowcount)
                connection.commit()

#                     affected_rows = cursor.rowcount
                cursor.close()
                connection.close()

                return {
                    "success": True,
                    "type": sql_upper.split()[0],
                    "affected_rows": affected_rows_list
                }
                
        except Error as e:
            connection.rollback()
            print(f"Error executing SQL: {e}")
            try:
                if 'connection' in locals() and connection.is_connected():
                    connection.close()
            except:
                pass
    
    def get_instance_databases(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """获取指定数据库实例中的所有数据库列表"""
        if not db_config:
            return {"success": False, "error": "Database not found"}
        
        try:
            # 连接到MySQL服务器（不指定具体数据库）
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            
            if not connection.is_connected():
                return {"success": False, "error": "Database connection failed"}
            
            cursor = connection.cursor()
            # 获取所有数据库列表
            cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in cursor.fetchall()]
            
            # 排除系统数据库（可选）
            system_databases = ['information_schema', 'performance_schema', 
                              'mysql', 'sys']
            user_databases = [db for db in databases if db not in system_databases]
            
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "data": user_databases
            }
            
        except Error as e:
            print(f"Error getting instance databases: {e}")
            return {"success": False, "error": str(e)}
    
    def export_table_data(self, db_name: str, table_name: str, format_type: str = "insert_sql") -> Dict[str, Any]:
        """导出指定表的数据为INSERT SQL或CSV格式"""
        db_config = self.get_database(db_name)
        if not db_config:
            return {"success": False, "error": "Database not found"}
        
        try:
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            
            if not connection.is_connected():
                return {"success": False, "error": "Database connection failed"}
            
            cursor = connection.cursor()
            
            # 获取表结构
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            
            # 构建列名列表，用于CSV导出和INSERT语句的字段部分
            column_names = [column[0] for column in columns]
            
            # 获取所有数据行
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()
            
            if format_type == "csv":
                # 生成CSV格式内容
                output_lines = []
                
                # 添加CSV头
                output_lines.append(','.join([f'"{col}"' for col in column_names]))
                
                # 处理每一行数据
                for row in rows:
                    csv_row = []
                    for value in row:
                        if value is None:
                            csv_row.append('')
                        elif isinstance(value, str):
                            # 对字符串进行转义处理，如果包含引号或逗号需要加引号
                            escaped_value = value.replace('"', '""')
                            csv_row.append(f'"{escaped_value}"')
                        else:
                            csv_row.append(str(value))
                    output_lines.append(','.join(csv_row))
                
                result_content = '\n'.join(output_lines)
            elif format_type == "insert_sql":
                # 生成INSERT SQL格式内容
                output_lines = []
                
                # 添加文件头注释
                output_lines.append("-- MySQL dump")
                output_lines.append(f"-- Table: {table_name}")
                output_lines.append("")
                
                for row in rows:
                    # 构建插入语句的值部分，注意数据类型的处理
                    values_list = []
                    for i, value in enumerate(row):
                        column_name = column_names[i]
                        
                        if value is None:
                            values_list.append('NULL')
                        elif isinstance(value, str):
                            # 对字符串进行转义和引号处理
                            escaped_value = value.replace('\\', '\\\\').replace("'", "\\'")
                            values_list.append(f"'{escaped_value}'")
                        elif isinstance(value, (int, float)):
                            values_list.append(str(value))
                        else:
                            # 其他类型转换为字符串并用引号包围
                            values_list.append(f"'{str(value)}'")
                    
                    # 构建INSERT语句
                    columns_str = ', '.join([f'`{col}`' for col in column_names])
                    values_str = ', '.join(values_list)
                    insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({values_str});"
                    output_lines.append(insert_sql)
                
                result_content = '\n'.join(output_lines)
            else:
                return {"success": False, "error": f"Unsupported format type: {format_type}"}
            
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "content": result_content,
                "format": format_type
            }
            
        except Error as e:
            print(f"Error exporting table data: {e}")
            try:
                if 'connection' in locals() and connection.is_connected():
                    connection.close()
            except:
                pass
            return {"success": False, "error": f"Failed to export data: {str(e)}"}
    
    def export_database_data(self, db_name: str, format_type: str = "insert_sql") -> Dict[str, Any]:
        """导出数据库中所有表的数据为INSERT SQL或CSV格式"""
        # 获取数据库中的所有表
        tables = self.get_tables(db_name)
        
        if not tables:
            return {"success": False, "error": "No tables found in database"}
        
        results = []
        
        for table_name in tables:
            # 导出每个表的数据
            export_result = self.export_table_data(db_name, table_name, format_type)
            
            if export_result["success"]:
                results.append({
                    "table": table_name,
                    "content": export_result["content"]
                })
            else:
                return {"success": False, "error": f"Failed to export table {table_name}: {export_result['error']}"}
        
        # 根据格式类型组合所有内容
        if format_type == "csv":
            # CSV导出时，将所有表的数据合并为一个大的CSV文件（每张表之间用空行分隔）
            output_lines = []
            for result in results:
                output_lines.append(f"-- Table: {result['table']}")
                output_lines.append(result["content"])
                output_lines.append("")  # 空行分隔不同表
            combined_content = '\n'.join(output_lines)
        elif format_type == "insert_sql":
            # INSERT SQL导出时，将所有表的内容合并为一个文件
            output_lines = []
            output_lines.append("-- MySQL dump of all tables")
            for result in results:
                output_lines.append(f"-- Table: {result['table']}")
                output_lines.append(result["content"])
                output_lines.append("")  # 空行分隔不同表
            combined_content = '\n'.join(output_lines)
        else:
            return {"success": False, "error": f"Unsupported format type: {format_type}"}
        
        return {
            "success": True,
            "content": combined_content,
            "format": format_type,
            "tables_count": len(tables)
            }

    def export_sql_data(self, db_name: str, sql_statement: str, format_type: str = "insert_sql", table_name: str = None) -> Dict[str, Any]:
        """根据SQL语句导出数据为INSERT SQL或CSV格式"""
        db_config = self.get_database(db_name)
        if not db_config:
            return {"success": False, "error": "Database not found"}
        
        try:
            connection = mysql.connector.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                database=db_config.get('database', ''),
                user=db_config.get('user', ''),
                password=db_config.get('password', '')
            )
            
            if not connection.is_connected():
                return {"success": False, "error": "Database connection failed"}
            
            cursor = connection.cursor()
            
            # 执行SQL语句
            cursor.execute(sql_statement)
            
            # 获取结果
            results = cursor.fetchall()
            
            # 如果是SELECT查询，获取列信息
            if sql_statement.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description]
                
                if format_type == "csv":
                    # 生成CSV格式内容
                    output_lines = []
                    
                    # 添加CSV头（字段名）
                    output_lines.append(','.join([f'"{col}"' for col in columns]))
                    
                    # 处理每一行数据
                    for row in results:
                        csv_row = []
                        for value in row:
                            if value is None:
                                csv_row.append('')
                            elif isinstance(value, str):
                                # 对字符串进行转义处理，如果包含引号或逗号需要加引号
                                escaped_value = value.replace('"', '""')
                                csv_row.append(f'"{escaped_value}"')
                            else:
                                csv_row.append(str(value))
                        output_lines.append(','.join(csv_row))
                    
                    result_content = '\n'.join(output_lines)
                elif format_type == "insert_sql":
                    # 生成INSERT SQL格式内容
                    output_lines = []
                    
                    # 添加文件头注释
                    output_lines.append("-- MySQL dump from custom SQL")
                    output_lines.append("")
                    
                    # 如果table_name为None或空字符串，需要从SQL中解析表名
                    if not table_name:
                        # 使用sql_util提取SQL中的表名
                        table_names = sql_util.extract_table_names(sql_statement)
                        if table_names:
                            table_name = table_names[0]  # 获取第一个表名
                        else:
                            table_name = "table_name"
                    
                    # 批量处理：每50条记录为一批进行插入
                    batch_size = 50
                    for i in range(0, len(results), batch_size):
                        batch = results[i:i + batch_size]
                        
                        # 对于每个批次，构建多个INSERT语句（单个INSERT包含多行）
                        if len(batch) == 1:
                            # 如果只有一条记录，则使用单条插入
                            row = batch[0]
                            values_list = []
                            for j, value in enumerate(row):
                                column_name = columns[j]
                                
                                if value is None:
                                    values_list.append('NULL')
                                elif isinstance(value, str):
                                    # 对字符串进行转义和引号处理
                                    escaped_value = value.replace('\\', '\\\\').replace("'", "\\'")
                                    values_list.append(f"'{escaped_value}'")
                                elif isinstance(value, (int, float)):
                                    values_list.append(str(value))
                                else:
                                    # 其他类型转换为字符串并用引号包围
                                    values_list.append(f"'{str(value)}'")
                            
                            columns_str = ', '.join([f'`{col}`' for col in columns])
                            values_str = ', '.join(values_list)
                            insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({values_str});"
                            output_lines.append(insert_sql)
                        else:
                            # 如果有多条记录，则使用多行插入
                            batch_values = []
                            for row in batch:
                                values_list = []
                                for j, value in enumerate(row):
                                    column_name = columns[j]
                                    
                                    if value is None:
                                        values_list.append('NULL')
                                    elif isinstance(value, str):
                                        # 对字符串进行转义和引号处理
                                        escaped_value = value.replace('\\', '\\\\').replace("'", "\\'")
                                        values_list.append(f"'{escaped_value}'")
                                    elif isinstance(value, (int, float)):
                                        values_list.append(str(value))
                                    else:
                                        # 其他类型转换为字符串并用引号包围
                                        values_list.append(f"'{str(value)}'")
                                
                                batch_values.append(f"({', '.join(values_list)})")
                            
                            columns_str = ', '.join([f'`{col}`' for col in columns])
                            values_str = ', '.join(batch_values)
                            insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES {values_str};"
                            output_lines.append(insert_sql)
                    
                    result_content = '\n'.join(output_lines)
                else:
                    return {"success": False, "error": f"Unsupported format type: {format_type}"}
            else:
                # 非SELECT语句（如INSERT/UPDATE/DELETE），返回影响的行数
                if format_type == "csv":
                    # 对于非SELECT语句，CSV格式可以简单返回影响行数信息
                    output_lines = []
                    output_lines.append('"affected_rows"')
                    output_lines.append(str(len(results)))
                    result_content = '\n'.join(output_lines)
                elif format_type == "insert_sql":
                    # 如果table_name为None或空字符串，需要从SQL中解析表名
                    if not table_name:
                        # 使用sql_util提取SQL中的表名
                        table_names = sql_util.extract_table_names(sql_statement)
                        if table_names:
                            table_name = table_names[0]  # 获取第一个表名
                    
                    # 对于非SELECT语句，INSERT SQL格式也可以返回影响行数信息
                    output_lines = []
                    output_lines.append("-- MySQL command results")
                    output_lines.append(f"-- SQL: {sql_statement}")
                    if table_name:
                        output_lines.append(f"-- Table: {table_name}")
                    output_lines.append(f"-- Affected rows: {len(results)}")
                    result_content = '\n'.join(output_lines)
                else:
                    return {"success": False, "error": f"Unsupported format type: {format_type}"}
            
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "content": result_content,
                "format": format_type,
                "row_count": len(results) if sql_statement.strip().upper().startswith("SELECT") else None
            }
            
        except Error as e:
            print(f"Error exporting SQL data: {e}")
            try:
                if 'connection' in locals() and connection.is_connected():
                    connection.close()
            except:
                pass

