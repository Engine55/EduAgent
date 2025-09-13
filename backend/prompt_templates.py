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
            basic_items.append(f"✓ 学科：{collected_info['subject']}")
        if collected_info.get("grade"):
            basic_items.append(f"✓ 年级：{collected_info['grade']}")
        if collected_info.get("knowledge_points"):
            points = "、".join(collected_info['knowledge_points'])
            basic_items.append(f"✓ 知识点：{points}")

        if basic_items:
            formatted_sections.append("【基础信息】\n" + "\n".join(basic_items))

        # 教学信息部分
        teaching_items = []
        if collected_info.get("teaching_goals"):
            goals = "、".join(collected_info['teaching_goals'])
            teaching_items.append(f"✓ 教学目标：{goals}")
        if collected_info.get("teaching_difficulties"):
            difficulties = "、".join(collected_info['teaching_difficulties'])
            teaching_items.append(f"✓ 教学难点：{difficulties}")

        if teaching_items:
            formatted_sections.append("【教学需求】\n" + "\n".join(teaching_items))

        # 游戏设定部分
        gamestyle_items = []
        if collected_info.get("game_style"):
            gamestyle_items.append(f"✓ 游戏风格：{collected_info['game_style']}")
        if collected_info.get("character_design"):
            gamestyle_items.append(f"✓ 角色设计：{collected_info['character_design']}")
        if collected_info.get("world_setting"):
            gamestyle_items.append(f"✓ 世界背景：{collected_info['world_setting']}")

        if gamestyle_items:
            formatted_sections.append("【游戏设定】\n" + "\n".join(gamestyle_items))

        # 情节需求部分
        scene_items = []
        if collected_info.get("plot_requirements"):
            plots = "、".join(collected_info['plot_requirements'])
            scene_items.append(f"✓ 情节需求：{plots}")
        if collected_info.get("interaction_requirements"):
            interactions = "、".join(collected_info['interaction_requirements'])
            scene_items.append(f"✓ 互动方式：{interactions}")

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
            missing_items.append(f"• {description}")

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
        "基础信息充足性": 85,
        "教学信息充足性": 75,
        "游戏设定充足性": 80,
        "情节设定充足性": 70
    }},
    "dimension_analysis": {{
        "基础信息充足性": "学科和年级信息明确，知识点具体",
        "教学信息充足性": "教学目标清晰，难点识别准确",
        "游戏设定充足性": "游戏风格和角色设计完整",
        "情节设定充足性": "故事情节和互动方式需要更多细节"
    }},
    "overall_score": 77.5,
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
    "input_fitness": "passed",
    "fitness_score": 85,
    "issues": [
        {{
            "category": "逻辑合理性",
            "severity": "high",
            "description": "具体问题描述",
            "suggestion": "改进建议"
        }}
    ],
    "assessment_summary": "输入内容整体评估"
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
        "overall_fitness": "passed",
        "concerns": [
            {{
                "category": "年龄适宜性",
                "severity": "medium",
                "description": "具体问题描述",
                "suggestion": "具体改进建议"
            }}
        ],
        "positive_aspects": ["积极方面1", "积极方面2"],
        "fitness_score": 85,
        "assessment_summary": "整体适宜性总结"
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
        
        return PromptTemplate(
            input_variables=["collected_info", "sufficiency_scores", "average_score", "conversation_context"],
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