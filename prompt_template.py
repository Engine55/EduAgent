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

        # 场景需求收集模板
        self.scene_info_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""你是专业的教育游戏设计助手。最后需要确定具体的场景和互动需求。

对话历史：
{history}

当前任务：确定场景需求和互动方式
需要了解的信息：
- 希望的场景类型（如：森林冒险、城堡解谜、太空探索等）
- 互动方式偏好（如：选择题答题、拖拽操作、语音互动等）
- 奖励和评估机制想法

用户输入：{input}

请了解用户对游戏场景和互动方式的具体想法，确保游戏既有趣又有教育意义。

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

        # 场景需求部分
        scene_items = []
        if collected_info.get("scene_requirements"):
            scenes = "、".join(collected_info['scene_requirements'])
            scene_items.append(f"✓ 场景需求：{scenes}")
        if collected_info.get("interaction_requirements"):
            interactions = "、".join(collected_info['interaction_requirements'])
            scene_items.append(f"✓ 互动方式：{interactions}")

        if scene_items:
            formatted_sections.append("【场景设计】\n" + "\n".join(scene_items))

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

        # 阶段特定指导
        stage_specific_guidance = {
            "basic_info": "请重点了解学科、年级和具体知识点，这些是游戏设计的基础。",
            "teaching_info": "请深入挖掘教学目标和学生的学习困难，这决定了游戏的教育价值。",
            "gamestyle_info": "请了解用户的喜好，打造有吸引力的游戏世界。",
            "scene_info": "请确定具体的场景和互动设计，让教育目标通过游戏玩法实现。"
        }

        specific_guidance = stage_specific_guidance.get(stage, "")

        return f"{base_encouragement} {specific_guidance}".strip()


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