from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from reasoning_graph import Stage1ReasoningGraph
from info_extractor import create_info_extractor


class AgentService:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """初始化Agent服务 - 单用户版本"""
        self.model_name = model_name

        # 单一会话实例
        self.reasoning_graph: Optional[Stage1ReasoningGraph] = None

        # 信息提取器
        self.extractor = create_info_extractor(model_name)

        print(f"AgentService初始化完成，使用模型: {model_name}")

    def start_conversation(self) -> Dict[str, Any]:
        """开始对话会话"""
        # 创建新的Stage1推理图实例
        self.reasoning_graph = Stage1ReasoningGraph(self.model_name, self.extractor)

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

        # 检查会话是否存在
        if self.reasoning_graph is None:
            return {
                "error": "会话未开始，请先开始对话",
                "action": "start_session",
                "timestamp": self._get_timestamp()
            }

        try:
            # 核心处理：调用推理图处理对话轮次
            result = await self.reasoning_graph.process_conversation_turn(user_input)

            # 添加metadata字段
            result["ready_for_stage2"] = (result["next_action"] == "proceed_to_stage2")

            # 根据推理图的结果决定下一步动作
            if result["next_action"] == "proceed_to_stage2":
                # Stage1完成，但仍使用collection格式返回
                return self._format_collection_response(result)

            elif result["next_action"] == "continue_collection":
                # Stage1未完成，继续收集信息
                return self._format_collection_response(result)

            else:
                # 处理其他可能的状态
                return self._format_general_response(result)

        except Exception as e:
            print(f"处理请求时出错: {e}")
            return {
                "error": f"处理请求时出现错误: {str(e)}",
                "action": "retry",
                "timestamp": self._get_timestamp()
            }

    async def _transition_to_stage2(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """过渡到Stage2 - 生成游戏内容"""
        requirements = result["requirements"]

        # TODO: 这里将来调用Stage2和Stage3的逻辑
        # stage2_result = await self.stage2_service.generate_story_blueprint(requirements)
        # stage3_result = await self.stage3_service.generate_scenes(stage2_result)

        # 清理Stage1会话
        self.reasoning_graph = None

        return {
            "response": result["response"] + "\n\n🚀 需求收集完成！正在为您生成游戏内容，请稍候...",
            "stage": "stage1_complete",
            "next_stage": "stage2_generation",
            "requirements": requirements,
            "timestamp": self._get_timestamp(),
            "action": "generate_content"
        }

    def _format_collection_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化Stage1信息收集中的响应"""
        response_data = {
            "response": result["response"],
            "ready_for_stage2": result.get("ready_for_stage2", False),
            "timestamp": self._get_timestamp(),
        }
        
        # 如果Stage1完成，返回完成状态的信息
        if result.get("next_action") == "proceed_to_stage2":
            response_data.update({
                "stage": "stage1_complete",
                "requirement_id": result.get("requirement_id"),
                "requirements": result.get("requirements"),
                "action": "stage1_completed"
            })
        else:
            # Stage1未完成，返回收集状态的信息
            response_data.update({
                "stage": "stage1_collecting", 
                "current_stage": result["lacked_info"]["stage"],
                "missing_fields": result["lacked_info"]["missing_fields"],
                "completion_rate": result["lacked_info"]["completion_rate"],
                "action": "continue_conversation"
            })
            
        return response_data

    def _format_general_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化一般响应"""
        return {
            "response": result.get("response", "我理解了您的输入，请继续..."),
            "stage": result.get("stage", "unknown"),
            "timestamp": self._get_timestamp(),
            "action": "continue_conversation"
        }

    def get_session_status(self) -> Dict[str, Any]:
        """获取会话状态"""
        if self.reasoning_graph is None:
            return {
                "status": "no_session",
                "message": "会话未开始",
                "timestamp": self._get_timestamp()
            }

        current_stage = self.reasoning_graph.determine_current_stage()

        if current_stage == "complete":
            completion_rate = 1.0
            missing_fields = []
        else:
            lacked_info = self.reasoning_graph.get_lacked_info()
            completion_rate = lacked_info["completion_rate"]
            missing_fields = lacked_info["missing_fields"]

        return {
            "status": "active",
            "current_stage": current_stage,
            "completion_rate": completion_rate,
            "missing_fields": missing_fields,
            "collected_info": self.reasoning_graph.collected_info,
            "timestamp": self._get_timestamp()
        }

    def end_session(self) -> Dict[str, Any]:
        """结束会话"""
        if self.reasoning_graph is None:
            return {
                "status": "no_session",
                "message": "会话不存在",
                "timestamp": self._get_timestamp()
            }

        # 获取最终收集的信息
        final_info = self.reasoning_graph.collected_info

        # 清理会话
        self.reasoning_graph = None

        return {
            "status": "session_ended",
            "message": "会话已成功结束",
            "final_collected_info": final_info,
            "timestamp": self._get_timestamp()
        }

    def reset_session(self) -> Dict[str, Any]:
        """重置会话"""
        # 重新创建推理图实例
        self.reasoning_graph = Stage1ReasoningGraph(self.model_name, self.extractor)

        return {
            "status": "session_reset",
            "message": "会话已重置，让我们重新开始",
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