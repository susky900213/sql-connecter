"""
LangChain 集成模块
用于连接本地 LM Studio 模型进行对话和文本生成
"""

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import requests
from typing import Dict, Any, List

class LangChainIntegration:
    def __init__(self, lm_studio_url: str = "http://192.168.2.243:1234"):
        """
        初始化 LangChain 集成
        
        Args:
            lm_studio_url (str): LM Studio 服务地址，默认为本地地址
        """
        self.lm_studio_url = lm_studio_url
        
        # 先查询本地支持的模型，取第一个模型
        model_name = self._get_first_available_model()
        
        # 创建 ChatOpenAI 实例，使用 LM Studio 的 OpenAI API 兼容接口
        self.llm = ChatOpenAI(
            base_url=lm_studio_url + "/v1",  # LM Studio 默认的 v1 接口路径
            api_key="lm-studio",  # LM Studio 不需要实际的 API key，但必须提供一个值
            model=model_name   # 使用查询到的第一个模型名称
        )
        
        # 创建简单的提示模板
        self.prompt_template = PromptTemplate.from_template(
            "你是一个数据库专家。请根据以下SQL查询结果回答用户的问题：\n\n"
            "{sql_result}\n\n"
            "请用中文回答，如果需要可以提供解释说明。"
        )
        
        # 链接处理器
        self.chain = self.prompt_template | self.llm | StrOutputParser()
    
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

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            dict: 包含模型相关信息的字典
        """
        try:
            return {
                "model_name": self.llm.model_name,
                "base_url": self.lm_studio_url,
                "status": "connected" if self.llm else "disconnected"
            }
        except Exception as e:
            print(f"获取模型信息失败: {str(e)}")
            return {
                "model_name": "unknown",
                "base_url": self.lm_studio_url,
                "status": "error"
            }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        获取LM Studio本地支持的并且被激活模型列表
        
        Returns:
            list: 可用模型信息列表
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
            
            return models
            
        except requests.exceptions.RequestException as e:
            print(f"请求模型列表失败: {str(e)}")
            return []
        except Exception as e:
            print(f"解析模型信息失败: {str(e)}")

