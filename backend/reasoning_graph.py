from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory  
from langchain_openai import ChatOpenAI
from typing import Dict
import json
import hashlib
from datetime import datetime
from upstash_redis import Redis


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
            "scene_requirements": None,
            "interaction_requirements": None
        }

        # 完成条件定义
        self.completion_criteria = {
            "basic_info": ["subject", "grade", "knowledge_points"],
            "teaching_info": ["teaching_goals", "teaching_difficulties"],
            "gamestyle_info": ["game_style", "character_design", "world_setting"],
            "scene_info": ["scene_requirements", "interaction_requirements"]
        }

        # 导入prompt模板
        from prompt_templates import PromptTemplates
        self.prompts = PromptTemplates()
        
        # 初始化Redis连接
        try:
            self.redis = Redis(
                url=os.getenv("UPSTASH_REDIS_URL"),
                token=os.getenv("UPSTASH_REDIS_TOKEN")
            )
            print("✅ Redis连接成功")
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            self.redis = None

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

        scene_requirements = self.collected_info.get("scene_requirements")
        if not scene_requirements or (isinstance(scene_requirements, list) and len(scene_requirements) == 0):
            missing.append("scene_requirements")
            details["scene_requirements"] = "需要描述希望的场景类型（如：森林冒险、城堡解谜、太空探索等）"

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
        print(f"dynmiac prompt is : {dynamic_prompt}")
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
                "scene_requirements": self.collected_info["scene_requirements"],
                "interaction_requirements": self.collected_info["interaction_requirements"]
            },
            "metadata": {
                "completion_date": self._get_current_timestamp(),
                "total_fields_collected": sum(1 for v in self.collected_info.values() if v)
            }
        }

    def _format_final_requirements(self) -> str:
        """格式化最终需求为易读文本并保存到Redis"""
        
        # 保存到Redis
        self._save_requirements_to_redis()
        
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

        # 场景需求
        sections.append("\n🏞️ 场景需求：")
        if self.collected_info['scene_requirements']:
            scenes = "、".join(self.collected_info['scene_requirements'])
            sections.append(f"  场景类型：{scenes}")
        if self.collected_info['interaction_requirements']:
            interactions = "、".join(self.collected_info['interaction_requirements'])
            sections.append(f"  互动方式：{interactions}")

        return "\n".join(sections)
    
    def _save_requirements_to_redis(self):
        """将最终需求保存到Upstash Redis"""
        if not self.redis:
            print("⚠️ Redis未连接，跳过保存")
            return
            
        try:
            # 生成唯一ID
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.md5(json.dumps(self.collected_info, sort_keys=True).encode()).hexdigest()[:8]
            requirement_id = f"requirement_{timestamp}_{content_hash}"
            
            # 准备保存的数据
            requirement_data = {
                "id": requirement_id,
                "user_id": "1",  # 添加用户ID
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
            
            # 保存到Redis
            key = f"eduagent:requirements:{requirement_id}"
            self.redis.set(key, json.dumps(requirement_data, ensure_ascii=False))
            self.redis.expire(key, 2592000)  # 30天过期
            
            # 添加到索引（按日期）
            date_key = f"eduagent:requirements:index:{datetime.now().strftime('%Y-%m-%d')}"
            self.redis.sadd(date_key, requirement_id)
            self.redis.expire(date_key, 2592000)  # 30天过期
            
            print(f"✅ 需求数据已保存到Redis: {requirement_id}")
            
        except Exception as e:
            print(f"❌ 保存到Redis失败: {e}")

    def save_final_requirements(self) -> Dict:
        """保存最终收集的需求信息到Redis"""
        try:
            # 检查Redis连接
            if not self.redis:
                return {
                    "success": False,
                    "message": "Redis未连接，无法保存",
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
            
            # 保存到Redis
            key = f"eduagent:requirements:{requirement_id}"
            self.redis.set(key, json.dumps(requirement_data, ensure_ascii=False))
            self.redis.expire(key, 2592000)  # 30天过期
            
            # 添加到索引（按日期）
            date_key = f"eduagent:requirements:index:{datetime.now().strftime('%Y-%m-%d')}"
            self.redis.sadd(date_key, requirement_id)
            self.redis.expire(date_key, 2592000)  # 30天过期
            
            return {
                "success": True,
                "message": f"需求信息保存成功: {requirement_id}",
                "requirement_id": requirement_id,
                "saved_fields": list(k for k, v in self.collected_info.items() if v),
                "total_fields": len([v for v in self.collected_info.values() if v]),
                "timestamp": timestamp
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