from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
import uuid

from reasoning_graph import create_reasoning_graph
from info_extractor import create_info_extractor
from database_client import DatabaseClient


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
        
        # 数据库客户端
        self.db_client = DatabaseClient()
        
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

        welcome_message = """您好！我是教育游戏设计助手！

我将通过几个简单的问题来了解您的需求，然后为您生成一个完整的RPG教育游戏设计方案。

让我们开始吧！请告诉我：
- 这个游戏是给哪个年级的学生设计的？
- 主要想教授哪个学科的内容？
- 有特定的知识点需要重点关注吗？

您可以一次回答所有问题，也可以逐一回答"""

        return {
            "message": welcome_message,
            "status": "session_started",
            "timestamp": self._get_timestamp(),
            "next_action": "await_user_input"
        }

    async def process_request(self, user_input: str) -> Dict[str, Any]:
        """处理用户请求 - 使用状态持久化"""

        try:
            # 确保推理状态已初始化
            if self.reasoning_state is None:
                self.reasoning_state = self.reasoning_graph.initialize_reasoning_state(
                    session_id=self.session_id,
                    user_id=self.user_id,
                    collected_info=self.collected_info
                )
            
            # 使用持久化状态处理请求
            reasoning_result = await self.reasoning_graph.process_reasoning_request_with_state(
                reasoning_state=self.reasoning_state,
                user_input=user_input
            )
            
            print(f"DEBUG: 推理结果: {reasoning_result}")
            
            # 更新持久化的状态
            if reasoning_result.get("success"):
                self.reasoning_state = reasoning_result["final_state"]
                # 同步更新collected_info
                self.collected_info = self.reasoning_state.get("collected_info", {})
            
            # 格式化并返回结果
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
        ready_for_generation = reasoning_result.get("ready_for_generation", False)
        
        # 获取最后一条助手消息作为回复
        assistant_message = ""
        analysis_report = None
        story_framework = None
        if messages:
            last_message = messages[-1]
            if last_message.get("role") == "assistant":
                assistant_message = last_message.get("content", "")
                analysis_report = last_message.get("analysis_report")  # 提取分析报告
                story_framework = last_message.get("story_framework")  # 提取故事框架
        
        # 提取关卡生成数据
        level_details = final_state.get("level_details", {})
        level_generation_status = final_state.get("level_generation_status", "pending")
        
        # 转换level_details为前端期望的storyboards格式
        storyboards_data = self._convert_level_details_to_storyboards(level_details, final_state)
        
        # 根据生成状态确定返回格式
        if level_generation_status == "completed":
            # 关卡生成完成，保存storyboard数据到数据库
            requirement_id = final_state.get("requirement_id", self.session_id)
            self._save_storyboard_to_database(requirement_id, storyboards_data, story_framework, final_state)
            
            return {
                "response": assistant_message,
                "ready_for_stage2": True,
                "stage": "all_levels_complete",
                "requirement_id": requirement_id,
                "final_requirements": final_state.get("final_requirements", {}),
                "collected_info": final_state.get("collected_info", {}),
                "analysis_report": analysis_report,
                "story_framework": story_framework,
                "level_details": level_details,  # 原始关卡数据（调试用）
                "storyboards_data": storyboards_data,  # 转换后的前端格式数据
                "level_generation_status": level_generation_status,
                "action": "all_content_generated",
                "timestamp": self._get_timestamp()
            }
        elif ready_for_generation:
            # 故事框架完成，准备生成关卡
            return {
                "response": assistant_message,
                "ready_for_stage2": True,
                "stage": "stage1_complete",
                "requirement_id": final_state.get("requirement_id", self.session_id),
                "final_requirements": final_state.get("final_requirements", {}),
                "collected_info": final_state.get("collected_info", {}),
                "analysis_report": analysis_report,
                "story_framework": story_framework,
                "level_details": level_details,  # 原始关卡数据（调试用）
                "storyboards_data": storyboards_data,  # 转换后的前端格式数据
                "level_generation_status": level_generation_status,
                "action": "stage1_completed",
                "timestamp": self._get_timestamp()
            }
        else:
            # 还在收集阶段，根据具体stage返回不同信息
            stage_display_names = {
                "stage1_collecting": "信息收集中",
                "need_more_details": "需要更多详细信息",
                "fitness_check": "内容适宜性检查中",
                "unknown": "处理中"
            }
            
            return {
                "response": assistant_message,
                "ready_for_stage2": False,
                "stage": "stage1_collecting",
                "current_reasoning_stage": stage,
                "stage_display": stage_display_names.get(stage, stage),
                "collected_info": final_state.get("collected_info", {}),
                "analysis_report": analysis_report,  # 添加分析报告
                "story_framework": story_framework,  # 添加故事框架
                "level_details": level_details,  # 原始关卡数据（调试用）
                "storyboards_data": storyboards_data,  # 转换后的前端格式数据
                "level_generation_status": level_generation_status,
                "action": "continue_conversation",
                "timestamp": self._get_timestamp()
            }

    def get_session_status(self) -> Dict[str, Any]:
        """获取当前会话状态"""
        if self.reasoning_state is None:
            return {
                "status": "not_initialized",
                "message": "会话未初始化",
                "timestamp": self._get_timestamp()
            }
        
        # 计算完成度
        total_fields = len(self.collected_info)
        completed_fields = sum(1 for v in self.collected_info.values() if v is not None and v != [] and v != "")
        completion_rate = completed_fields / total_fields if total_fields > 0 else 0
        
        return {
            "status": "active",
            "session_id": self.session_id,
            "user_id": self.user_id,
            "completion_rate": completion_rate,
            "collected_info": self.collected_info,
            "ready_for_generation": self.reasoning_state.get("ready_for_generation", False),
            "current_stage": self.reasoning_state.get("current_stage", "unknown"),
            "timestamp": self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _save_storyboard_to_database(self, requirement_id: str, storyboards_data: dict, story_framework: str, final_state: dict) -> bool:
        """保存storyboard数据到数据库"""
        try:
            if not self.db_client:
                print("数据库客户端未初始化，无法保存storyboard数据")
                return False
            
            # 准备完整的storyboard数据
            story_data = {
                "requirement_id": requirement_id,
                "story_framework": story_framework,
                "storyboards_data": storyboards_data,
                "collected_info": final_state.get("collected_info", {}),
                "level_details": final_state.get("level_details", {}),
                "level_generation_status": "completed",
                "generated_at": self._get_timestamp()
            }
            
            # 生成story_id（基于requirement_id）
            story_id = f"story_{requirement_id}"
            
            # 保存到数据库
            result = self.db_client.save_story(
                story_id=story_id,
                requirement_id=requirement_id,
                story_data=story_data
            )
            
            if result.get("success"):
                print(f"storyboard数据已保存到数据库，story_id: {story_id}")
                return True
            else:
                print(f"保存storyboard数据失败: {result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"保存storyboard数据时出错: {e}")
            return False
    
    def _convert_level_details_to_storyboards(self, level_details: Dict[str, Any], final_state: Dict[str, Any]) -> Dict[str, Any]:
        """将level_details转换为前端期望的storyboards格式"""
        
        try:
            import json
            
            storyboards = []
            
            # 从final_state获取基础信息
            story_framework = final_state.get("story_framework", "")
            collected_info = final_state.get("collected_info", {})
            
            # 提取故事标题（从story_framework中解析或使用默认）
            story_title = "RPG教育游戏"  # 可以后续从story_framework解析
            
            for level in range(1, 7):
                level_key = f"level_{level}"
                if level_key not in level_details:
                    continue
                    
                level_data = level_details[level_key]
                
                # 解析场景数据JSON
                scene_json = {}
                if "scenes_script" in level_data and level_data["scenes_status"] == "completed":
                    try:
                        scenes_content = level_data["scenes_script"]
                        # 提取JSON部分（去除markdown格式）
                        if "```json" in scenes_content:
                            json_start = scenes_content.find("```json") + 7
                            json_end = scenes_content.find("```", json_start)
                            if json_end != -1:
                                json_str = scenes_content[json_start:json_end].strip()
                                scene_json = json.loads(json_str)
                    except Exception as e:
                        print(f"⚠️ 第{level}关卡场景JSON解析失败: {e}")
                
                # 解析角色数据JSON
                character_json = {}
                if "characters_dialogue" in level_data and level_data["characters_status"] == "completed":
                    try:
                        characters_content = level_data["characters_dialogue"]
                        # 提取JSON部分（去除markdown格式）
                        if "```json" in characters_content:
                            json_start = characters_content.find("```json") + 7
                            json_end = characters_content.find("```", json_start)
                            if json_end != -1:
                                json_str = characters_content[json_start:json_end].strip()
                                character_json = json.loads(json_str)
                    except Exception as e:
                        print(f"⚠️ 第{level}关卡角色JSON解析失败: {e}")
                
                # 合并scene和character数据
                storyboard_data = {}
                
                # 从scene_json提取数据
                if scene_json:
                    storyboard_data["分镜基础信息"] = scene_json.get("分镜基础信息", {})
                    storyboard_data["图片提示词"] = scene_json.get("图片生成提示词", {})
                    storyboard_data["剧本"] = scene_json.get("剧本", {})
                
                # 从character_json提取数据
                if character_json:
                    storyboard_data["人物档案"] = character_json.get("人物档案", {})
                    storyboard_data["人物对话"] = character_json.get("人物对话", [])
                
                # 生成stage_name（从分镜标题提取或使用默认）
                stage_name = f"关卡{level}"
                if storyboard_data.get("分镜基础信息", {}).get("分镜标题"):
                    title = storyboard_data["分镜基础信息"]["分镜标题"]
                    if "-" in title:
                        stage_name = title.split("-", 1)[1].strip()
                
                # 构建单个storyboard
                storyboard_item = {
                    "stage_index": level,
                    "stage_name": stage_name,
                    "stage_id": level_key,
                    "storyboard": storyboard_data,
                    # 可选字段
                    "teachingGoal": collected_info.get("teaching_goals", ["未指定"])[0] if collected_info.get("teaching_goals") else "未指定",
                    "generation_status": {
                        "storyboard": "success" if (scene_json and character_json) else "failed",
                        "scene": "success" if scene_json else "failed", 
                        "dialogue": "success" if character_json else "failed"
                    }
                }
                
                storyboards.append(storyboard_item)
            
            # 构建完整的返回数据
            return {
                "story_id": self.session_id,
                "story_title": story_title,
                "subject": collected_info.get("subject", "未知"),
                "grade": collected_info.get("grade", "未知"),
                "storyboards": storyboards
            }
            
        except Exception as e:
            print(f"❌ 转换storyboards数据失败: {e}")
            return {
                "story_id": self.session_id,
                "story_title": "转换失败",
                "subject": "未知",
                "grade": "未知", 
                "storyboards": []
            }


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