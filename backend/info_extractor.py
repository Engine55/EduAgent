from pydantic import BaseModel, Field, validator
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from typing import List, Optional, Dict, Any


# 拆分的模型定义
class BasicInfoExtracted(BaseModel):
    """基础信息提取模型"""
    subject: Optional[str] = Field(None, description="学科，如数学、语文、英语、科学")
    grade: Optional[str] = Field(None, description="年级，如一年级、二年级、三年级")
    knowledge_points: Optional[List[str]] = Field(None, description="具体知识点列表")
    
    class Config:
        extra = "forbid"


class TeachingInfoExtracted(BaseModel):
    """教学信息提取模型"""
    teaching_goals: Optional[List[str]] = Field(None, description="教学目标列表")
    teaching_difficulties: Optional[List[str]] = Field(None, description="教学难点列表")
    
    class Config:
        extra = "forbid"


class GameStyleExtracted(BaseModel):
    """游戏风格信息提取模型"""
    game_style: Optional[str] = Field(None, description="游戏风格，如魔法冒险、科幻探索、童话故事")
    character_design: Optional[str] = Field(None, description="角色设计偏好")
    world_setting: Optional[str] = Field(None, description="世界观背景设定")
    
    class Config:
        extra = "forbid"


class SceneInfoExtracted(BaseModel):
    """场景信息提取模型"""
    plot_requirements: Optional[List[str]] = Field(None, description="情节需求列表")
    interaction_requirements: Optional[List[str]] = Field(None, description="互动方式需求列表")
    
    class Config:
        extra = "forbid"


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
    plot_requirements: Optional[List[str]] = Field(description="情节需求列表")
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
        
        # 为每个stage创建parser
        self.parsers = {
            "basic_info": PydanticOutputParser(pydantic_object=BasicInfoExtracted),
            "teaching_info": PydanticOutputParser(pydantic_object=TeachingInfoExtracted),
            "gamestyle_info": PydanticOutputParser(pydantic_object=GameStyleExtracted),
            "scene_info": PydanticOutputParser(pydantic_object=SceneInfoExtracted)
        }

    async def extract_from_user_input(self, user_input: str, stage: str = "basic_info") -> Dict[str, Any]:
        """从用户输入中提取信息 - 根据stage使用不同的parser"""

        try:
            # 获取对应stage的parser
            parser = self.parsers.get(stage, self.parsers["basic_info"])
            print(f"Using parser for stage: {stage}")

            # 构建完整的提取提示
            extraction_prompt = PromptTemplate(
                template="""
你是专业的信息提取器，需要严格按照规则从用户输入中提取信息。

【信息提取严格规则】

核心原则：
1. 只提取用户明确表达的内容，绝不进行任何推断、联想或补充
2. 每个信息点必须能在用户原话中找到直接对应的词句
3. 严格禁止跨信息类别的推断（比如根据学科推断游戏风格）
4. 用户没有明确说明的信息类别必须标记为空值

提取标准：
✅ 可以提取：用户直接说出的具体内容
❌ 不能提取：需要推理、猜测、常识判断的内容

严格禁止的推断行为：
- 根据学科类型推断教学方式
- 根据年级推断角色设计
- 根据知识点推断游戏风格  
- 根据教学目标推断互动方式
- 根据常识或经验补充用户未说的信息

示例对比：
用户："我要给三年级做数学游戏，学习加法"
✅ 正确：提取"三年级"、"数学"、"加法"
❌ 错误：推断"卡通风格"、"可爱角色"、"数字王国"

用户："希望孩子在魔法森林学拼音，主角是小兔子"  
✅ 正确：提取"拼音"、"魔法森林"、"小兔子"
❌ 错误：推断"提高拼音能力"、"拼音难记"

质量验证：
每个提取的信息都要回答：用户是否明确说了这个内容？
如果答案是"需要推断"或"根据常识"，则必须标记为空值。

{format_instructions}

用户输入："{user_input}"

请严格按照规则进行提取，用户没有明确说出的信息必须标记为null。
""",
                input_variables=["user_input"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )

            chain = LLMChain(
                llm=self.llm,
                prompt=extraction_prompt,
                output_parser=parser
            )

            result = await chain.arun(user_input=user_input)
            print(f"Extracted for {stage}: {result.dict()}")
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
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    llm = ChatOpenAI(
        model=model_name, 
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    return InfoExtractor(llm)