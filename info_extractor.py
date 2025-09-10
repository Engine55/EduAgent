from pydantic import BaseModel, Field, validator
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from typing import List, Optional, Dict, Any


class ExtractedInfo(BaseModel):
    """教育游戏需求信息模型"""
    subject: Optional[str] = Field(description="学科，如数学、语文、英语、科学")
    grade: Optional[str] = Field(description="年级，如一年级、二年级、三年级")
    knowledge_points: Optional[List[str]] = Field(description="具体知识点列表")
    teaching_goals: Optional[List[str]] = Field(description="教学目标列表")
    teaching_difficulties: Optional[List[str]] = Field(description="教学难点列表")
    game_style: Optional[str] = Field(description="游戏风格，如魔法冒险、科幻探索、童话故事")
    character_design: Optional[str] = Field(description="角色设计偏好")
    world_setting: Optional[str] = Field(description="世界观背景设定")
    scene_requirements: Optional[List[str]] = Field(description="场景需求列表")
    interaction_requirements: Optional[List[str]] = Field(description="互动方式需求列表")

    # 只保留基本的数据清理
    @validator('*', pre=True)
    def clean_data(cls, v):
        """基本的数据清理"""
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        elif isinstance(v, list):
            cleaned_list = [item.strip() for item in v if item and item.strip()]
            return cleaned_list if cleaned_list else None
        return v


class InfoExtractor:
    def __init__(self, llm: ChatOpenAI):
        """初始化信息提取器"""
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=ExtractedInfo)

    async def extract_from_user_input(self, user_input: str) -> Dict[str, Any]:
        """从用户输入中提取信息 - 完全依赖AI模型"""
        try:
            extraction_prompt = PromptTemplate(
                template="""
请智能提取并标准化以下用户输入中的教育游戏需求信息：

用户输入：{user_input}

请发挥你的理解能力：
- 自动识别和标准化学科、年级信息（如："3年级"→"三年级"，"math"→"数学"）
- 智能推断知识点、教学目标等信息
- 理解游戏风格、角色设计等偏好
- 如果某项信息不存在或不确定，请返回null

{format_instructions}
""",
                input_variables=["user_input"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )

            chain = LLMChain(
                llm=self.llm,
                prompt=extraction_prompt,
                output_parser=self.parser
            )

            result = await chain.arun(user_input=user_input)
            return result.dict(exclude_none=True)

        except Exception as e:
            print(f"信息提取失败: {e}")
            # 返回空字典，让系统自然处理
            return {}

    async def extract_from_conversation(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """从完整对话中提取信息（可选功能）"""
        conversation_text = f"用户输入：{user_input}\nAI回复：{ai_response}"
        return await self.extract_from_user_input(conversation_text)


# 便利函数
def create_info_extractor(model_name: str = "gpt-4o-mini") -> InfoExtractor:
    """创建信息提取器的便利函数"""
    llm = ChatOpenAI(model=model_name, temperature=0.3)
    return InfoExtractor(llm)