from langchain.prompts import PromptTemplate
from typing import Dict, Any


class PromptTemplates:
    def __init__(self):
        """初始化所有Stage1的提示词模板"""
        self._init_base_templates()
        self._init_dynamic_templates()

    def _init_base_templates(self):
        """初始化基础提示词模板"""

        # 基础信息收集模板
        self.basic_info_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""你是专业的教育游戏设计助手。现在需要收集基础信息来设计RPG教育游戏。

对话历史：
{history}

当前任务：收集基础信息
需要了解的信息：
- 目标年级（如：一年级、二年级、三年级等）
- 学科领域（如：数学、语文、英语、科学等）
- 具体知识点（如：10以内加法、汉语拼音、英语字母等）

用户输入：{input}

请友好地引导用户提供这些基础信息。如果用户已经提到了部分信息，请确认并询问缺失的部分。保持对话自然流畅，一次不要问太多问题。

助手回复："""
        )

        # 教学信息收集模板
        self.teaching_info_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""你是专业的教育游戏设计助手。基础信息已经收集完成，现在需要深入了解教学需求。

对话历史：
{history}

当前任务：了解教学目标和难点
需要了解的信息：
- 具体的教学目标（学生通过游戏要达到什么学习效果？）
- 教学难点（学生在这个知识点上通常有什么困难？）
- 期望的学习成果

用户输入：{input}

请深入了解用户的教学需求，重点关注学生的学习困难和期望达成的教学目标。

助手回复："""
        )

        # 游戏风格收集模板
        self.gamestyle_info_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""你是专业的教育游戏设计助手。现在需要确定游戏的风格和设定。

对话历史：
{history}

当前任务：设计游戏风格和角色设定
需要了解的信息：
- 游戏风格偏好（如：魔法冒险、科幻探索、童话故事、历史穿越等）
- 角色设计想法（如：可爱的小动物、勇敢的小勇士、智慧的导师等）
- 世界观背景（如：魔法森林、未来世界、童话王国等）

用户输入：{input}

请帮助用户确定游戏的视觉风格和角色设定，让游戏更有吸引力。

助手回复："""
        )

        # 情节需求收集模板
        self.scene_info_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""你是专业的教育游戏设计助手。最后需要确定具体的情节和互动需求。

对话历史：
{history}

当前任务：设计情节发展和互动方式
需要了解的详细信息：
【情节需求】
- 故事主线：主角的目标和动机（如：拯救被困的朋友、寻找失落的宝藏、完成学习任务）
- 情节结构：故事发展方式（如：线性闯关、分支选择、开放探索）
- 冲突设置：学习挑战的呈现形式（如：解谜障碍、知识竞赛、合作任务）
- 角色关系：主角与NPC的互动类型（如：师生关系、伙伴协作、竞争对手）
- 情感基调：希望营造的氛围（如：轻松愉快、紧张刺激、温馨感人）

【互动方式】
- 操作方式偏好（如：选择题答题、拖拽操作、语音互动等）
- 评估和奖励机制想法

用户输入：{input}

请详细了解用户对游戏情节发展和互动方式的具体想法，确保游戏既有完整的故事性又有教育意义。

助手回复："""
        )

        # 完成确认模板
        self.completion_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""你是专业的教育游戏设计助手。信息收集即将完成！

对话历史：
{history}

当前状态：信息收集基本完成
任务：确认信息并准备生成游戏内容

用户输入：{input}

请总结收集到的所有信息，向用户确认是否准确，然后准备进入游戏内容生成阶段。

助手回复："""
        )

        # 默认模板
        self.default_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""你是专业的教育游戏设计助手。

对话历史：
{history}

用户输入：{input}

请根据对话上下文，友好地回应用户并继续收集教育游戏设计所需的信息。

助手回复："""
        )

    def _init_dynamic_templates(self):
        """初始化动态模板的基础结构"""

        # 动态模板的基础框架
        self.dynamic_template_base = """你是专业的教育游戏设计助手。

            当前收集阶段：{stage_name}
            已收集信息：
            {collected_info}
            
            还需要了解：
            {missing_info}
            
            对话历史：
            {history}
            
            用户输入：{input}
            
            {stage_guidance}
            
            请根据缺失的信息重点询问，保持对话自然友好。
            
            助手回复："""

    def get_prompt_by_stage(self, stage: str) -> PromptTemplate:
        """根据阶段名称获取对应的prompt模板"""
        stage_mapping = {
            "basic_info": self.basic_info_prompt,
            "teaching_info": self.teaching_info_prompt,
            "gamestyle_info": self.gamestyle_info_prompt,
            "scene_info": self.scene_info_prompt,
            "complete": self.completion_prompt
        }

        return stage_mapping.get(stage, self.default_prompt)

    def generate_dynamic_prompt(self, stage: str, collected_info: Dict[str, Any],
                                lacked_info: Dict[str, Any]) -> PromptTemplate:
        """基于收集状态动态生成prompt"""

        # 格式化已收集信息
        collected_summary = self._format_collected_info(collected_info, stage)

        # 格式化缺失信息
        missing_summary = self._format_missing_info(lacked_info)
        print(f"missing summary is {missing_summary}")
        # 生成阶段指导语
        stage_guidance = self._generate_stage_guidance(stage, lacked_info)

        # 阶段名称映射
        stage_names = {
            "basic_info": "基础信息收集",
            "teaching_info": "教学需求了解",
            "gamestyle_info": "游戏风格设定",
            "scene_info": "场景互动设计"
        }

        return PromptTemplate(
            input_variables=["history", "input"],
            template=self.dynamic_template_base,
            partial_variables={
                "stage_name": stage_names.get(stage, stage),
                "collected_info": collected_summary,
                "missing_info": missing_summary,
                "stage_guidance": stage_guidance
            }
        )

    def _format_collected_info(self, collected_info: Dict[str, Any], stage: str) -> str:
        """格式化已收集的信息"""
        if not any(collected_info.values()):
            return "暂无信息"

        formatted_sections = []

        # 基础信息部分
        basic_items = []
        if collected_info.get("subject"):
            basic_items.append(f"- 学科：{collected_info['subject']}")
        if collected_info.get("grade"):
            basic_items.append(f"- 年级：{collected_info['grade']}")
        if collected_info.get("knowledge_points"):
            points = "、".join(collected_info['knowledge_points'])
            basic_items.append(f"- 知识点：{points}")

        if basic_items:
            formatted_sections.append("【基础信息】\n" + "\n".join(basic_items))

        # 教学信息部分
        teaching_items = []
        if collected_info.get("teaching_goals"):
            goals = "、".join(collected_info['teaching_goals'])
            teaching_items.append(f"- 教学目标：{goals}")
        if collected_info.get("teaching_difficulties"):
            difficulties = "、".join(collected_info['teaching_difficulties'])
            teaching_items.append(f"- 教学难点：{difficulties}")

        if teaching_items:
            formatted_sections.append("【教学需求】\n" + "\n".join(teaching_items))

        # 游戏设定部分
        gamestyle_items = []
        if collected_info.get("game_style"):
            gamestyle_items.append(f"- 游戏风格：{collected_info['game_style']}")
        if collected_info.get("character_design"):
            gamestyle_items.append(f"- 角色设计：{collected_info['character_design']}")
        if collected_info.get("world_setting"):
            gamestyle_items.append(f"- 世界背景：{collected_info['world_setting']}")

        if gamestyle_items:
            formatted_sections.append("【游戏设定】\n" + "\n".join(gamestyle_items))

        # 情节需求部分
        scene_items = []
        if collected_info.get("plot_requirements"):
            plots = "、".join(collected_info['plot_requirements'])
            scene_items.append(f"- 情节需求：{plots}")
        if collected_info.get("interaction_requirements"):
            interactions = "、".join(collected_info['interaction_requirements'])
            scene_items.append(f"- 互动方式：{interactions}")

        if scene_items:
            formatted_sections.append("【情节设计】\n" + "\n".join(scene_items))

        return "\n\n".join(formatted_sections) if formatted_sections else "暂无信息"

    def _format_missing_info(self, lacked_info: Dict[str, Any]) -> str:
        """格式化缺失信息"""
        missing_details = lacked_info.get("missing_details", {})
        if not missing_details:
            return "信息收集完成"

        missing_items = []
        for field, description in missing_details.items():
            missing_items.append(f"- {description}")

        return "\n".join(missing_items)

    def _generate_stage_guidance(self, stage: str, lacked_info: Dict[str, Any]) -> str:
        """生成针对性的阶段指导语"""
        completion_rate = lacked_info.get("completion_rate", 0)
        missing_count = len(lacked_info.get("missing_fields", []))

        # 基础鼓励语
        if completion_rate == 0:
            base_encouragement = "让我们开始收集信息吧！"
        elif completion_rate < 0.5:
            base_encouragement = f"很好！还需要了解{missing_count}个方面的信息。"
        elif completion_rate < 1.0:
            base_encouragement = f"非常棒！我们快完成了，还需要{missing_count}个信息。"
        else:
            base_encouragement = "信息收集完成，让我们进入下一阶段。"

        # 根据具体缺失字段生成精确指导
        missing_fields = lacked_info.get("missing_fields", [])
        
        field_guidance = {
            # basic_info字段
            "subject": "请明确学科领域",
            "grade": "请确认目标年级", 
            "knowledge_points": "请详细说明要学习的知识点",
            
            # teaching_info字段
            "teaching_goals": "请说明希望学生通过游戏达到的学习目标",
            "teaching_difficulties": "请告诉我学生在这个知识点上的常见困难",
            
            # gamestyle_info字段  
            "game_style": "请描述您偏好的游戏风格",
            "character_design": "请说明希望的角色设计",
            "world_setting": "请描述游戏的世界背景设定",
            
            # scene_info字段  
            "plot_requirements": "请详细描述希望的情节发展，包括故事主线、情节结构、冲突设置、角色关系和情感基调",
            "interaction_requirements": "请说明偏好的互动方式和评估机制"
        }
        
        if missing_fields:
            specific_guidances = [field_guidance.get(field, f"请提供{field}信息") for field in missing_fields]
            specific_guidance = "重点关注：" + "、".join(specific_guidances) + "。"
        else:
            specific_guidance = ""

        return f"{base_encouragement} {specific_guidance}".strip()

    def get_sufficiency_assessment_prompt(self) -> PromptTemplate:
        """获取信息详细度评估模板"""
        template = """你是专业的教育游戏设计评估专家。请评估以下收集到的信息是否足够详细，能够用来生成高质量的教育游戏内容。

已收集信息：
{collected_info}

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
        "基础信息充足性": [0-100分，基于实际评估],
        "教学信息充足性": [0-100分，基于实际评估],
        "游戏设定充足性": [0-100分，基于实际评估],
        "情节设定充足性": [0-100分，基于实际评估]
    }},
    "dimension_analysis": {{
        "基础信息充足性": "[具体分析基础信息的充足程度]",
        "教学信息充足性": "[具体分析教学信息的充足程度]",
        "游戏设定充足性": "[具体分析游戏设定的充足程度]",
        "情节设定充足性": "[具体分析情节设定的充足程度]"
    }},
    "overall_score": [4个维度分数的平均值],
    "insufficient_areas": ["情节发展细节", "互动机制设计"],
    "assessment_summary": "基础信息完整，需要补充情节和互动细节"
}}

评分标准：
- 90-100分：信息非常详细完整，可以直接生成高质量内容
- 75-89分：信息基本充足，可能需要少量补充
- 60-74分：信息有一定基础，但需要重要补充
- 60分以下：信息不足，需要大量补充

请确保返回有效的JSON格式。"""
        
        return PromptTemplate(
            input_variables=["collected_info", "conversation_context"],
            template=template
        )
    
    def get_sufficiency_questions_prompt(self) -> PromptTemplate:
        """获取详细度补充问题生成模板"""
        template = """你是专业的教育游戏设计助手。根据以下信息评估结果，生成针对性的补充问题来完善游戏设计信息。

当前收集信息：
{collected_info}

详细度评估结果：
{sufficiency_scores}
总体评分：{overall_score}/100

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
        
        return PromptTemplate(
            input_variables=["collected_info", "sufficiency_scores", "overall_score", "conversation_context"],
            template=template
        )

    def get_input_fitness_check_prompt(self) -> PromptTemplate:
        """获取用户输入适宜性检查模板"""
        template = """你是专业的教育内容审查专家。请检查用户输入的教育游戏设计需求是否合理和适宜。

用户输入：
{user_input}

当前收集的信息：
{collected_info}

请从以下维度检查用户输入的适宜性：

1. **逻辑合理性** - 学科和知识点是否匹配（如：语文课教四则运算、负一年级、高三学前班内容等不合理组合）
2. **难度合理性** - 知识点难度是否与年级水平匹配（如：一年级学微积分、幼儿园学高等数学等超纲内容）
3. **价值观正确性** - 教学目标是否积极正面（拒绝偷窃、暴力、欺骗等不良内容）
4. **年龄适宜性** - 内容是否适合目标年龄段（拒绝少儿不宜、恐怖、血腥内容）
5. **教育合规性** - 是否符合教育法规和道德标准
6. **引导性检查** - 是否有恶意引导或不当暗示

请以JSON格式返回检查结果：
{{
    "input_fitness": "[passed或rejected，基于评估结果]",
    "fitness_score": [0-100分，基于实际评估],
    "issues": [
        {{
            "category": "[问题类别]",
            "severity": "[high/medium/low]",
            "description": "[具体问题描述]",
            "suggestion": "[改进建议]"
        }}
    ],
    "assessment_summary": "[输入内容的整体评估结论]"
}}

检查标准：
- input_fitness: "passed"(通过) 或 "rejected"(拒绝)
- high severity: 严重违反常识或道德标准，必须拒绝
- medium severity: 需要用户澄清或修改
- low severity: 建议性提醒

请严格按照JSON格式返回结果。"""

        return PromptTemplate(
            input_variables=["user_input", "collected_info"],
            template=template
        )

    def get_fitness_check_prompt(self) -> PromptTemplate:
        """获取内容适宜性检查模板"""
        template = """你是专业的教育内容审查专家。请检查以下教育游戏设计需求的适宜性，确保内容适合目标年龄段的学生。

    收集的信息：
    {collected_info}

    对话上下文：
    {conversation_context}

    请从以下维度检查适宜性：

    1. **年龄适宜性** - 内容是否适合目标年级的学生
    2. **教育价值观** - 是否传递正确的教育价值观
    3. **内容安全性** - 是否包含不当内容（暴力、恐怖、歧视等）
    4. **心理健康** - 是否会对学生心理造成负面影响
    5. **文化敏感性** - 是否尊重不同文化背景
    6. **学习难度** - 游戏难度是否与年级水平匹配

    请以JSON格式返回检查结果，请确保所有值都是具体内容：
    {{
        "overall_fitness": "[passed或concerns，基于评估结果]",
        "concerns": [
            {{
                "category": "[问题类别]",
                "severity": "[high/medium/low]",
                "description": "[具体问题描述]",
                "suggestion": "[具体改进建议]"
            }}
        ],
        "positive_aspects": ["[积极方面1]", "[积极方面2]"],
        "fitness_score": [0-100分，基于实际评估],
        "assessment_summary": "[整体适宜性总结]"
    }}

    检查标准：
    - high severity: 严重违反教育原则或安全标准
    - medium severity: 需要调整但不影响整体适宜性  
    - low severity: 建议性改进

    请严格按照上述JSON格式返回，确保：
    1. overall_fitness 值为 "passed" 或 "concerns" 
    2. fitness_score 为0-100的数字
    3. 所有字符串值都填写具体内容，不使用占位符。"""

        return PromptTemplate(
            input_variables=["collected_info", "conversation_context"],
            template=template
        )
    
    def get_negotiate_response_prompt(self) -> PromptTemplate:
        """获取适宜性协商回复模板"""
        template = """你是专业的教育游戏设计助手。在内容适宜性检查中发现了一些需要讨论的问题，请以友好、专业的方式与用户协商解决方案。

当前收集信息：
{collected_info}

适宜性检查结果：
总体评估：{overall_fitness}
适宜性评分：{fitness_score}/100

发现的问题：
{concerns}

积极方面：
{positive_aspects}

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
        
        return PromptTemplate(
            input_variables=["collected_info", "overall_fitness", "fitness_score", "concerns", "positive_aspects", "conversation_context"],
            template=template
        )
    
    def get_finish_response_prompt(self) -> PromptTemplate:
        """获取完成确认回复模板"""
        template = """你是专业的教育游戏设计助手。经过详细的信息收集和评估，现在准备为用户生成完整的教育游戏内容。请生成一个专业、令人兴奋的完成确认回复。

最终收集信息：
{collected_info}

详细度评估结果：
{sufficiency_scores}
平均评分：{average_score}/100

对话历程：
{conversation_context}

请生成一个专业而令人兴奋的完成回复，包含：

1. **庆祝完成** - 祝贺用户完成详细的需求收集过程
2. **总结收集成果** - 简要总结收集到的关键信息
3. **确认理解** - 确认对用户需求的理解是否准确
4. **预告生成内容** - 说明将要生成什么样的游戏内容
5. **下一步指引** - 告知用户如何进行下一步

回复应该专业且充满期待，类似：
"太棒了！经过我们的详细交流，教育游戏的需求收集已经完成！

让我总结一下我们收集到的信息：
[关键信息总结]

基于这些信息，我将为您生成：
- 完整的游戏故事框架和剧情设计
- 每个关卡的详细场景和任务设置
- 角色对话和互动内容
- 教育目标的巧妙融入方式

请确认以上理解是否准确？如果没有问题，我就开始为您生成完整的教育游戏内容！"

请生成回复："""
        
        return PromptTemplate(
            input_variables=["collected_info", "sufficiency_scores", "average_score", "conversation_context"],
            template=template
        )
    
    def get_requirement_analysis_prompt(self) -> PromptTemplate:
        """获取RPG教育游戏需求分析报告模板"""
        template = """你是专业的RPG教育游戏设计分析师。请基于收集的需求信息生成一份面向RPG故事框架设计的需求分析报告。

收集的需求信息：
{collected_info}

质量评估结果：
{sufficiency_scores}
平均评分：{average_score}/100

请生成专业的RPG教育游戏需求分析报告，重点提取以下RPG设计核心元素：

**【项目基础信息】**
- 目标学科、年级、知识点
- 教学目标和学习难点

**【RPG世界观设计要素】**
- 游戏世界背景和设定
- 主要角色和NPC设计
- 世界观与教育内容的结合点

**【RPG故事结构要素】**
- 主线剧情框架
- 教育内容如何融入故事线
- 关键故事节点和教学检查点

**【RPG游戏机制要素】**
- 核心互动机制
- 进度系统和奖励机制
- 教育评估的游戏化实现

**【教育-RPG融合分析】**
- 教学目标与RPG元素的匹配度
- 知识点在故事中的分布策略
- 学习难点的游戏化解决方案

**【第二阶段设计指导】**
- RPG故事框架的关键设计点
- 内容拓展的重点方向
- 技术实现的核心需求

要求：
- 重点突出RPG设计要素
- 为故事框架生成提供具体指导
- 确保所有基础信息完整包含
- 格式清晰，便于第二阶段系统使用

请以结构化文本报告格式输出。"""

        return PromptTemplate(
            input_variables=["collected_info", "sufficiency_scores", "average_score"],
            template=template
        )
    
    def get_story_framework_generation_prompt(self) -> PromptTemplate:
        """获取RPG故事框架生成模板"""
        template = """你是专业的RPG教育游戏故事设计师。请基于需求信息生成一个完整的6关卡RPG故事框架。

需求信息：
{collected_info}

质量评估：
{sufficiency_scores}
平均评分：{average_score}/100

请生成一个完整的RPG教育游戏故事框架，必须包含以下内容：

## 【故事主线设计】
请设计一个引人入胜的主线故事，包含：
- **主角背景**：主角的身份、动机、特殊能力
- **世界观设定**：游戏世界的背景、规则、特色
- **核心冲突**：主要矛盾和挑战（与教学目标相关）
- **故事目标**：主角的终极目标和成长轨迹
- **主线剧情**：完整的故事发展脉络（起承转合）

## 【6关卡详细设计】
为每个关卡设计详细内容：

**关卡1：[关卡名称]**
- 场景设定：
  * 环境概述：详细描述关卡的环境氛围和视觉特色
  * 核心场景：关卡中的关键场景和主要物品/角色
  * 氛围定调：营造的情感氛围和探索感受
- 剧情描述：具体的故事情节和场景
- 教学融入：如何自然融入知识点"{knowledge_points}"
- 考核设计：主要考核点和评估方式
- 互动方式：游戏化的学习互动
- 主线衔接：与总体故事的关系

**关卡2-6：[依此类推]**
每个关卡都需要包含相同的场景设定格式，包括环境概述、核心场景、氛围定调等要素。

### 场景描述示例参考：
关卡示例：[神秘森林]
- 场景设定：
  * 环境概述：古老茂密的魔法森林，阳光透过树叶洒下斑驳光影
  * 核心场景：被数字符号装饰的神秘笼子困住小兔子  
  * 氛围定调：温馨而神秘，充满探索感

请为每个关卡创建类似风格但内容不同的场景设定，确保：
1. 环境描述生动形象，符合年级学生的想象力
2. 核心场景与教学内容自然结合
3. 氛围营造有利于学习投入和情感代入

## 【连贯性保证】
- **情节衔接**：各关卡间的逻辑过渡
- **角色发展**：主角在各关卡的成长变化
- **知识递进**：知识点的循序渐进安排
- **奖励系统**：贯穿始终的激励机制

## 【教育游戏化设计】
- **学中玩**：如何让学习过程充满趣味
- **情景代入**：让学生沉浸在故事世界中
- **成就感**：通过游戏机制增强学习成就感

要求：
1. 故事必须符合"{grade}"学生的认知水平和兴趣
2. 知识点融入要自然，避免生硬的"做题"感觉
3. 每个关卡都要有明确的教学目标和考核点
4. 故事情节要连贯流畅，吸引学生持续参与
5. 符合"{game_style}"风格和"{world_setting}"设定
6. 主角可以是"{character_design}"类型

请以结构化格式输出完整的故事框架设计。"""

        return PromptTemplate(
            input_variables=["collected_info", "sufficiency_scores", "average_score", "knowledge_points", "grade", "game_style", "world_setting", "character_design", "analysis_report"],
            template=template
        )

    def get_story_review_prompt(self) -> PromptTemplate:
        """获取故事框架审核评分模板"""
        template = """你是专业的教育游戏质量评估专家。请对以下RPG故事框架进行全面评估打分。

原始需求：
{collected_info}

生成的故事框架：
{story_framework}

请从以下6个维度进行评分（每项0-100分）：

## 【评分维度】

**1. 主线明确性评分 (0-100分)**
评估标准：
- 故事目标是否清晰明确
- 主角动机是否合理充分
- 核心冲突设置是否有吸引力
- 教学目标与故事融合度
- 整体故事弧线是否完整

**2. 内容一致性评分 (0-100分)**
评估标准：
- 与用户需求的匹配程度
- 学科、年级、知识点的准确对应
- 游戏风格、角色、世界观的一致性
- 教学难点的合理体现
- 互动需求的准确实现

**3. 剧情连贯性评分 (0-100分)**
评估标准：
- 6个关卡间的逻辑衔接
- 故事情节发展的流畅性
- 角色成长轨迹的合理性
- 情节过渡的自然性
- 整体叙事的完整性

**4. 教育融合度评分 (0-100分)**
评估标准：
- 知识点融入的自然程度
- 考核方式的创新性和合理性
- 互动设计与教学目标的匹配
- 避免生硬"做题"的程度
- 教学难点的有效解决方案

**5. 吸引力评估评分 (0-100分)**
评估标准：
- 故事的趣味性和吸引力
- 游戏化设计的丰富程度
- 沉浸感体验的营造
- "玩中学"理念的体现
- 对目标年龄段的适宜性

**6. 场景剧本贴合度评分 (0-100分)**
评估标准：
- 场景设定的完整性和生动性（环境概述、核心场景、氛围定调）
- 场景与剧情的自然融合度
- 环境描述与教学内容的匹配程度
- 视觉场景的想象力激发效果
- 场景氛围与学习目标的协调性
- 各关卡场景间的风格一致性和变化合理性

## 【评分要求】
- 每个维度给出具体分数和详细理由
- 指出具体的优点和不足
- 提供针对性的改进建议
- 总分为6个维度的平均分

## 【通过标准】
- 各单项维度≥75分
- 总分≥80分（6个维度的平均分）
- 如未达标，需重新生成

请以JSON格式返回评分结果：
{{
    "主线明确性": {{
        "分数": [根据实际评估给出0-100的分数],
        "评价": "[详细分析该维度的表现]",
        "改进建议": "[针对性的改进建议]"
    }},
    "内容一致性": {{
        "分数": [根据实际评估给出0-100的分数],
        "评价": "[详细分析该维度的表现]",
        "改进建议": "[针对性的改进建议]"
    }},
    "剧情连贯性": {{
        "分数": [根据实际评估给出0-100的分数],
        "评价": "[详细分析该维度的表现]", 
        "改进建议": "[针对性的改进建议]"
    }},
    "教育融合度": {{
        "分数": [根据实际评估给出0-100的分数],
        "评价": "[详细分析该维度的表现]",
        "改进建议": "[针对性的改进建议]"
    }},
    "吸引力评估": {{
        "分数": [根据实际评估给出0-100的分数],
        "评价": "[详细分析该维度的表现]",
        "改进建议": "[针对性的改进建议]"
    }},
    "场景剧本贴合度": {{
        "分数": [根据实际评估给出0-100的分数],
        "评价": "[详细分析场景设定的完整性、场景与剧情融合度、环境描述效果等]",
        "改进建议": "[针对场景描述、氛围营造、视觉效果的具体改进建议]"
    }},
    "总分": [6个维度分数的平均值],
    "整体评价": "[综合评价故事框架的整体质量]",
    "是否通过": [true/false，基于通过标准判断],
    "重点改进方向": ["[具体改进点1]", "[具体改进点2]"]
}}

重要提醒：请根据故事框架的实际质量进行客观评分，不要使用示例中的数字！"""

        return PromptTemplate(
            input_variables=["collected_info", "story_framework"],
            template=template
        )

    def get_story_improvement_prompt(self) -> PromptTemplate:
        """获取故事改进指导模板"""
        template = """基于专家评审反馈，请改进RPG故事框架设计。

原始需求：
{collected_info}

当前故事框架：
{current_framework}

评审反馈：
{review_feedback}

重点改进方向：
{improvement_focus}

请根据评审意见，重新设计故事框架，重点改进以下方面：
{specific_improvements}

改进要求：
1. 保持已有的优点和高分部分
2. 针对性解决评分低的问题
3. 确保改进后的设计更加优秀
4. 维持整体故事的完整性和吸引力

请输出改进后的完整故事框架。"""

        return PromptTemplate(
            input_variables=["collected_info", "current_framework", "review_feedback", "improvement_focus", "specific_improvements"],
            template=template
        )


    def get_level_scenes_generation_prompt(self) -> PromptTemplate:
        """获取关卡场景剧本生成模板"""
        template = """节奏感知场景剧本生成Prompt
你是一名"剧情驱动教育游戏分镜设计师"。你的任务是基于Story Framework为第{level}关创造沉浸式的冒险分镜，其中学科知识是解决困境、推进剧情的核心工具。

【核心设计理念】
- 学科知识必须是解决剧情困境的唯一途径
- 角色有真实的动机和目标，遇到真实的困难
- 学习过程伪装成"发现世界规律"和"解谜探索"
- 避免"老师出题"模式，采用"伙伴探索"模式
节奏适配：根据关卡特点调整场景氛围和剧情节奏，创造丰富的情感体验层次

【Story Framework】
{story_framework}

【当前任务】
请分析Story Framework中的"关卡{level}"部分，生成该关卡的完整分镜内容。

【关卡节奏识别与场景适配】
首先分析关卡特点，判断应采用的场景氛围类型：

**紧张型场景**（危机关卡、boss战、潜入、时间限制等）
- 场景氛围：高压、紧迫、危险感、肾上腺素飙升
- 剧本节奏：快速推进、直奔主题、少描述多行动
- 时长估计：5-8分钟（快节奏）
- 视觉特点：暗色调、锐利构图、动态光影、紧张氛围
- 知识融入：生死关头的精确计算、关键时刻的救命工具

**探索型场景**（森林入口、新环境、调查线索、解谜等）
- 场景氛围：神秘、好奇、逐步发现、恍然大悟
- 剧本节奏：中等推进、描述与行动并重、层层揭示
- 时长估计：8-12分钟（中等节奏）
- 视觉特点：柔和光线、平衡构图、渐变色调、探索氛围
- 知识融入：解谜钥匙、发现规律、理解机制、探索奥秘

**轻松型场景**（美丽场景、友善NPC、庆祝时刻、日常互动等）
- 场景氛围：温馨、愉快、放松、满足感、成长喜悦
- 剧本节奏：舒缓推进、充分描述、情感交流、关系深化
- 时长估计：10-15分钟（慢节奏）
- 视觉特点：明亮色调、温馨构图、柔和光线、和谐氛围
- 知识融入：自然交流、有趣游戏、轻松练习、友好分享

【氛围匹配的设计原则】

1) **氛围驱动的困境设计**：
   - 困境的紧迫程度要与场景类型匹配
   - 紧张型：真实威胁、时间限制、高风险后果
   - 探索型：谜题障碍、未知挑战、需要智慧
   - 轻松型：友好困难、成长机会、温和挑战

2) **节奏感知的剧情设计**：
   - 剧本内容要与场景氛围完全匹配
   - 紧张型：快速推进的危机处理，高潮迭起
   - 探索型：层层递进的发现过程，恍然大悟
   - 轻松型：舒缓温馨的成长时刻，情感深化

3) **氛围一致的视觉设计**：
   - 图片提示词要体现场景氛围的视觉特征
   - 紧张型：暗色调、锐利线条、动态构图、戏剧性光影
   - 探索型：柔和光线、平衡构图、渐变色彩、神秘氛围
   - 轻松型：明亮色调、温馨构图、柔和光线、和谐画面

【输出格式】

请严格按照以下JSON格式输出，确保是有效的JSON:


{{{{
  "分镜基础信息": {{
    "分镜编号": "scene_{{level}}",
    "分镜标题": "关卡{{level}}-[场景名称]",
    "场景节奏类型": "紧张型 / 探索型 / 轻松型",
    "场景氛围": "[具体的氛围描述，体现节奏类型特点]",
    "时长估计": "[根据节奏类型调整的时长]",
    "关键事件": "[符合场景氛围的具体事件描述]"
  }},
  "人物档案": {{
    "主角": {{
      "角色名": "[从Story Framework提取主角名称]",
      "外貌": "[从Story Framework提取主角外貌描述]",
      "性格": "[从Story Framework提取主角性格特点]",
      "特殊能力": "[从Story Framework提取主角特殊能力]"
    }},
    "NPC": {{
      "角色名": "[从Story Framework提取NPC名称]",
      "外貌": "[从Story Framework提取NPC外貌描述]",
      "性格": "[从Story Framework提取NPC性格特点]",
      "作用": "[从Story Framework提取NPC在故事中的作用]"
    }}
  }},
  "人物对话": [
    {{
      "轮次": 1,
      "NPC": "[基于Story Framework的角色性格，结合场景氛围开场对话]",
      "主角": "[符合Story Framework角色设定和当前场景氛围的回应]"
    }},
    {{
      "轮次": 2,
      "NPC": "[推进Story Framework故事线和场景剧情的对话]",
      "主角": "[体现Story Framework角色成长和场景互动的回应]"
    }}
  ],
  "图片生成提示词": {{
    "视觉风格": "[与Story Framework世界观和场景氛围匹配的艺术风格]",
    "场景描述": "[根据节奏类型调整的具体视觉氛围，包括色调、光影、构图特点]",
    "角色描述": "[基于场景氛围的角色表现和动作状态]",
    "构图要求": "[根据场景节奏选择的最佳构图方式]",
    "技术参数": "高分辨率，16:9横版构图，适合移动端游戏界面展示"
  }},
  "剧本": {{
    "旁白": "[根据场景节奏类型营造相应氛围的开场描述]",
    "情节描述": "[匹配场景氛围的完整冒险弧线，体现相应的节奏感和情感强度]",
    "互动设计": "[根据场景类型调整的学习机制包装方式，确保氛围一致性]"
  }}
}}}}

【格式要求】
- 所有字段必须填写，体现场景氛围特点
- 场景氛围要与节奏类型完全匹配，避免氛围冲突
- 剧本内容要突出相应的节奏感和情感强度
- 图片提示词必须体现场景氛围的视觉特征
- **关键**：整个分镜的所有元素都要服务于同一种氛围营造
- **避免**：在同一分镜中混合不同节奏类型的元素
- 使用简洁的文档格式，用代码块标记图片提示词和剧本段落内容

请严格按照上述要求生成氛围一致的分镜脚本。"""

        return PromptTemplate(
            input_variables=["story_framework", "level"],
            template=template
        )


# 便利函数
def create_prompt_templates() -> PromptTemplates:
    """创建提示词模板实例的便利函数"""
    return PromptTemplates()


# 测试函数
def test_templates():
    """测试模板生成效果"""
    templates = create_prompt_templates()

    # 测试基础模板
    print("=== 基础信息收集模板 ===")
    basic_prompt = templates.get_prompt_by_stage("basic_info")
    formatted = basic_prompt.format(
        history="用户：你好\n助手：您好，我来帮您设计教育游戏",
        input="我想做一个数学游戏"
    )
    print(formatted)

    # 测试动态模板
    print("\n=== 动态模板 ===")
    collected_info = {
        "subject": "数学",
        "grade": "三年级",
        "knowledge_points": None,
        "teaching_goals": None
    }

    lacked_info = {
        "stage": "basic_info",
        "missing_fields": ["knowledge_points"],
        "missing_details": {"knowledge_points": "需要明确具体知识点"},
        "completion_rate": 0.67
    }

    dynamic_prompt = templates.generate_dynamic_prompt("basic_info", collected_info, lacked_info)
    formatted_dynamic = dynamic_prompt.format(
        history="用户：三年级数学游戏\n助手：很好，请告诉我具体的知识点",
        input="加法运算"
    )
    print(formatted_dynamic)


if __name__ == "__main__":
    test_templates()