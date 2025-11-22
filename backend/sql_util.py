# -*- coding: utf-8 -*-
"""
SQL工具模块
包含用于解析SQL语句并提取相关信息的实用函数
"""

try:
    import sqlglot
except ImportError:
    raise ImportError("请安装sqlglot库: pip install sqlglot")

def extract_table_names(sql):
    """
    解析SQL语句，提取其中涉及的表名
    
    Args:
        sql (str): 要解析的SQL语句
        
    Returns:
        list: 涉及的表名列表
        
    Examples:
        >>> extract_table_names("SELECT * FROM users WHERE id = 1")
        ['users']
        
        >>> extract_table_names("SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id")
        ['users', 'posts']
    """
    if not sql or not isinstance(sql, str):
        return []
    
    try:
        # 使用sqlglot解析SQL语句
        parsed = sqlglot.parse_one(sql, dialect="mysql")
        
        # 提取所有表名
        table_names = []
        # 遍历所有的表引用
        for expression in parsed.find_all(sqlglot.expressions.Table):
            if expression.name:  # 确保表名不为空
                table_names.append(expression.name)
                
        # 去重并返回结果
        return list(dict.fromkeys(table_names))  # 保持顺序的去重
        
    except Exception as e:
        # 如果解析失败，返回空列表
        print(f"SQL解析错误: {e}")
        return []

# 测试函数（可选）
if __name__ == "__main__":
    # 测试用例
    test_sql = [
        "SELECT * FROM users WHERE id = 1",
        "SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id",
        "INSERT INTO orders (user_id, product) VALUES (1, 'laptop')",
        "UPDATE users SET name='John' WHERE id=1",
        "DELETE FROM products WHERE category='electronics'"
    ]
    
    for sql in test_sql:
        tables = extract_table_names(sql)
        print(f"SQL: {sql}, tables: {tables}")

