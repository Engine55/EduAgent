from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
import uuid

from reasoning_graph import Stage1ReasoningGraph, ReasoningGraph, create_reasoning_graph
from info_extractor import create_info_extractor


class AgentService:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """初始化Agent服务"""
        self.model_name = model_name
        
        # 会话管理
        self.session_id = str(uuid.uuid4())
        self.user_id = "default_user"

        # 智能推理图 - 负责完整的对话推理流程
        self.reasoning_graph = create_reasoning_graph()

        # 信息提取器
        self.extractor = create_info_extractor(model_name)
        
        # 维护collected_info状态
        self.collected_info = {
            "subject": None,
            "grade": None,
            "knowledge_points": None,
            "teaching_goals": None,
            "teaching_difficulties": None,
            "game_style": None,
            "character_design": None,
            "world_setting": None,
            "plot_requirements": None,
            "interaction_requirements": None
        }
        
        # 推理状态持久化 - 只在开始新会话时初始化
        self.reasoning_state = None

        print(f"AgentService初始化完成，使用模型: {model_name}，启用智能推理")

    def start_conversation(self) -> Dict[str, Any]:
        """开始对话会话"""
        # 重新生成会话ID
        self.session_id = str(uuid.uuid4())
        
        # 初始化推理状态 - 只在开始新会话时做一次
        self.reasoning_state = self.reasoning_graph.initialize_reasoning_state(
            session_id=self.session_id,
            user_id=self.user_id,
            collected_info=self.collected_info
        )

        welcome_message = """🎮 您好！我是教育游戏设计助手！

我将通过几个简单的问题来了解您的需求，然后为您生成一个完整的RPG教育游戏设计方案。

让我们开始吧！请告诉我：
- 这个游戏是给哪个年级的学生设计的？
- 主要想教授哪个学科的内容？
- 有特定的知识点需要重点关注吗？

您可以一次回答所有问题，也可以逐一回答 😊"""

        return {
            "message": welcome_message,
            "status": "session_started",
            "timestamp": self._get_timestamp(),
            "next_action": "await_user_input"
        }

    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """处理用户请求 - 核心业务逻辑"""

        try:
            # 1. 提取用户输入中的信息并更新状态
            extracted_info = await self._extract_and_update_info(user_input)
            print(f"DEBUG: 提取到的信息: {extracted_info}")
            print(f"DEBUG: 当前collected_info: {self.collected_info}")
            
            # 2. 调用ReasoningGraph进行智能推理
            reasoning_result = await self.reasoning_graph.process_reasoning_request(
                session_id=self.session_id,
                user_id=self.user_id,
                collected_info=self.collected_info
            )
            
            print(f"DEBUG: 推理结果: {reasoning_result}")
            
            # 3. 格式化并返回结果
            return self._format_reasoning_response(reasoning_result, user_input)

        except Exception as e:
            print(f"处理请求时出错: {e}")
            return {
                "error": f"处理请求时出现错误: {str(e)}",
                "action": "retry",
                "timestamp": self._get_timestamp()
            }


    def reset_session(self) -> Dict[str, Any]:
        """重置会话"""
        # 重新生成会话ID并清空collected_info
        self.session_id = str(uuid.uuid4())
        self.collected_info = {
            "subject": None,
            "grade": None,
            "knowledge_points": None,
            "teaching_goals": None,
            "teaching_difficulties": None,
            "game_style": None,
            "character_design": None,
            "world_setting": None,
            "plot_requirements": None,
            "interaction_requirements": None
        }
        
        # 重置推理状态
        self.reasoning_state = self.reasoning_graph.initialize_reasoning_state(
            session_id=self.session_id,
            user_id=self.user_id,
            collected_info=self.collected_info
        )

        return {
            "status": "session_reset",
            "message": "会话已重置，让我们重新开始",
            "timestamp": self._get_timestamp()
        }

    async def _extract_and_update_info(self, user_input: str) -> Dict[str, Any]:
        """提取用户输入信息并更新collected_info状态"""
        
        # 使用信息提取器提取信息
        extracted_info = await self.extractor.extract_from_user_input(user_input)
        
        # 更新collected_info状态
        for key, value in extracted_info.items():
            if value and key in self.collected_info:
                if isinstance(value, list):
                    # 处理列表类型的数据
                    if self.collected_info[key]:
                        # 合并列表，去重
                        existing = self.collected_info[key] if isinstance(self.collected_info[key], list) else [self.collected_info[key]]
                        combined = existing + value
                        self.collected_info[key] = list(set(combined))
                    else:
                        self.collected_info[key] = value
                else:
                    # 处理字符串类型的数据
                    self.collected_info[key] = value
        
        return extracted_info

    def _format_reasoning_response(self, reasoning_result: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """格式化ReasoningGraph的返回结果"""
        
        if not reasoning_result.get("success"):
            return {
                "error": reasoning_result.get("error", "推理处理失败"),
                "action": "retry",
                "timestamp": self._get_timestamp()
            }
        
        final_state = reasoning_result["final_state"]
        stage = reasoning_result["stage"]
        messages = reasoning_result.get("messages", [])
        
        # 获取最后一条助手消息作为回复
        assistant_message = ""
        if messages:
            last_message = messages[-1]
            if last_message.get("role") == "assistant":
                assistant_message = last_message.get("content", "")
        
        # 根据stage确定返回格式
        if stage == "ready_for_generation":
            return {
                "response": assistant_message,
                "ready_for_stage2": True,
                "stage": "stage1_complete",
                "requirement_id": final_state.get("session_id"),
                "final_requirements": final_state.get("final_requirements", {}),
                "action": "stage1_completed",
                "timestamp": self._get_timestamp()
            }
        else:
            return {
                "response": assistant_message,
                "ready_for_stage2": False,
                "stage": "stage1_collecting",
                "current_reasoning_stage": stage,
                "action": "continue_conversation",
                "timestamp": self._get_timestamp()
            }

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 便利函数
def create_agent_service(model_name: str = "gpt-4o-mini") -> AgentService:
    """创建Agent服务的便利函数"""
    return AgentService(model_name)


# 演示函数
async def demo_conversation():
    """演示完整的对话流程"""
    agent = create_agent_service()

    print("=== 教育游戏设计助手演示 ===")

    # 开始会话
    start_result = agent.start_conversation()
    print(f"助手: {start_result['message']}")

    # 模拟用户输入
    test_inputs = [
        "我想为三年级学生做一个数学游戏",
        "重点是10以内的加法，很多学生容易算错",
        ""
    ]

    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n第{i}轮对话:")
        print(f"用户: {user_input}")

        result = await agent.process_request(user_input)
        print(f"助手: {result['response']}")

        if result.get("action") == "generate_content":
            print("\n🎉 Stage1完成，准备生成游戏内容！")
            print(f"收集到的需求: {result['requirements']}")
            break

        # 显示当前进度
        if "completion_rate" in result:
            progress = result["completion_rate"] * 100
            print(f"进度: {progress:.1f}%")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_conversation())