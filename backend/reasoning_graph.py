from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory  
from langchain_openai import ChatOpenAI
from typing import Dict, List, TypedDict, Any
import json
import hashlib
from datetime import datetime
from langgraph.graph import StateGraph, END
import os

from database_client import db_client


class Stage1ReasoningGraph:
    def __init__(self, model_name="gpt-4o-mini", extractor=None, user_id="1"):
        """初始化Stage1推理图"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.llm = ChatOpenAI(
            model=model_name, 
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.extractor = extractor
        self.user_id = str(user_id)  # 确保是字符串格式

        # 初始化Memory
        self.memory = ConversationSummaryBufferMemory(
            max_token_limit=8000,
            llm=self.llm,
            return_messages=True
        )

        # 收集的信息存储
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

        # 完成条件定义
        self.completion_criteria = {
            "basic_info": ["subject", "grade", "knowledge_points"],
            "teaching_info": ["teaching_goals", "teaching_difficulties"],
            "gamestyle_info": ["game_style", "character_design", "world_setting"],
            "scene_info": ["plot_requirements", "interaction_requirements"]
        }

        # 导入prompt模板
        from prompt_templates import PromptTemplates
        self.prompts = PromptTemplates()
        
        # 初始化数据库连接
        try:
            self.db_client = db_client
            print("✅ 数据库连接成功")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            self.db_client = None

    async def process_conversation_turn(self, user_input: str) -> Dict:
        """处理一轮对话的完整流程"""
        
        # 确定当前阶段
        current_stage = self.determine_current_stage()
        
        # 只在未完成时提取信息
        if current_stage != "complete":
            # 1. 根据当前阶段提取信息
            extracted_info = await self.extract_info(user_input, current_stage)
        else:
            extracted_info = {}

        # 2. 更新状态
        self.update_state(extracted_info)

        # 3. 检查是否达成Stage1目标
        if self.check_stage_completion():
            print("progress 1 completed")
            
            # Stage1完成，保存需求信息
            save_result = self.save_final_requirements()
            if save_result["success"]:
                print(f"✅ 需求信息已保存: {save_result['requirement_id']}")
            else:
                print(f"❌ 保存失败: {save_result['message']}")
            
            # Stage1完成
            response = self.generate_stage_completion_response()
            return {
                "response": response,
                "stage": "stage1_complete",
                "next_action": "proceed_to_stage2",
                "requirements": self.get_final_requirements(),
                "save_result": save_result,
                "requirement_id": save_result.get("requirement_id", None)
            }
        else:
            # Stage1未完成，继续收集
            lacked_info = self.get_lacked_info()
            response = await self.generate_response_with_lacked_info(lacked_info)
            return {
                "response": response,
                "stage": "stage1_collecting",
                "next_action": "continue_collection",
                "lacked_info": lacked_info,
                # "progress": self.get_progress_summary()
            }

    async def extract_info(self, user_input: str, stage: str = "basic_info") -> Dict:
        """提取用户输入中的信息"""
        return await self.extractor.extract_from_user_input(user_input, stage)

    def update_state(self, extracted_info: Dict) -> None:
        """更新收集状态"""
        print(f"DEBUG update_state: received = {extracted_info}")
        for key, value in extracted_info.items():
            print(f"DEBUG: processing key={key}, value={value}")
            if value and key in self.collected_info:
                if isinstance(value, list):
                    # 处理列表类型的数据
                    if self.collected_info[key]:
                        # 合并列表，去重
                        existing = self.collected_info[key] if isinstance(self.collected_info[key], list) else [
                            self.collected_info[key]]
                        combined = existing + value
                        self.collected_info[key] = list(set(combined))
                    else:
                        self.collected_info[key] = value
                else:
                    # 处理字符串类型的数据
                    self.collected_info[key] = value
                print(f"DEBUG: updated {key} -> {self.collected_info[key]}")
            else:
                print(f"DEBUG: skipped {key} (empty value or key not found)")
        
        print(f"DEBUG: final collected_info = {self.collected_info}")
        print("="*50)

    def check_stage_completion(self) -> bool:
        """检查Stage1是否完成"""
        all_stages = ["basic_info", "teaching_info", "gamestyle_info", "scene_info"]

        for stage in all_stages:
            required_fields = self.completion_criteria[stage]
            for field in required_fields:
                value = self.collected_info.get(field)
                if not value:  # None 或空列表都算未完成
                    return False
                if isinstance(value, list) and len(value) == 0:
                    return False
                print(f"{stage} finished")

        return True


    def determine_current_stage(self) -> str:
        """确定当前应该收集哪个阶段的信息"""
        if not self._stage_completed("basic_info"):
            return "basic_info"
        elif not self._stage_completed("teaching_info"):
            return "teaching_info"
        elif not self._stage_completed("gamestyle_info"):
            return "gamestyle_info"
        elif not self._stage_completed("scene_info"):
            return "scene_info"
        else:
            return "complete"

    def _stage_completed(self, stage: str) -> bool:
        """检查特定阶段是否完成"""
        required_fields = self.completion_criteria[stage]
        for field in required_fields:
            value = self.collected_info.get(field)
            if not value:
                return False
            if isinstance(value, list) and len(value) == 0:
                return False
        return True

    def get_lacked_info(self) -> Dict:
        """获取缺失信息详情"""
        current_stage = self.determine_current_stage()

        if current_stage == "complete":
            return {"stage": "complete", "missing_fields": [], "missing_details": {}, "completion_rate": 1.0}

        # 根据当前阶段获取缺失信息
        if current_stage == "basic_info":
            return self._check_basic_info_gaps()
        elif current_stage == "teaching_info":
            return self._check_teaching_info_gaps()
        elif current_stage == "gamestyle_info":
            return self._check_gamestyle_info_gaps()
        elif current_stage == "scene_info":
            return self._check_scene_info_gaps()

        return {"stage": current_stage, "missing_fields": [], "missing_details": {}, "completion_rate": 0.0}

    def _check_basic_info_gaps(self) -> Dict:
        """检查基础信息缺失"""
        missing = []
        details = {}

        if not self.collected_info.get("subject"):
            missing.append("subject")
            details["subject"] = "需要确定学科领域（如：数学、语文、英语、科学等）"

        if not self.collected_info.get("grade"):
            missing.append("grade")
            details["grade"] = "需要确定年级段（如：一年级、二年级、三年级等）"

        knowledge_points = self.collected_info.get("knowledge_points")
        if not knowledge_points or (isinstance(knowledge_points, list) and len(knowledge_points) == 0):
            missing.append("knowledge_points")
            details["knowledge_points"] = "需要明确具体知识点（如：10以内加法、汉语拼音、英语字母等）"

        total_fields = len(self.completion_criteria["basic_info"])
        completed_fields = total_fields - len(missing)
        completion_rate = completed_fields / total_fields if total_fields > 0 else 0

        return {
            "stage": "basic_info",
            "missing_fields": missing,
            "missing_details": details,
            "completion_rate": completion_rate
        }

    def _check_teaching_info_gaps(self) -> Dict:
        """检查教学信息缺失"""
        missing = []
        details = {}

        # 调试输出
        print(f"DEBUG: collected_info = {self.collected_info}")
        
        teaching_goals = self.collected_info.get("teaching_goals")
        if not teaching_goals or (isinstance(teaching_goals, list) and len(teaching_goals) == 0):
            missing.append("teaching_goals")
            details["teaching_goals"] = "需要明确教学目标（学生通过游戏要达到什么学习效果）"

        teaching_difficulties = self.collected_info.get("teaching_difficulties")
        if not teaching_difficulties or (isinstance(teaching_difficulties, list) and len(teaching_difficulties) == 0):
            missing.append("teaching_difficulties")
            details["teaching_difficulties"] = "需要了解教学难点（学生在这个知识点上的常见困难）"

        total_fields = len(self.completion_criteria["teaching_info"])
        completed_fields = total_fields - len(missing)
        completion_rate = completed_fields / total_fields if total_fields > 0 else 0

        return {
            "stage": "teaching_info",
            "missing_fields": missing,
            "missing_details": details,
            "completion_rate": completion_rate
        }

    def _check_gamestyle_info_gaps(self) -> Dict:
        """检查游戏风格信息缺失"""
        missing = []
        details = {}

        if not self.collected_info.get("game_style"):
            missing.append("game_style")
            details["game_style"] = "需要确定游戏风格（如：魔法冒险、科幻探索、童话故事等）"

        if not self.collected_info.get("character_design"):
            missing.append("character_design")
            details["character_design"] = "需要设计角色形象（如：可爱的小动物、勇敢的小勇士等）"

        if not self.collected_info.get("world_setting"):
            missing.append("world_setting")
            details["world_setting"] = "需要确定世界观背景（如：魔法王国、未来世界、童话森林等）"

        total_fields = len(self.completion_criteria["gamestyle_info"])
        completed_fields = total_fields - len(missing)
        completion_rate = completed_fields / total_fields if total_fields > 0 else 0

        return {
            "stage": "gamestyle_info",
            "missing_fields": missing,
            "missing_details": details,
            "completion_rate": completion_rate
        }

    def _check_scene_info_gaps(self) -> Dict:
        """检查场景信息缺失"""
        missing = []
        details = {}

        plot_requirements = self.collected_info.get("plot_requirements")
        if not plot_requirements or (isinstance(plot_requirements, list) and len(plot_requirements) == 0):
            missing.append("plot_requirements")
            details["plot_requirements"] = """需要详细描述情节需求，包括：
            1. 故事主线：主角的目标和动机（如：拯救被困的朋友、寻找失落的宝藏、完成学习任务）
            2. 情节结构：故事发展方式（如：线性闯关、分支选择、开放探索）
            3. 冲突设置：学习挑战的呈现形式（如：解谜障碍、知识竞赛、合作任务）
            4. 角色关系：主角与NPC的互动类型（如：师生关系、伙伴协作、竞争对手）
            5. 情感基调：希望营造的氛围（如：轻松愉快、紧张刺激、温馨感人）"""

        interaction_requirements = self.collected_info.get("interaction_requirements")
        if not interaction_requirements or (
                isinstance(interaction_requirements, list) and len(interaction_requirements) == 0):
            missing.append("interaction_requirements")
            details["interaction_requirements"] = "需要确定互动方式（如：选择题答题、拖拽操作、语音交互等）"

        total_fields = len(self.completion_criteria["scene_info"])
        completed_fields = total_fields - len(missing)
        completion_rate = completed_fields / total_fields if total_fields > 0 else 0

        return {
            "stage": "scene_info",
            "missing_fields": missing,
            "missing_details": details,
            "completion_rate": completion_rate
        }

    def generate_stage_completion_response(self) -> str:
        """生成Stage1完成的确认回复"""
        requirements_summary = self._format_final_requirements()

        completion_response = f"""🎉 太棒了！教育游戏需求收集已经完成！

让我为您总结一下收集到的完整信息：

{requirements_summary}

请确认以上信息是否准确？如果需要修改任何内容，请告诉我具体要调整的地方。

如果信息无误，我将开始为您生成完整的游戏设计方案，包括：
- 详细的游戏剧本和故事线
- 每个场景的具体设计
- 角色对话和互动内容
- 教育目标的融入方式

请回复"确认无误"开始生成，或指出需要修改的内容。"""

        return completion_response


    async def generate_response_with_lacked_info(self, lacked_info: Dict) -> str:
        """基于缺失信息生成回复"""
        # 获取动态prompt
        dynamic_prompt = self.prompts.generate_dynamic_prompt(
            lacked_info["stage"],
            self.collected_info,
            lacked_info
        )
        print(f"dynamic prompt is : {dynamic_prompt}")
        # 创建对话链
        conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=dynamic_prompt
        )

        # 构建上下文输入，让AI知道要重点收集什么信息
        missing_fields_str = "、".join(
            [lacked_info["missing_details"][field] for field in lacked_info["missing_fields"]])
        context_input = f"继续对话，重点了解：{missing_fields_str}"
        print(f"context input is {context_input}")
        response = await conversation.apredict(input=context_input)
        return response
    #
    # def get_progress_summary(self) -> Dict:
    #     """获取整体进度摘要"""
    #     all_stages = ["basic_info", "teaching_info", "gamestyle_info", "scene_info"]
    #     progress = {}
    #
    #     for stage in all_stages:
    #         if stage == self.determine_current_stage():
    #             # 当前阶段获取详细进度
    #             lacked_info = self.get_lacked_info()
    #             progress[stage] = {
    #                 "completion_rate": lacked_info["completion_rate"],
    #                 "missing_count": len(lacked_info["missing_fields"]),
    #                 "status": "current"
    #             }
    #         elif self._stage_completed(stage):
    #             progress[stage] = {
    #                 "completion_rate": 1.0,
    #                 "missing_count": 0,
    #                 "status": "completed"
    #             }
    #         else:
    #             required_fields = self.completion_criteria[stage]
    #             completed = sum(1 for field in required_fields if self.collected_info.get(field))
    #             progress[stage] = {
    #                 "completion_rate": completed / len(required_fields),
    #                 "missing_count": len(required_fields) - completed,
    #                 "status": "pending"
    #             }
    #
    #     # 计算整体进度
    #     total_completion = sum(p["completion_rate"] for p in progress.values()) / len(progress)
    #     progress["overall"] = {
    #         "completion_rate": total_completion,
    #         "current_stage": self.determine_current_stage()
    #     }
    #
    #     return progress

    def get_final_requirements(self) -> Dict:
        """获取最终需求文档"""
        return {
            "basic_info": {
                "subject": self.collected_info["subject"],
                "grade": self.collected_info["grade"],
                "knowledge_points": self.collected_info["knowledge_points"]
            },
            "teaching_info": {
                "teaching_goals": self.collected_info["teaching_goals"],
                "teaching_difficulties": self.collected_info["teaching_difficulties"]
            },
            "gamestyle_info": {
                "game_style": self.collected_info["game_style"],
                "character_design": self.collected_info["character_design"],
                "world_setting": self.collected_info["world_setting"]
            },
            "scene_info": {
                "plot_requirements": self.collected_info["plot_requirements"],
                "interaction_requirements": self.collected_info["interaction_requirements"]
            },
            "metadata": {
                "completion_date": self._get_current_timestamp(),
                "total_fields_collected": sum(1 for v in self.collected_info.values() if v)
            }
        }

    def _format_final_requirements(self) -> str:
        """格式化最终需求为易读文本"""

        # 注意：数据库保存将在 save_final_requirements() 中统一执行
        
        sections = []

        # 基础信息
        sections.append("📚 基础信息：")
        sections.append(f"  学科：{self.collected_info['subject']}")
        sections.append(f"  年级：{self.collected_info['grade']}")
        if self.collected_info['knowledge_points']:
            points = "、".join(self.collected_info['knowledge_points'])
            sections.append(f"  知识点：{points}")

        # 教学信息
        sections.append("\n🎯 教学信息：")
        if self.collected_info['teaching_goals']:
            goals = "、".join(self.collected_info['teaching_goals'])
            sections.append(f"  教学目标：{goals}")
        if self.collected_info['teaching_difficulties']:
            difficulties = "、".join(self.collected_info['teaching_difficulties'])
            sections.append(f"  教学难点：{difficulties}")

        # 游戏设定
        sections.append("\n🎮 游戏设定：")
        sections.append(f"  游戏风格：{self.collected_info['game_style']}")
        sections.append(f"  角色设计：{self.collected_info['character_design']}")
        sections.append(f"  世界背景：{self.collected_info['world_setting']}")

        # 情节需求  
        sections.append("\n📖 情节需求：")
        if self.collected_info['plot_requirements']:
            plots = "、".join(self.collected_info['plot_requirements'])
            sections.append(f"  情节发展：{plots}")
        if self.collected_info['interaction_requirements']:
            interactions = "、".join(self.collected_info['interaction_requirements'])
            sections.append(f"  互动方式：{interactions}")

        return "\n".join(sections)
    def save_final_requirements(self) -> Dict:
        """保存最终收集的需求信息到数据库"""
        try:
            # 检查数据库连接
            if not self.db_client:
                return {
                    "success": False,
                    "message": "数据库未连接，无法保存",
                    "timestamp": self._get_current_timestamp()
                }
            
            # 生成唯一ID
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.md5(json.dumps(self.collected_info, sort_keys=True).encode()).hexdigest()[:8]
            requirement_id = f"requirement_{timestamp}_{content_hash}"
            
            # 准备保存的数据
            requirement_data = {
                "id": requirement_id,
                "user_id": self.user_id,
                "timestamp": timestamp,
                "collected_info": self.collected_info,
                "summary": {
                    "subject": self.collected_info.get("subject"),
                    "grade": self.collected_info.get("grade"),
                    "knowledge_points_count": len(self.collected_info.get("knowledge_points", [])),
                    "completion_status": "completed"
                },
                "metadata": {
                    "total_fields_collected": sum(1 for v in self.collected_info.values() if v),
                    "stages_completed": ["basic_info", "teaching_info", "gamestyle_info", "scene_info"]
                }
            }
            
            # 保存到数据库
            result = self.db_client.save_requirement(requirement_id, self.user_id, requirement_data)
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": f"需求信息保存成功: {requirement_id}",
                    "requirement_id": requirement_id,
                    "saved_fields": list(k for k, v in self.collected_info.items() if v),
                    "total_fields": len([v for v in self.collected_info.values() if v]),
                    "timestamp": timestamp
                }
            else:
                return {
                    "success": False,
                    "message": f"保存失败: {result.get('error')}",
                    "error": result.get('error'),
                    "timestamp": self._get_current_timestamp()
                }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"保存失败: {str(e)}",
                "error": str(e),
                "timestamp": self._get_current_timestamp()
            }

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def reset_conversation(self) -> None:
        """重置对话状态"""
        self.collected_info = {key: None for key in self.collected_info.keys()}
        self.memory.clear()


# 辅助函数
def create_stage1_reasoning_graph(model_name: str = "gpt-4o-mini"):
    """创建Stage1推理图实例的便利函数"""
    from langchain_openai import ChatOpenAI
    from info_extractor import InfoExtractor

    llm = ChatOpenAI(model=model_name, temperature=0.7)
    extractor = InfoExtractor(llm)

    return Stage1ReasoningGraph(llm, extractor)


# ==================== 新增：StateGraph版本的ReasoningGraph ====================

class ReasoningState(TypedDict):
    """ReasoningGraph的状态定义"""
    # 基础会话状态
    session_id: str
    messages: List[Dict[str, str]]
    user_id: str
    
    # 需求收集状态
    collected_info: Dict[str, Any]
    stage1_complete: bool
    
    # 详细度评估状态
    sufficiency_score: Dict[str, float]  # 各维度sufficiency评分
    overall_sufficiency: float           # 总体sufficiency评分
    sufficiency_threshold: float         # 阈值 (默认75)
    sufficiency_passed: bool
    
    # 适宜性检查状态
    fitness_assessment: Dict[str, Any]
    fitness_concerns: List[Dict[str, str]]
    fitness_passed: bool
    
    # 最终状态
    ready_for_generation: bool
    final_requirements: Dict[str, Any]


class ReasoningGraph:
    """基于StateGraph的智能推理图"""
    
    def __init__(self, db_client=None):
        self.db_client = db_client or db_client
        
        # 初始化LLM
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.3,  # 评估时使用较低温度
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # 初始化信息提取器
        from info_extractor import create_info_extractor
        self.extractor = create_info_extractor("gpt-4o-mini")
        
        # 初始化Stage1ReasoningGraph实例，复用状态
        self.stage1_graph = Stage1ReasoningGraph("gpt-4o-mini", self.extractor)
        
        self.graph = self._build_reasoning_graph()
    
    def _build_reasoning_graph(self) -> StateGraph:
        """构建推理状态图"""
        
        workflow = StateGraph(ReasoningState)
        
        # ==================== 节点定义 ====================
        
        # 阶段1：检查基础信息完整性
        workflow.add_node("check_info_completed", self._check_info_completed)
        workflow.add_node("generate_lack_response", self._generate_lack_response)
        
        # 阶段2：检查信息详细度充足性
        workflow.add_node("need_more_details", self._assess_sufficiency)
        workflow.add_node("generate_need_more_details_response", self._generate_sufficiency_questions)
        
        # 阶段3：检查内容适宜性
        workflow.add_node("check_fitness", self._check_fitness)
        workflow.add_node("generate_negotiate_response", self._generate_negotiate_response)
        
        # 最终完成阶段
        workflow.add_node("generate_finish_response", self._generate_finish_response)
        
        # ==================== 流程路由 ====================
        
        # 设置入口点
        workflow.set_entry_point("check_info_completed")
        
        # 阶段1路由：检查基础信息完整性
        workflow.add_conditional_edges(
            "check_info_completed",
            self._decide_after_info_check,
            {
                "info_incomplete": "generate_lack_response",
                "info_complete": "need_more_details"
            }
        )
        
        # 基础信息不足时，生成回复后结束（等待用户补充）
        workflow.add_edge("generate_lack_response", END)
        
        # 阶段2路由：检查详细度充足性
        workflow.add_conditional_edges(
            "need_more_details",
            self._decide_after_sufficiency_check,
            {
                "need_more_details": "generate_need_more_details_response",
                "sufficiency_passed": "check_fitness"
            }
        )
        
        # 需要更多细节时，生成问题后结束（等待用户回答）
        workflow.add_edge("generate_need_more_details_response", END)
        
        # 阶段3路由：检查适宜性
        workflow.add_conditional_edges(
            "check_fitness",
            self._decide_after_fitness_check,
            {
                "fitness_concerns": "generate_negotiate_response",
                "fitness_passed": "generate_finish_response"
            }
        )
        
        # 有适宜性问题时，生成协商回复后结束（等待用户回应）
        workflow.add_edge("generate_negotiate_response", END)
        
        # 所有检查通过，生成完成回复后结束
        workflow.add_edge("generate_finish_response", END)
        
        # 编译图
        return workflow.compile()
    
    # ==================== 决策逻辑 ====================
    
    def _decide_after_info_check(self, state: ReasoningState) -> str:
        """阶段1决策：检查基础信息完整性后的路由"""
        
        if state["stage1_complete"]:
            print("✅ Stage1信息收集完成，进入详细度评估")
            return "info_complete"
        else:
            print("❌ Stage1信息不完整，需要补充基础信息")
            return "info_incomplete"

    def _decide_after_sufficiency_check(self, state: ReasoningState) -> str:
        """阶段2决策：检查详细度充足性后的路由"""
        
        overall_score = state["overall_sufficiency"]
        threshold = state["sufficiency_threshold"]
        
        if overall_score >= threshold:
            print(f"✅ Sufficiency检查通过 ({overall_score:.1f} >= {threshold})")
            return "sufficiency_passed"
        else:
            print(f"❌ 需要更多详细信息 ({overall_score:.1f} < {threshold})")
            return "need_more_details"

    def _decide_after_fitness_check(self, state: ReasoningState) -> str:
        """阶段3决策：检查适宜性后的路由"""
        
        if state["fitness_concerns"]:
            concern_count = len(state["fitness_concerns"])
            print(f"⚠️ 发现{concern_count}个适宜性问题，需要协商")
            return "fitness_concerns"
        else:
            print("✅ 适宜性检查通过，准备完成")
            return "fitness_passed"
    
    # ==================== 节点实现占位符 ====================
    # 这些方法在Step 2中实现
    
    async def _check_info_completed(self, state: ReasoningState) -> ReasoningState:
        """检查基础信息完整性"""
        print("🔍 检查基础信息完整性...")
        
        # 使用复用的Stage1ReasoningGraph实例，保持状态一致性
        self.stage1_graph.collected_info = state["collected_info"]
        
        # 检查是否完成
        is_complete = self.stage1_graph.check_stage_completion()
        state["stage1_complete"] = is_complete
        
        if is_complete:
            print("✅ 基础信息收集完成")
        else:
            print("❌ 基础信息不完整")
            
        return state
    
    async def _generate_lack_response(self, state: ReasoningState) -> ReasoningState:
        """生成信息不足的回复"""
        print("📝 生成信息不足回复...")
        
        # 使用复用的Stage1ReasoningGraph实例，保持状态一致性
        self.stage1_graph.collected_info = state["collected_info"]
        
        # 获取缺失信息详情
        lacked_info = self.stage1_graph.get_lacked_info()
        
        # 生成回复
        response = await self.stage1_graph.generate_response_with_lacked_info(lacked_info)
        
        # 更新状态
        state["messages"].append({
            "role": "assistant", 
            "content": response,
            "stage": lacked_info["stage"],
            "lacked_info": lacked_info
        })
        
        return state
    
    async def _assess_sufficiency(self, state: ReasoningState) -> ReasoningState:
        """评估信息详细度充足性"""
        print("🔍 评估信息详细度...")
        
        collected_info = state["collected_info"]
        conversation_context = self._build_conversation_context(state["messages"])
        
        # 使用LLM评估各个维度的详细度
        sufficiency_assessment = await self._llm_assess_sufficiency(collected_info, conversation_context)
        
        # 更新状态
        state["sufficiency_score"] = sufficiency_assessment["dimension_scores"]
        state["overall_sufficiency"] = sufficiency_assessment["overall_score"]
        state["sufficiency_passed"] = sufficiency_assessment["overall_score"] >= state["sufficiency_threshold"]
        
        print(f"📊 详细度评估完成:")
        for dimension, score in sufficiency_assessment["dimension_scores"].items():
            print(f"  {dimension}: {score:.1f}/100")
        print(f"  总体评分: {sufficiency_assessment['overall_score']:.1f}/100 (阈值: {state['sufficiency_threshold']})")
        
        return state
    
    async def _generate_sufficiency_questions(self, state: ReasoningState) -> ReasoningState:
        """生成详细度补充问题"""
        print("❓ 生成详细度补充问题...")
        
        # 获取评估结果
        sufficiency_scores = state["sufficiency_score"]
        overall_score = state["overall_sufficiency"]
        
        # 生成针对性的补充问题
        questions_response = await self._llm_generate_sufficiency_questions(
            collected_info=state["collected_info"],
            sufficiency_scores=sufficiency_scores,
            overall_score=overall_score,
            conversation_context=self._build_conversation_context(state["messages"])
        )
        
        # 更新状态
        state["messages"].append({
            "role": "assistant",
            "content": questions_response,
            "type": "sufficiency_questions",
            "sufficiency_scores": sufficiency_scores
        })
        
        return state
    
    async def _check_fitness(self, state: ReasoningState) -> ReasoningState:
        """检查内容适宜性"""
        print("🛡️ 检查内容适宜性...")
        
        # 获取收集的信息
        collected_info = state["collected_info"]
        conversation_context = self._build_conversation_context(state["messages"])
        
        # 使用LLM进行适宜性检查
        fitness_result = await self._llm_check_fitness(collected_info, conversation_context)
        
        # 更新状态
        state["fitness_assessment"] = fitness_result
        state["fitness_concerns"] = fitness_result.get("concerns", [])
        state["fitness_passed"] = len(fitness_result.get("concerns", [])) == 0
        
        if state["fitness_passed"]:
            print("✅ 适宜性检查通过")
        else:
            concern_count = len(state["fitness_concerns"])
            print(f"⚠️ 发现{concern_count}个适宜性问题需要处理")
        
        return state
    
    async def _generate_negotiate_response(self, state: ReasoningState) -> ReasoningState:
        """生成适宜性协商回复"""
        print("🤝 生成适宜性协商回复...")
        
        # 获取适宜性检查结果
        fitness_assessment = state["fitness_assessment"]
        fitness_concerns = state["fitness_concerns"]
        
        # 生成协商回复
        negotiate_response = await self._llm_generate_negotiate_response(
            collected_info=state["collected_info"],
            fitness_assessment=fitness_assessment,
            concerns=fitness_concerns,
            conversation_context=self._build_conversation_context(state["messages"])
        )
        
        # 更新状态
        state["messages"].append({
            "role": "assistant",
            "content": negotiate_response,
            "type": "fitness_negotiation",
            "fitness_concerns": fitness_concerns
        })
        
        return state
    
    async def _generate_finish_response(self, state: ReasoningState) -> ReasoningState:
        """生成完成回复"""
        print("🎉 生成完成回复...")
        
        # 准备最终需求文档
        final_requirements = self._prepare_final_requirements(state["collected_info"])
        
        # 生成完成回复
        finish_response = await self._llm_generate_finish_response(
            collected_info=state["collected_info"],
            sufficiency_scores=state["sufficiency_score"],
            final_requirements=final_requirements,
            conversation_context=self._build_conversation_context(state["messages"])
        )
        
        # 更新最终状态
        state["ready_for_generation"] = True
        state["final_requirements"] = final_requirements
        state["messages"].append({
            "role": "assistant",
            "content": finish_response,
            "type": "completion_confirmation",
            "final_requirements": final_requirements
        })
        
        return state
    
    # ==================== 工具方法 ====================
    
    def initialize_reasoning_state(self, session_id: str, user_id: str, 
                                 collected_info: Dict[str, Any]) -> ReasoningState:
        """初始化推理状态"""
        
        return ReasoningState(
            session_id=session_id,
            messages=[],
            user_id=user_id,
            
            # 需求收集状态
            collected_info=collected_info,
            stage1_complete=False,
            
            # 详细度评估状态  
            sufficiency_score={},
            overall_sufficiency=0.0,
            sufficiency_threshold=75.0,  # 可配置
            sufficiency_passed=False,
            
            # 适宜性检查状态
            fitness_assessment={},
            fitness_concerns=[],
            fitness_passed=False,
            
            # 最终状态
            ready_for_generation=False,
            final_requirements={}
        )
    
    async def process_reasoning_request(self, session_id: str, user_id: str, 
                                      collected_info: Dict[str, Any]) -> Dict[str, Any]:
        """处理推理请求的主入口"""
        
        # 初始化状态
        initial_state = self.initialize_reasoning_state(session_id, user_id, collected_info)
        
        # 运行图
        thread_config = {"configurable": {"thread_id": session_id}}
        
        try:
            final_state = await self.graph.ainvoke(initial_state, config=thread_config)
            
            return {
                "success": True,
                "final_state": final_state,
                "ready_for_generation": final_state.get("ready_for_generation", False),
                "messages": final_state.get("messages", []),
                "stage": self._determine_current_stage(final_state)
            }
            
        except Exception as e:
            print(f"❌ StateGraph执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "ready_for_generation": False
            }
    
    def _determine_current_stage(self, final_state: ReasoningState) -> str:
        """根据最终状态确定当前所处阶段"""
        
        if final_state.get("ready_for_generation"):
            return "ready_for_generation"
        elif not final_state.get("stage1_complete"):
            return "stage1_incomplete"
        elif not final_state.get("sufficiency_passed"):
            return "need_more_details"
        elif final_state.get("fitness_concerns"):
            return "fitness_negotiation"
        else:
            return "processing"
    
    # ==================== LLM评估相关方法 ====================
    
    def _build_conversation_context(self, messages: List[Dict[str, str]]) -> str:
        """构建对话上下文"""
        if not messages:
            return "暂无对话记录"
            
        context_parts = []
        total_length = 0
        max_context_length = 10000  # 设置较大的长度限制
        
        # 按时间顺序处理所有消息
        for msg in messages:
            role = "用户" if msg["role"] == "user" else "助手"
            msg_text = f"{role}: {msg['content']}"
            
            # 如果超出长度限制就停止，但不做特殊处理
            if total_length + len(msg_text) > max_context_length:
                break
                
            context_parts.append(msg_text)
            total_length += len(msg_text)
        
        return "\n".join(context_parts)
    
    async def _llm_assess_sufficiency(self, collected_info: Dict[str, Any], 
                                    conversation_context: str) -> Dict[str, Any]:
        """使用LLM评估信息详细度充足性"""
        
        assessment_prompt = f"""你是专业的教育游戏设计评估专家。请评估以下收集到的信息是否足够详细，能够用来生成高质量的教育游戏内容。

已收集信息：
{self._format_collected_info_for_assessment(collected_info)}

对话上下文：
{conversation_context}

请从以下4个维度评估信息的详细度充足性，每个维度给出0-100分的评分和具体理由：

1. **基础信息充足性** (学科、年级、知识点的明确性和具体性)
2. **教学信息充足性** (教学目标和难点的清晰度和可操作性) 
3. **游戏设定充足性** (游戏风格、角色、世界观的完整性和吸引力)
4. **情节设定充足性** (故事情节、互动方式的丰富性和教育性)

请以JSON格式返回评估结果：
{{
    "dimension_scores": {{
        "基础信息": <分数>,
        "教学信息": <分数>,
        "游戏设定": <分数>,
        "情节设定": <分数>
    }},
    "dimension_analysis": {{
        "基础信息": "<详细分析>",
        "教学信息": "<详细分析>",
        "游戏设定": "<详细分析>",
        "情节设定": "<详细分析>"
    }},
    "overall_score": <总体加权平均分>,
    "insufficient_areas": ["<需要补充的方面1>", "<需要补充的方面2>"],
    "assessment_summary": "<整体评估总结>"
}}

评分标准：
- 90-100分：信息非常详细完整，可以直接生成高质量内容
- 75-89分：信息基本充足，可能需要少量补充
- 60-74分：信息有一定基础，但需要重要补充
- 60分以下：信息不足，需要大量补充

请确保返回有效的JSON格式。"""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": assessment_prompt}])
            import json
            assessment_result = json.loads(response.content)
            
            return assessment_result
            
        except Exception as e:
            print(f"❌ LLM评估失败: {e}")
            # 返回默认评估结果
            return {
                "dimension_scores": {
                    "基础信息": 60.0,
                    "教学信息": 60.0,
                    "游戏设定": 60.0,
                    "情节设定": 60.0
                },
                "dimension_analysis": {
                    "基础信息": "评估异常，使用默认分数",
                    "教学信息": "评估异常，使用默认分数",
                    "游戏设定": "评估异常，使用默认分数",
                    "情节设定": "评估异常，使用默认分数"
                },
                "overall_score": 60.0,
                "insufficient_areas": ["信息评估异常"],
                "assessment_summary": "由于技术问题，无法准确评估，建议人工检查"
            }
    
    def _format_collected_info_for_assessment(self, collected_info: Dict[str, Any]) -> str:
        """格式化收集的信息用于评估"""
        formatted_parts = []
        
        # 基础信息
        if any([collected_info.get("subject"), collected_info.get("grade"), collected_info.get("knowledge_points")]):
            formatted_parts.append("【基础信息】")
            if collected_info.get("subject"):
                formatted_parts.append(f"  学科: {collected_info['subject']}")
            if collected_info.get("grade"):
                formatted_parts.append(f"  年级: {collected_info['grade']}")
            if collected_info.get("knowledge_points"):
                kp = collected_info['knowledge_points']
                kp_str = "、".join(kp) if isinstance(kp, list) else str(kp)
                formatted_parts.append(f"  知识点: {kp_str}")
        
        # 教学信息
        if any([collected_info.get("teaching_goals"), collected_info.get("teaching_difficulties")]):
            formatted_parts.append("\n【教学信息】")
            if collected_info.get("teaching_goals"):
                tg = collected_info['teaching_goals']
                tg_str = "、".join(tg) if isinstance(tg, list) else str(tg)
                formatted_parts.append(f"  教学目标: {tg_str}")
            if collected_info.get("teaching_difficulties"):
                td = collected_info['teaching_difficulties']
                td_str = "、".join(td) if isinstance(td, list) else str(td)
                formatted_parts.append(f"  教学难点: {td_str}")
        
        # 游戏设定
        if any([collected_info.get("game_style"), collected_info.get("character_design"), collected_info.get("world_setting")]):
            formatted_parts.append("\n【游戏设定】")
            if collected_info.get("game_style"):
                formatted_parts.append(f"  游戏风格: {collected_info['game_style']}")
            if collected_info.get("character_design"):
                formatted_parts.append(f"  角色设计: {collected_info['character_design']}")
            if collected_info.get("world_setting"):
                formatted_parts.append(f"  世界背景: {collected_info['world_setting']}")
        
        # 情节设定
        if any([collected_info.get("plot_requirements"), collected_info.get("interaction_requirements")]):
            formatted_parts.append("\n【情节设定】")
            if collected_info.get("plot_requirements"):
                pr = collected_info['plot_requirements']
                pr_str = "、".join(pr) if isinstance(pr, list) else str(pr)
                formatted_parts.append(f"  情节需求: {pr_str}")
            if collected_info.get("interaction_requirements"):
                ir = collected_info['interaction_requirements']
                ir_str = "、".join(ir) if isinstance(ir, list) else str(ir)
                formatted_parts.append(f"  互动需求: {ir_str}")
        
        return "\n".join(formatted_parts) if formatted_parts else "暂无收集信息"
    
    async def _llm_generate_sufficiency_questions(self, collected_info: Dict[str, Any], 
                                                 sufficiency_scores: Dict[str, float],
                                                 overall_score: float,
                                                 conversation_context: str) -> str:
        """使用LLM生成针对性的补充问题"""
        
        questions_prompt = f"""你是专业的教育游戏设计助手。根据以下信息评估结果，生成针对性的补充问题来完善游戏设计信息。

当前收集信息：
{self._format_collected_info_for_assessment(collected_info)}

详细度评估结果：
{self._format_scores_for_prompt(sufficiency_scores)}
总体评分：{overall_score:.1f}/100

对话上下文：
{conversation_context}

请根据评估结果生成3-5个具体的补充问题，重点关注评分较低的维度。要求：

1. **问题应该具体明确**，避免模糊的开放性问题
2. **优先关注评分低于75分的维度**
3. **结合对话上下文**，避免重复已经讨论过的内容
4. **循序渐进**，一次不要问太多问题
5. **友好自然**，保持对话的连贯性

回复格式：
首先简要说明当前完成度和需要补充的方面，然后提出具体问题。

示例回复风格：
"根据目前的信息，基础设定已经比较完整了！不过为了设计出更优质的教育游戏，我还需要了解一些细节：

1. [具体问题1]
2. [具体问题2] 
3. [具体问题3]

这些信息将帮助我为您生成更精准、更有趣的游戏内容。"

请生成回复："""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": questions_prompt}])
            return response.content
        except Exception as e:
            print(f"❌ LLM生成问题失败: {e}")
            return self._generate_fallback_questions(sufficiency_scores)
    
    def _format_scores_for_prompt(self, sufficiency_scores: Dict[str, float]) -> str:
        """格式化评分结果用于prompt"""
        score_parts = []
        for dimension, score in sufficiency_scores.items():
            status = "✅ 充足" if score >= 75 else "⚠️ 需补充" if score >= 60 else "❌ 不足"
            score_parts.append(f"  {dimension}: {score:.1f}/100 {status}")
        return "\n".join(score_parts)
    
    def _generate_fallback_questions(self, sufficiency_scores: Dict[str, float]) -> str:
        """生成备用问题（当LLM失败时使用）"""
        low_score_dimensions = [dim for dim, score in sufficiency_scores.items() if score < 75]
        
        fallback_questions = {
            "基础信息": "请您再详细说明一下具体的知识点和学习目标？",
            "教学信息": "您希望学生通过游戏重点解决哪些学习困难？",
            "游戏设定": "请描述一下您理想中的游戏角色和世界观？",
            "情节设定": "您希望游戏的故事情节如何展开？有什么特别的互动想法吗？"
        }
        
        response_parts = ["根据目前的信息，我还需要了解一些细节：\n"]
        for i, dim in enumerate(low_score_dimensions[:3], 1):  # 最多3个问题
            if dim in fallback_questions:
                response_parts.append(f"{i}. {fallback_questions[dim]}")
        
        response_parts.append("\n这些信息将帮助我为您设计更完善的教育游戏。")
        return "\n".join(response_parts)
    
    async def _llm_check_fitness(self, collected_info: Dict[str, Any], 
                                conversation_context: str) -> Dict[str, Any]:
        """使用LLM检查内容适宜性"""
        
        fitness_prompt = f"""你是专业的教育内容审查专家。请检查以下教育游戏设计需求的适宜性，确保内容适合目标年龄段的学生。

收集的信息：
{self._format_collected_info_for_assessment(collected_info)}

对话上下文：
{conversation_context}

请从以下维度检查适宜性：

1. **年龄适宜性** - 内容是否适合目标年级的学生
2. **教育价值观** - 是否传递正确的教育价值观
3. **内容安全性** - 是否包含不当内容（暴力、恐怖、歧视等）
4. **心理健康** - 是否会对学生心理造成负面影响
5. **文化敏感性** - 是否尊重不同文化背景
6. **学习难度** - 游戏难度是否与年级水平匹配

请以JSON格式返回检查结果：
{{
    "overall_fitness": <"passed" 或 "concerns">,
    "concerns": [
        {{
            "category": "<问题类别>",
            "severity": "<high/medium/low>",
            "description": "<具体问题描述>",
            "suggestion": "<改进建议>"
        }}
    ],
    "positive_aspects": ["<积极方面1>", "<积极方面2>"],
    "fitness_score": <0-100的适宜性评分>,
    "assessment_summary": "<整体适宜性总结>"
}}

检查标准：
- high severity: 严重违反教育原则或安全标准
- medium severity: 需要调整但不影响整体适宜性  
- low severity: 建议性改进

请确保返回有效的JSON格式。"""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": fitness_prompt}])
            import json
            fitness_result = json.loads(response.content)
            
            return fitness_result
            
        except Exception as e:
            print(f"❌ LLM适宜性检查失败: {e}")
            # 返回保守的默认结果
            return {
                "overall_fitness": "concerns",
                "concerns": [{
                    "category": "技术问题",
                    "severity": "low",
                    "description": "无法自动完成适宜性检查，建议人工审核",
                    "suggestion": "请人工检查内容适宜性"
                }],
                "positive_aspects": ["内容收集完整"],
                "fitness_score": 70,
                "assessment_summary": "由于技术问题，无法完成自动适宜性检查，建议人工审核"
            }
    
    async def _llm_generate_negotiate_response(self, collected_info: Dict[str, Any],
                                             fitness_assessment: Dict[str, Any],
                                             concerns: List[Dict[str, str]],
                                             conversation_context: str) -> str:
        """使用LLM生成适宜性协商回复"""
        
        concerns_text = "\n".join([
            f"• {concern['category']} ({concern['severity']}): {concern['description']} - {concern['suggestion']}"
            for concern in concerns
        ])
        
        negotiate_prompt = f"""你是专业的教育游戏设计助手。在内容适宜性检查中发现了一些需要讨论的问题，请以友好、专业的方式与用户协商解决方案。

当前收集信息：
{self._format_collected_info_for_assessment(collected_info)}

适宜性检查结果：
总体评估：{fitness_assessment.get('overall_fitness', 'unknown')}
适宜性评分：{fitness_assessment.get('fitness_score', 0)}/100

发现的问题：
{concerns_text}

积极方面：
{', '.join(fitness_assessment.get('positive_aspects', []))}

对话上下文：
{conversation_context}

请生成一个友好、建设性的回复，要求：

1. **肯定积极方面** - 先赞扬用户提供的良好想法
2. **温和提出问题** - 以建议的方式提出需要调整的地方
3. **提供解决方案** - 给出具体的改进建议
4. **保持合作态度** - 强调是为了创造更好的教育体验
5. **邀请讨论** - 询问用户的想法和偏好

回复应该类似这样的风格：
"您的游戏创意很棒！特别是[积极方面]。为了确保游戏更适合目标年龄段的学生，我建议我们在几个方面稍作调整：

[具体建议和原因]

您觉得这样的调整如何？或者您有其他想法吗？"

请生成回复："""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": negotiate_prompt}])
            return response.content
        except Exception as e:
            print(f"❌ LLM生成协商回复失败: {e}")
            return self._generate_fallback_negotiate_response(concerns)
    
    async def _llm_generate_finish_response(self, collected_info: Dict[str, Any],
                                          sufficiency_scores: Dict[str, float],
                                          final_requirements: Dict[str, Any],
                                          conversation_context: str) -> str:
        """使用LLM生成完成确认回复"""
        
        finish_prompt = f"""你是专业的教育游戏设计助手。经过详细的信息收集和评估，现在准备为用户生成完整的教育游戏内容。请生成一个专业、令人兴奋的完成确认回复。

最终收集信息：
{self._format_collected_info_for_assessment(collected_info)}

详细度评估结果：
{self._format_scores_for_prompt(sufficiency_scores)}
平均评分：{sum(sufficiency_scores.values()) / len(sufficiency_scores):.1f}/100

对话历程：
{conversation_context}

请生成一个专业而令人兴奋的完成回复，包含：

1. **庆祝完成** - 祝贺用户完成详细的需求收集过程
2. **总结收集成果** - 简要总结收集到的关键信息
3. **确认理解** - 确认对用户需求的理解是否准确
4. **预告生成内容** - 说明将要生成什么样的游戏内容
5. **下一步指引** - 告知用户如何进行下一步

回复应该专业且充满期待，类似：
"🎉 太棒了！经过我们的详细交流，教育游戏的需求收集已经完成！

让我总结一下我们收集到的信息：
[关键信息总结]

基于这些信息，我将为您生成：
• 完整的游戏故事框架和剧情设计
• 每个关卡的详细场景和任务设置  
• 角色对话和互动内容
• 教育目标的巧妙融入方式

请确认以上理解是否准确？如果没有问题，我就开始为您生成完整的教育游戏内容！"

请生成回复："""

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": finish_prompt}])
            return response.content
        except Exception as e:
            print(f"❌ LLM生成完成回复失败: {e}")
            return self._generate_fallback_finish_response(collected_info)
    
    def _generate_fallback_negotiate_response(self, concerns: List[Dict[str, str]]) -> str:
        """生成备用协商回复"""
        high_concerns = [c for c in concerns if c.get('severity') == 'high']
        
        if high_concerns:
            return f"感谢您提供的创意想法！为了确保游戏内容适合目标年龄段的学生，我建议我们在以下方面做一些调整：\n\n" + \
                   "\n".join([f"• {c['description']}" for c in high_concerns[:2]]) + \
                   "\n\n您觉得这样的调整如何？我们一起来优化这个游戏设计吧！"
        else:
            return "您的游戏创意很不错！让我们进一步完善一些细节，确保游戏更适合目标学生群体。您有什么想法吗？"
    
    def _generate_fallback_finish_response(self, collected_info: Dict[str, Any]) -> str:
        """生成备用完成回复"""
        return f"""🎉 太好了！教育游戏需求收集已经完成！

根据我们的交流，我了解到您想要为{collected_info.get('grade', '目标年级')}的学生设计一个{collected_info.get('subject', '特定学科')}教育游戏。

我将为您生成完整的游戏内容，包括故事情节、角色设计、关卡设置等所有元素。

请确认信息无误，我就开始生成您的专属教育游戏！"""
    
    def _prepare_final_requirements(self, collected_info: Dict[str, Any]) -> Dict[str, Any]:
        """准备最终需求文档"""
        return {
            "basic_info": {
                "subject": collected_info.get("subject"),
                "grade": collected_info.get("grade"),
                "knowledge_points": collected_info.get("knowledge_points", [])
            },
            "teaching_info": {
                "teaching_goals": collected_info.get("teaching_goals", []),
                "teaching_difficulties": collected_info.get("teaching_difficulties", [])
            },
            "gamestyle_info": {
                "game_style": collected_info.get("game_style"),
                "character_design": collected_info.get("character_design"),
                "world_setting": collected_info.get("world_setting")
            },
            "plot_info": {
                "plot_requirements": collected_info.get("plot_requirements", []),
                "interaction_requirements": collected_info.get("interaction_requirements", [])
            },
            "metadata": {
                "completion_timestamp": self._get_current_timestamp(),
                "total_collected_fields": sum(1 for v in collected_info.values() if v)
            }
        }
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 创建实例的便利函数
def create_reasoning_graph():
    """创建ReasoningGraph实例"""
    return ReasoningGraph(db_client)