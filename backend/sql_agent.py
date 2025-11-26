from database_manager import DatabaseManager
from langchain_core.tools import tool, Tool
from langchain_openai import ChatOpenAI
import requests
from typing import List, Dict, Any
from langchain.agents import create_agent

db_manager = DatabaseManager()

# 保留原有的工具函数
@tool(parse_docstring=True)
def get_database_all_tables(db_name: str) -> str:
    """
    获取数据库所有表名和描述

    Args:
        db_name: 数据库名称
    """
    print(f"get_database_all_tables: {db_name}")
    tables_info = db_manager.get_tables_info(db_name)

    # 创建Markdown表格格式的输出
    if not tables_info["tables"]:
        return "| 表名 | 描述 |\n|------|------|\n| 暂无数据 | 暂无数据 |"

    # 构建表头和行内容
    markdown_table = "| 表名 | 描述 |\n|------|------|\n"
    for table in tables_info["tables"]:
        table_name = table[0]  # 第一列是表名
        description = table[1] if len(table) > 1 else ""  # 第二列可能是描述
        markdown_table += f"| {table_name} | {description} |\n"
    print(f"get_database_all_tables markdown_table: {markdown_table}")
    return markdown_table

@tool(parse_docstring=True)
def get_table_fields(db_name: str, table_name: str) -> str:
    """
    获取表的字段描述

    Args:
        db_name: 数据库名称
        table_name: 表名称
    """
    print(f"get_table_fields : {db_name}, {table_name}")
    structure = db_manager.get_table_structure(db_name, table_name)

    # 创建Markdown表格格式的输出
    if not structure:
        return f"#### 表名：{table_name}\n\n| 字段名 | 类型 | 是否为空 | 键类型 | 默认值 | 额外信息 |\n|--------|------|----------|--------|--------|-----------|\n| 暂无数据 | | | | | |"

    # 构建表头和行内容
    markdown_table = f"#### 表名：{table_name}\n\n| 字段名 | 类型 | 是否为空 | 键类型 | 默认值 | 额外信息 |\n|--------|------|----------|--------|--------|-----------|\n"
    for column in structure:
        field = column['Field']
        type_ = column['Type']
        null = column['Null']
        key = column['Key']
        default = column['Default'] if column['Default'] is not None else ""
        extra = column['Extra']

        markdown_table += f"| {field} | {type_} | {null} | {key} | {default} | {extra} |\n"
    print(f"get_table_fields markdown_table: {markdown_table}")

    return markdown_table

# 创建一个专门的SQL Agent类，使用LangChain的Agent框架
class SQLAgent:
    def __init__(self, lm_studio_url: str = "http://192.168.2.243:1234"):
        """
        初始化SQL Agent

        Args:
            lm_studio_url (str): LM Studio 服务地址
        """
        self.lm_studio_url = lm_studio_url

        # 获取第一个可用的模型
        model_name = self._get_first_available_model()

        # 创建 ChatOpenAI 实例，使用 LM Studio 的 OpenAI API 兼容接口
        self.llm = ChatOpenAI(
            base_url=lm_studio_url + "/v1",
            api_key="lm-studio",  # LM Studio 不需要实际的 API key
            model=model_name   # 使用查询到的第一个模型名称
        )

        # 创建工具列表
        self.tools = [get_database_all_tables, get_table_fields]

        # 定义提示模板
        prompt_template = """
        你是一个资深的MySQL数据库专家。

        你的任务是根据用户的问题，通过调用特定工具来获取信息，并生成准确的SQL语句。你需要：
        1. 首先使用 get_database_all_tables 工具获取数据库中的所有表
        2. 然后分析问题与哪些表相关，最多选择10个相关表
        3. 对于每个相关的表，调用 get_table_fields 获取其结构信息
        4. 基于这些信息和用户的问题生成SQL语句，并且只能返回一条SQL
        """

        # 创建React agent
        self.agent = create_agent(
            self.llm,
            tools=self.tools,
            system_prompt=prompt_template
        )

    def _get_first_available_model(self) -> str:
        """
        查询本地支持的模型列表并返回第一个可用模型

        Returns:
            str: 第一个可用的模型名称，如果无可用模型则返回默认值
        """
        try:
            # 构建API请求URL
            models_url = f"{self.lm_studio_url}/v1/models"

            # 发送GET请求获取模型列表
            response = requests.get(models_url)
            response.raise_for_status()

            # 解析JSON响应
            data = response.json()

            # 提取模型信息（根据LM Studio API格式）
            models = []
            if "data" in data:
                for model_data in data["data"]:
                    # 根据不同字段提取模型信息
                    model_info = {
                        "id": model_data.get("id", ""),
                        "object": model_data.get("object", ""),
                        "created": model_data.get("created", 0),
                        "owned_by": model_data.get("owned_by", "")
                    }
                    models.append(model_info)
            else:
                # 如果没有"date"字段，可能是不同的响应格式
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item:
                            model_info = {
                                "id": item.get("id", ""),
                                "object": item.get("object", ""),
                                "created": item.get("created", 0),
                                "owned_by": item.get("owned_by", "")
                            }
                            models.append(model_info)
                else:
                    # 尝试处理单个模型对象
                    if isinstance(data, dict) and "id" in data:
                        model_info = {
                            "id": data.get("id", ""),
                            "object": data.get("object", ""),
                            "created": data.get("created", 0),
                            "owned_by": data.get("owned_by", "")
                        }
                        models.append(model_info)

            # 返回第一个模型的ID，如果没有可用模型则返回默认值
            if models:
                return models[0]["id"]
            else:
                print("警告: 没有找到可用的本地模型，使用默认模型 'local-model'")
                return "local-model"

        except requests.exceptions.RequestException as e:
            print(f"请求模型列表失败: {str(e)}")
            print("警告: 使用默认模型 'local-model'")
            return "local-model"
        except Exception as e:
            print(f"解析模型信息失败: {str(e)}")
            print("警告: 使用默认模型 'local-model'")
            return "local-model"

    def get_sql_for_question(self, database_name: str, question: str, limit_flag: bool = False, limit: int = 10) -> str:
        """
        根据问题生成SQL语句

        Args:
            database_name (str): 数据库名称
            question (str): 用户的问题

        Returns:
            str: 生成的SQL语句
        """
        try:
            limit = f"- SELECT语句必须加上limit {limit}" if limit_flag else ""

            prompt = f"""
                已知数据库名称: {database_name}

                请记住:
                - 只返回SQL语句本身，不要包含任何解释或额外信息
                {limit}

                用户问题: {question}
            """

            # 执行agent并获取结果
            result = self.agent.invoke({"messages": [{"role": "user", "content": prompt}]})
            
            # 从结果中提取SQL语句（通常在 "output" 字段中）
            response_content = result["messages"][-1].content.strip()

            # 确保返回的是纯SQL语句
            if not response_content:
                return None
            else:
                return response_content

        except Exception as e:
            print(f"生成SQL时出错: {str(e)}")
            raise e

# 创建一个全局实例供外部使用
sql_agent = SQLAgent()
