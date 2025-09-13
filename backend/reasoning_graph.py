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


# ==================== StateGraph版本的ReasoningGraph ====================

class ReasoningState(TypedDict):
    """ReasoningGraph的状态定义 - 包含Stage1合并的字段"""
    # 基础会话状态
    session_id: str
    messages: List[Dict[str, str]]
    user_id: str
    
    # 需求收集状态
    collected_info: Dict[str, Any]
    stage1_complete: bool
    
    # === 从Stage1保留的状态字段 ===
    extracted_info: Dict[str, Any]  # 当前轮提取的信息
    current_stage: str              # 当前所在阶段
    
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
    """基于StateGraph的智能推理图 - 合并了Stage1功能"""
    
    def __init__(self, db_client=None):
        self.db_client = db_client or db_client
        
        # 初始化LLM
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.7,  # 对话生成使用较高温度
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # 初始化信息提取器
        from info_extractor import create_info_extractor
        self.extractor = create_info_extractor("gpt-4o-mini")
        
        # ===== 从Stage1ReasoningGraph合并的状态管理 =====
        
        # 初始化Memory (从Stage1合并)
        self.memory = ConversationSummaryBufferMemory(
            max_token_limit=8000,
            llm=self.llm,
            return_messages=True
        )
        
        # 收集的信息存储 (从Stage1合并)
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
        
        # 完成条件定义 (从Stage1合并)
        self.completion_criteria = {
            "basic_info": ["subject", "grade", "knowledge_points"],
            "teaching_info": ["teaching_goals", "teaching_difficulties"],
            "gamestyle_info": ["game_style", "character_design", "world_setting"],
            "scene_info": ["plot_requirements", "interaction_requirements"]
        }
        
        # 导入prompt模板 (从Stage1合并)
        from prompt_templates import PromptTemplates
        self.prompts = PromptTemplates()
        
        self.graph = self._build_reasoning_graph()
    
    # ===== 从Stage1ReasoningGraph合并的方法 =====
    
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
                        existing = self.collected_info[key] if isinstance(self.collected_info[key], list) else [self.collected_info[key]]
                        combined = existing + value
                        self.collected_info[key] = list(set(combined))
                    else:
                        self.collected_info[key] = value
                else:
                    # 处理字符串类型的数据
                    self.collected_info[key] = value
        
        print(f"DEBUG update_state: final collected_info = {self.collected_info}")

    def check_stage_completion(self) -> bool:
        """检查是否达成Stage1目标"""
        return self.determine_current_stage() == "complete"
    
    def get_lacked_info(self) -> Dict:
        """获取缺失信息详情"""
        current_stage = self.determine_current_stage()

        if current_stage == "complete":
            return {"stage": "complete", "missing_fields": [], "missing_details": {}, "completion_rate": 1.0}
        
        print(f"current stage is {current_stage}")
        # 根据当前阶段获取缺失信息
        if current_stage == "basic_info":
            return self._check_basic_info_gaps()
        elif current_stage == "teaching_info":
            return self._check_teaching_info_gaps()
        elif current_stage == "gamestyle_info":
            return self._check_gamestyle_info_gaps()
        elif current_stage == "scene_info":
            return self._check_scene_info_gaps()
        else:
            return {"stage": current_stage, "missing_fields": [], "missing_details": {}, "completion_rate": 0.0}

    def _check_basic_info_gaps(self) -> Dict:
        """检查基础信息缺失"""
        missing_fields = []
        missing_details = {}
        
        if not self.collected_info.get("subject"):
            missing_fields.append("subject")
            missing_details["subject"] = "学科领域"
        if not self.collected_info.get("grade"):
            missing_fields.append("grade")
            missing_details["grade"] = "目标年级"
        if not self.collected_info.get("knowledge_points"):
            missing_fields.append("knowledge_points")
            missing_details["knowledge_points"] = "具体知识点"
        
        completion_rate = 1.0 - len(missing_fields) / 3
        return {
            "stage": "basic_info",
            "missing_fields": missing_fields,
            "missing_details": missing_details,
            "completion_rate": completion_rate
        }

    def _check_teaching_info_gaps(self) -> Dict:
        """检查教学信息缺失"""
        missing_fields = []
        missing_details = {}
        
        if not self.collected_info.get("teaching_goals"):
            missing_fields.append("teaching_goals")
            missing_details["teaching_goals"] = "教学目标"
        if not self.collected_info.get("teaching_difficulties"):
            missing_fields.append("teaching_difficulties")
            missing_details["teaching_difficulties"] = "教学难点"
        
        completion_rate = 1.0 - len(missing_fields) / 2
        return {
            "stage": "teaching_info",
            "missing_fields": missing_fields,
            "missing_details": missing_details,
            "completion_rate": completion_rate
        }

    def _check_gamestyle_info_gaps(self) -> Dict:
        """检查游戏风格信息缺失"""
        missing_fields = []
        missing_details = {}
        
        if not self.collected_info.get("game_style"):
            missing_fields.append("game_style")
            missing_details["game_style"] = "游戏风格"
        if not self.collected_info.get("character_design"):
            missing_fields.append("character_design")
            missing_details["character_design"] = "角色设计"
        if not self.collected_info.get("world_setting"):
            missing_fields.append("world_setting")
            missing_details["world_setting"] = "世界背景"
        
        completion_rate = 1.0 - len(missing_fields) / 3
        return {
            "stage": "gamestyle_info",
            "missing_fields": missing_fields,
            "missing_details": missing_details,
            "completion_rate": completion_rate
        }

    def _check_scene_info_gaps(self) -> Dict:
        """检查情节信息缺失"""
        missing_fields = []
        missing_details = {}
        
        if not self.collected_info.get("plot_requirements"):
            missing_fields.append("plot_requirements")
            missing_details["plot_requirements"] = "情节需求"
        if not self.collected_info.get("interaction_requirements"):
            missing_fields.append("interaction_requirements")
            missing_details["interaction_requirements"] = "互动方式"
        
        completion_rate = 1.0 - len(missing_fields) / 2
        return {
            "stage": "scene_info",
            "missing_fields": missing_fields,
            "missing_details": missing_details,
            "completion_rate": completion_rate
        }
    
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
        
        # 生成回复（空输入，让模板处理）
        response = await conversation.apredict(input="")
        return response.strip()
    
    def save_final_requirements(self) -> Dict:
        """保存最终收集的需求信息到数据库"""
        try:
            # 检查数据库连接
            if not self.db_client:
                return {
                    "success": False,
                    "message": "数据库未连接，无法保存",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 生成唯一ID
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.md5(json.dumps(self.collected_info, sort_keys=True).encode()).hexdigest()[:8]
            requirement_id = f"requirement_{timestamp}_{content_hash}"
            
            # 准备保存的数据
            requirement_data = {
                "id": requirement_id,
                "user_id": "default_user",  # 简化为default
                "timestamp": timestamp,
                "collected_info": self.collected_info,
                "final_requirements": self.collected_info,  # 为了兼容性
                "status": "completed"
            }
            
            # 保存到数据库
            save_success = self.db_client.save_requirement(requirement_data)
            
            if save_success:
                return {
                    "success": True,
                    "requirement_id": requirement_id,
                    "message": "需求信息已成功保存",
                    "timestamp": timestamp
                }
            else:
                return {
                    "success": False,
                    "message": "保存失败",
                    "timestamp": timestamp
                }
                
        except Exception as e:
            print(f"⚠️ 保存需求信息失败: {e}")
            return {
                "success": False,
                "message": f"保存失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_reasoning_graph(self) -> StateGraph:
        """构建推理状态图"""
        
        workflow = StateGraph(ReasoningState)
        
        # ==================== 节点定义 ====================
        
        # 新流程：Stage1集成的节点
        workflow.add_node("check_info_completed", self._check_info_completed)
        workflow.add_node("extract_and_update_info", self._extract_and_update_info)
        workflow.add_node("determine_stage", self._determine_stage)
        workflow.add_node("generate_lack_response", self._generate_lack_response)
        
        # 保留：后续详细度和适宜性检查节点
        workflow.add_node("need_more_details", self._assess_sufficiency)
        workflow.add_node("generate_need_more_details_response", self._generate_sufficiency_questions)
        workflow.add_node("check_fitness", self._check_fitness)
        workflow.add_node("generate_negotiate_response", self._generate_negotiate_response)
        workflow.add_node("generate_finish_response", self._generate_finish_response)
        
        # ==================== 流程路由 ====================
        
        # 设置入口点
        workflow.set_entry_point("check_info_completed")
        
        # 新流程：总是流转到信息提取
        workflow.add_edge("check_info_completed", "extract_and_update_info")
        
        # 信息提取后流转到阶段判断
        workflow.add_edge("extract_and_update_info", "determine_stage")
        
        # 阶段判断后的条件路由
        workflow.add_conditional_edges(
            "determine_stage",
            self._decide_stage_routing,
            {
                "info_incomplete": "generate_lack_response",
                "info_complete": "need_more_details"  # 继续原有流程
            }
        )
        
        # 信息不足时结束（等待用户补充）
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
    
    def _decide_after_sufficiency_check(self, state: ReasoningState) -> str:
        """sufficiency检查后的路由决策"""
        if state.get("sufficiency_passed", False):
            print("✅ 详细度检查通过，进入适宜性检查")
            return "sufficiency_passed"
        else:
            print("❌ 详细度不足，需要更多信息")
            return "need_more_details"
    
    def _decide_after_fitness_check(self, state: ReasoningState) -> str:
        """fitness检查后的路由决策"""
        fitness_concerns = state.get("fitness_concerns", [])
        
        if fitness_concerns:
            print(f"⚠️ 发现适宜性问题: {len(fitness_concerns)}个")
            return "fitness_concerns"
        else:
            print("✅ 适宜性检查通过，准备完成")
            return "fitness_passed"
    
    # ==================== 新增节点函数 ====================
    
    async def _extract_and_update_info(self, state: ReasoningState) -> ReasoningState:
        """提取并更新用户输入的信息"""
        try:
            # 获取最新的用户消息
            messages = state.get("messages", [])
            if not messages:
                return state
                
            latest_message = messages[-1]
            if latest_message.get("role") != "user":
                return state
                
            user_input = latest_message.get("content", "")
            current_stage = state.get("current_stage", "basic_info")
            
            # 提取信息
            extracted_info = await self.extract_info(user_input, current_stage)
            print(f"DEBUG: 提取到的信息: {extracted_info}")
            
            # 更新状态
            self.update_state(extracted_info)
            
            # 更新state中的信息
            state["extracted_info"] = extracted_info
            state["collected_info"] = self.collected_info.copy()
            
            return state
            
        except Exception as e:
            print(f"❌ 信息提取失败: {e}")
            return state
    
    async def _determine_stage(self, state: ReasoningState) -> ReasoningState:
        """确定当前阶段和完成状态"""
        try:
            # 确定当前阶段
            current_stage = self.determine_current_stage()
            stage1_complete = self.check_stage_completion()
            
            print(f"DEBUG: 当前阶段: {current_stage}, Stage1完成: {stage1_complete}")
            
            # 更新状态
            state["current_stage"] = current_stage
            state["stage1_complete"] = stage1_complete
            
            # 如果完成，设置ready_for_generation和保存需求
            if stage1_complete:
                save_result = self.save_final_requirements()
                if save_result["success"]:
                    state["ready_for_generation"] = True
                    state["final_requirements"] = self.collected_info.copy()
                    print(f"✅ 需求信息已保存: {save_result['requirement_id']}")
            
            return state
            
        except Exception as e:
            print(f"❌ 阶段判断失败: {e}")
            return state
    
    def _decide_stage_routing(self, state: ReasoningState) -> str:
        """决定阶段路由：完成或未完成"""
        stage1_complete = state.get("stage1_complete", False)
        
        if stage1_complete:
            return "info_complete"
        else:
            return "info_incomplete"
    
    # ==================== 节点实现 ====================
    
    async def _check_info_completed(self, state: ReasoningState) -> ReasoningState:
        """检查基础信息完整性 - 简化版，主要用于初始化"""
        print("🔍 检查基础信息完整性...")
        
        # 同步状态
        self.collected_info = state["collected_info"]
        
        # 这个节点现在主要是一个占位符，实际检查在determine_stage中进行
        print(f"当前collected_info: {self.collected_info}")
            
        return state
    
    async def _generate_lack_response(self, state: ReasoningState) -> ReasoningState:
        """生成信息不足的回复 - 使用合并的Stage1逻辑"""
        print("📝 生成信息不足回复...")
        print(f"current collected_info is {self.collected_info}")
        
        # 同步状态
        self.collected_info = state["collected_info"]
        
        # 获取缺失信息详情
        lacked_info = self.get_lacked_info()
        
        # 生成回复
        response = await self.generate_response_with_lacked_info(lacked_info)
        
        # 更新状态
        state["messages"].append({
            "role": "assistant", 
            "content": response,
            "stage": lacked_info["stage"],
            "lacked_info": lacked_info,
            "timestamp": datetime.now().isoformat()
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
            fitness_concerns=fitness_concerns,
            collected_info=state["collected_info"],
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
        """生成最终完成回复"""
        print("🎉 生成最终完成回复...")
        
        # 生成最终确认回复
        final_response = await self._llm_generate_final_response(
            collected_info=state["collected_info"],
            conversation_context=self._build_conversation_context(state["messages"])
        )
        
        # 标记为ready_for_generation
        state["ready_for_generation"] = True
        state["final_requirements"] = state["collected_info"].copy()
        
        # 更新状态
        state["messages"].append({
            "role": "assistant",
            "content": final_response,
            "type": "completion_confirmation"
        })
        
        return state
    
    # ==================== LLM辅助方法 ====================
    
    def _build_conversation_context(self, messages: List[Dict[str, str]]) -> str:
        """构建对话上下文"""
        if not messages:
            return "暂无对话记录"
            
        context_parts = []
        # 取最近10轮对话
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")  # 移除长度限制
            context_parts.append(f"{role}: {content}")
            
        return "\n".join(context_parts)
    
    async def _llm_assess_sufficiency(self, collected_info: Dict[str, Any], 
                                    conversation_context: str) -> Dict[str, Any]:
        """使用LLM评估信息详细度充足性"""
        
        # 使用PromptTemplate
        prompt_template = self.prompts.get_sufficiency_assessment_prompt()
        assessment_prompt = prompt_template.format(
            collected_info=self._format_collected_info_for_assessment(collected_info),
            conversation_context=conversation_context
        )

        try:
            response = await self.llm.apredict(assessment_prompt)
            # 提取markdown代码块中的JSON内容
            json_content = self._extract_json_from_markdown(response.strip())
            result = json.loads(json_content)
            return result
        except Exception as e:
            print(f"❌ LLM评估失败: {e}")
            # 返回默认的低分评估
            return {
                "dimension_scores": {
                    "基础信息充足性": 60,
                    "教学信息充足性": 60,
                    "游戏设定充足性": 60,
                    "情节设定充足性": 60
                },
                "overall_score": 60,
                "detailed_feedback": {
                    "strengths": [],
                    "weaknesses": ["评估过程中出现错误"],
                    "suggestions": ["请重新评估信息详细度"]
                }
            }
    
    async def _llm_generate_sufficiency_questions(self, collected_info: Dict[str, Any], 
                                                sufficiency_scores: Dict[str, float], 
                                                overall_score: float,
                                                conversation_context: str) -> str:
        """使用LLM生成详细度补充问题"""
        
        # 找到得分最低的维度
        lowest_dimension = min(sufficiency_scores.keys(), key=lambda k: sufficiency_scores[k])
        lowest_score = sufficiency_scores[lowest_dimension]
        
        # 使用PromptTemplate
        prompt_template = self.prompts.get_sufficiency_questions_prompt()
        questions_prompt = prompt_template.format(
            collected_info=self._format_collected_info_for_assessment(collected_info),
            overall_score=overall_score,
            lowest_dimension=lowest_dimension,
            lowest_score=lowest_score,
            conversation_context=conversation_context
        )

        try:
            return await self.llm.apredict(questions_prompt)
        except Exception as e:
            print(f"❌ 生成补充问题失败: {e}")
            return f"为了更好地设计游戏，请提供更多关于{lowest_dimension}的详细信息。比如您希望游戏具体如何帮助学生学习？"
    
    async def _llm_check_fitness(self, collected_info: Dict[str, Any], 
                               conversation_context: str) -> Dict[str, Any]:
        """使用LLM检查内容适宜性"""
        
        # 使用PromptTemplate
        prompt_template = self.prompts.get_fitness_check_prompt()
        fitness_prompt = prompt_template.format(
            collected_info=self._format_collected_info_for_assessment(collected_info),
            conversation_context=conversation_context
        )

        try:
            response = await self.llm.apredict(fitness_prompt)
            json_content = self._extract_json_from_markdown(response.strip())
            return json.loads(json_content)
        except Exception as e:
            print(f"❌ 适宜性检查失败: {e}")
            # 返回默认通过的结果
            return {
                "overall_fitness": "适宜",
                "concerns": [],
                "positive_aspects": ["内容积极健康"]
            }
    
    async def _llm_generate_negotiate_response(self, fitness_concerns: List[Dict], 
                                             collected_info: Dict[str, Any],
                                             conversation_context: str) -> str:
        """使用LLM生成适宜性协商回复"""

        concerns_text = "\n".join([
            f"- {concern.get('category', concern.get('type', '未知类别'))}: {concern.get('description', '未知描述')} (严重程度: {concern.get('severity', '未知')})"
            for concern in fitness_concerns
        ])
        
        # 使用PromptTemplate
        prompt_template = self.prompts.get_negotiate_response_prompt()
        negotiate_prompt = prompt_template.format(
            concerns_text=concerns_text,
            collected_info=self._format_collected_info_for_assessment(collected_info),
            conversation_context=conversation_context
        )

        try:
            return await self.llm.apredict(negotiate_prompt)
        except Exception as e:
            print(f"❌ 生成协商回复失败: {e}")
            return "发现一些需要调整的地方，请修改设计以确保内容更适合目标学生群体。"
    
    async def _llm_generate_final_response(self, collected_info: Dict[str, Any],
                                         conversation_context: str) -> str:
        """使用LLM生成最终确认回复"""
        
        # 使用PromptTemplate
        prompt_template = self.prompts.get_finish_response_prompt()
        final_prompt = prompt_template.format(
            collected_info=self._format_collected_info_for_assessment(collected_info),
            conversation_context=conversation_context
        )

        try:
            return await self.llm.apredict(final_prompt)
        except Exception as e:
            print(f"❌ 生成最终回复失败: {e}")
            return "🎉 信息收集完成！您的教育游戏设计非常棒，我们现在开始生成具体的游戏内容。"
    
    def _extract_json_from_markdown(self, content: str) -> str:
        """从markdown代码块中提取JSON内容"""
        content = content.strip()
        
        # 检查是否包含markdown代码块
        if content.startswith("```json") and content.endswith("```"):
            # 提取代码块中的内容
            lines = content.split('\n')
            # 移除第一行的```json和最后一行的```
            json_lines = lines[1:-1]
            return '\n'.join(json_lines)
        elif content.startswith("```") and content.endswith("```"):
            # 处理其他类型的代码块
            lines = content.split('\n')
            json_lines = lines[1:-1]
            return '\n'.join(json_lines)
        else:
            # 如果没有代码块包装，直接返回原内容
            return content

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
                points = collected_info['knowledge_points']
                if isinstance(points, list):
                    points = "、".join(points)
                formatted_parts.append(f"  知识点: {points}")

        # 教学信息
        if any([collected_info.get("teaching_goals"), collected_info.get("teaching_difficulties")]):
            formatted_parts.append("\n【教学信息】")
            if collected_info.get("teaching_goals"):
                goals = collected_info['teaching_goals']
                if isinstance(goals, list):
                    goals = "、".join(goals)
                formatted_parts.append(f"  教学目标: {goals}")
            if collected_info.get("teaching_difficulties"):
                difficulties = collected_info['teaching_difficulties']
                if isinstance(difficulties, list):
                    difficulties = "、".join(difficulties)
                formatted_parts.append(f"  教学难点: {difficulties}")

        # 游戏设定
        if any([collected_info.get("game_style"), collected_info.get("character_design"),
                collected_info.get("world_setting")]):
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
                plots = collected_info['plot_requirements']
                if isinstance(plots, list):
                    plots = "、".join(plots)
                formatted_parts.append(f"  情节需求: {plots}")
            if collected_info.get("interaction_requirements"):
                interactions = collected_info['interaction_requirements']
                if isinstance(interactions, list):
                    interactions = "、".join(interactions)
                formatted_parts.append(f"  互动方式: {interactions}")

        return "\n".join(formatted_parts) if formatted_parts else "暂无详细信息"
    # ==================== 公共接口方法 ====================
    
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
            
            # === Stage1状态字段 ===
            extracted_info={},
            current_stage="basic_info",
            
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
    
    async def process_reasoning_request_with_state(self, reasoning_state: Dict[str, Any], 
                                                  user_input: str) -> Dict[str, Any]:
        """使用已有状态处理推理请求 - 支持状态持久化"""
        
        try:
            # 添加用户输入到消息历史
            if "messages" not in reasoning_state:
                reasoning_state["messages"] = []
            
            # 添加用户消息
            reasoning_state["messages"].append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            
            # 同步更新collected_info状态
            print(f"DEBUG: 同步更新状态，collected_info: {reasoning_state.get('collected_info', {})}")
            self.collected_info = reasoning_state.get("collected_info", {})
            
            # 清空之前的memory并重新同步对话历史（避免重复）
            self.memory.chat_memory.clear()
            
            # 重新添加所有历史消息到memory
            messages = reasoning_state.get("messages", [])
            for msg in messages:
                if msg.get("role") == "user":
                    self.memory.chat_memory.add_user_message(msg["content"])
                elif msg.get("role") == "assistant":
                    self.memory.chat_memory.add_ai_message(msg["content"])
            
            # 运行图
            thread_config = {"configurable": {"thread_id": reasoning_state.get("session_id", "default")}}
            
            final_state = await self.graph.ainvoke(reasoning_state, config=thread_config)
            
            return {
                "success": True,
                "final_state": final_state,
                "ready_for_generation": final_state.get("ready_for_generation", False),
                "messages": final_state.get("messages", []),
                "stage": self._determine_current_stage(final_state)
            }
            
        except Exception as e:
            print(f"❌ StateGraph持久化执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "ready_for_generation": False
            }
    
    def _determine_current_stage(self, final_state: ReasoningState) -> str:
        """根据最终状态确定当前所处阶段"""
        
        if final_state.get("ready_for_generation"):
            return "ready_for_generation"
        elif not final_state.get("stage1_complete", False):
            return "stage1_collecting"
        elif not final_state.get("sufficiency_passed", False):
            return "need_more_details"
        elif not final_state.get("fitness_passed", False):
            return "fitness_check"
        else:
            return "unknown"


# 便利函数
def create_reasoning_graph() -> ReasoningGraph:
    """创建ReasoningGraph实例的便利函数"""
    return ReasoningGraph()