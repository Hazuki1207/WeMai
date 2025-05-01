import json
import logging
import time
import hashlib
import requests
from datetime import datetime
from config import MAIBOT_API_URL, PLATFORM_ID

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# MaiBot API 配置已移动到config.py

class MessageProcessor:
    def __init__(self, platform=PLATFORM_ID):
        """
        初始化消息处理器
        
        Args:
            platform (str): 消息平台标识，默认使用配置文件中的PLATFORM_ID
        """
        self.platform = platform
        logger.info(f"消息处理器初始化成功，平台：{platform}")
    
    def process_message(self, chat_name, message_data):
        """
        处理微信消息并转发到 MaiBot
        
        Args:
            chat_name (str): 聊天对象名称
            message_data (dict): 消息数据，包含 sender, content, type, timestamp 等信息
        
        Returns:
            dict: MaiBot 的响应结果
        """
        try:
            # 记录接收到的消息
            logger.info(f"处理消息: {chat_name} - {message_data['sender']}: {message_data['content']}")
            
            # 构建 MaiBot 消息体
            maibot_message = self._build_maibot_message(chat_name, message_data)
            
            # 发送消息到 MaiBot
            response = self._send_to_maibot(maibot_message)
            
            return response
        except Exception as e:
            logger.error(f"处理消息时发生错误: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _build_maibot_message(self, chat_name, message_data):
        """
        构建 MaiBot 消息体
        
        Args:
            chat_name (str): 聊天对象名称
            message_data (dict): 消息数据
        
        Returns:
            dict: MaiBot 格式的消息体
        """
        # 提取消息信息
        sender = message_data['sender']
        content = message_data['content']
        msg_type = message_data['type']
        timestamp = time.time()  # 使用当前时间戳
        
        # 判断是群聊还是私聊
        is_group_chat = not (chat_name == sender)
        
        # 生成包含用户特征的消息 ID
        # 结合发送者、聊天名称、时间戳和消息内容前20个字符生成哈希
        id_source = f"{sender}_{chat_name}_{timestamp}_{content[:20]}"
        message_id = hashlib.md5(id_source.encode('utf-8')).hexdigest()
        
        # 使用 MD5 哈希生成用户ID和群组ID
        user_id_hash = hashlib.md5(sender.encode('utf-8')).hexdigest()
        
        # 构建基本消息信息
        message_info = {
            "platform": self.platform,
            "message_id": message_id,
            "time": timestamp,
            "format_info": {
                "content_format": "text",
                "accept_format": "text,emoji"
            }
        }
        
        # 添加用户信息
        message_info["user_info"] = {
            "platform": self.platform,
            "user_id": user_id_hash,  # 使用哈希后的用户ID
            "user_nickname": sender
        }
        
        # 如果是群聊，添加群组信息
        if is_group_chat:
            # 使用 MD5 哈希生成群组ID
            group_id_hash = hashlib.md5(chat_name.encode('utf-8')).hexdigest()
            
            message_info["group_info"] = {
                "platform": self.platform,
                "group_id": group_id_hash,  # 使用哈希后的群组ID
                "group_name": chat_name
            }
            # 在群聊中，添加用户的群昵称
            message_info["user_info"]["user_cardname"] = sender
        
        # 构建消息段
        message_segment = {
            "type": "text",
            "data": content
        }
        
        # 组合完整消息体
        maibot_message = {
            "message_info": message_info,
            "message_segment": message_segment
        }
        
        return maibot_message
    
    def _send_to_maibot(self, message):
        """
        发送消息到 MaiBot API
        
        Args:
            message (dict): MaiBot 格式的消息体
        
        Returns:
            dict: API 响应结果
        """
        try:
            # 记录发送的消息
            logger.info(f"发送消息到 MaiBot: {json.dumps(message, ensure_ascii=False)}")
            
            # 发送 POST 请求
            response = requests.post(
                MAIBOT_API_URL,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                logger.info(f"MaiBot 响应成功: {json.dumps(result, ensure_ascii=False)}")
                return {"success": True, "data": result}
            else:
                logger.error(f"MaiBot 响应错误: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP错误: {response.status_code}"}
        
        except requests.RequestException as e:
            logger.error(f"发送请求到 MaiBot 时发生错误: {str(e)}")
            return {"success": False, "error": str(e)}
        except json.JSONDecodeError:
            logger.error(f"解析 MaiBot 响应时发生错误: {response.text}")
            return {"success": False, "error": "无法解析响应JSON"}
        except Exception as e:
            logger.error(f"与 MaiBot 通信时发生未知错误: {str(e)}")
            return {"success": False, "error": str(e)}


# 示例：如何使用消息处理器
if __name__ == "__main__":
    # 创建消息处理器实例
    processor = MessageProcessor()
    
    # 模拟消息数据
    chat_name = "测试群"
    message_data = {
        "sender": "张三",
        "content": "你好，机器人",
        "type": "friend",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 处理消息
    result = processor.process_message(chat_name, message_data)
    print(f"处理结果: {result}")
