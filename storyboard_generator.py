#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分镜生成器：基于RPG框架和关卡数据生成详细分镜脚本
输入：RPG故事框架 + 单个关卡数据
输出：分镜基础信息、人物对话、剧本、图片提示词
"""

import json
import os
from datetime import datetime
from upstash_redis import Redis
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 分镜生成prompt模板
STORYBOARD_PROMPT = """你是一名"教育游戏分镜设计师 + 编剧 + 美术指导"。请基于【RPG框架】和【关卡数据】为这个关卡生成完整的分镜脚本，最终只输出一个 JSON 对象，**不要**输出任何解释或多余文本。

【RPG框架】
- 标题：{title}
- 世界观：{worldview}
- 主线剧情：{main_plot}
- 玩家角色：{player_character}
- NPC角色：{npc_character}

【关卡数据】
- 关卡名称：{stage_name}
- 场景名称：{scene_name}
- 关卡编号：{stage_id}
- 教学目标：{teaching_goal}
- 故事情境：{story_context}
- 知识讲解：{knowledge_explanation}
- 下一关选项：{next_options}
  请在"场景转换"中使用格式：目标节点ID: 选项描述
- 是否结束节点：{is_final}

【学科信息】
- 学科：{subject}
- 年级：{grade}

【输出要求】

1) **分镜基础信息**：
   - 分镜编号：按"scene_[关卡编号]"格式
   - 场景类型：如"对话场景"、"学习场景"、"选择场景"等
   - 时长估计：预估该分镜的游戏时长（分钟）
   - 关键事件：本分镜的核心事件描述

2) **人物档案**：
   - 为本关卡涉及的角色创建详细档案
   - 主角信息：角色名、外貌、性格、特殊能力
   - NPC信息：角色名、外貌、性格、作用
   - 要与RPG框架中的角色设定保持一致
   - 外貌和性格要适合{grade}年级学生理解和喜爱

3) **人物对话**：
   - 根据故事情境设计自然的角色对话
   - 如果是关卡开始：NPC介绍场景、引导学习
   - 如果是学习环节：NPC讲解知识点，玩家可以提问
   - 如果是关卡结尾：必须包含问答环节，格式如下：
     * NPC: 问题内容（根据教学目标设计的题目）
     * 主角选项：A. 选项A内容  B. 选项B内容
     * 反馈机制：根据主角回答问题的对错做出赞赏或者鼓励，并作出相应的解释或者提示
   - 如果不是结束节点：问答后提供通往下个场景的选项，格式为"目标节点ID: 选项描述"
   - 保持角色性格一致，语言符合{grade}年级理解水平
   - 题目内容必须符合{subject}学科和{grade}年级认知水平，能够自然融入RPG故事背景

4) **剧本**：
   - 旁白：故事情境的背景介绍 - 详细描述当前场景的环境、氛围、以及玩家角色所处的状况。要生动具体，让读者能够想象出完整的场景画面。
   - 情节描述：将故事情境写得更加完整详细 - 不仅包含基本的故事背景，还要描述角色的心理状态、环境的细节变化、以及推动剧情发展的关键事件。要有起承转合的完整结构。
   - 互动设计：结合故事情景和RPG框架，根据用户的互动需求来设计具体的互动环节 - 特别是为了解开题目而设计的情景互动。包括：玩家如何发现题目、与NPC的互动过程、解题的具体步骤、以及成功/失败后的反馈机制。要让学习过程自然融入游戏情境中。

5) **图片提示词**：
   - 视觉风格：与场景名称、RPG框架以及教育目标配套的视觉风格
   - 场景描述：与场景名称、RPG框架以及教育目标配套的故事情景生成的场景
   - 角色描述：NPC和玩家两个角色的详细介绍（合并为一句话描述）
   - 构图要求：根据关卡所处的故事阶段起到的作用性以及符合场景内容、RPG框架的视觉元素
   - 技术参数：高分辨率，适合移动端呈现

【特殊要求】

1) **题目设计原则**：
   - 题目内容必须符合{subject}学科和{grade}年级认知水平
   - 题目能够自然融入RPG故事背景和当前场景
   - 选项设置要有一定迷惑性但不过分困难
   - 解释要通俗易懂，结合故事元素

2) **对话风格**：
   - NPC说话要符合其在RPG框架中的人设
   - 语言活泼生动，适合{grade}年级学生
   - 鼓励性语言要真诚不做作
   - 表扬要具体指出学生做得好的地方

3) **场景连贯性**：
   - 与上一关卡的故事自然衔接
   - 为下一关卡做好铺垫
   - 保持整体世界观的一致性

【输出格式】严格按照以下JSON结构：

{{
  "分镜基础信息": {{
    "分镜编号": "scene_{stage_id}",
    "场景类型": "...",
    "时长估计": "...分钟",
    "关键事件": "..."
  }},
  "人物档案": {{
    "主角": {{
      "角色名": "...",
      "外貌": "...",
      "性格": "...",
      "特殊能力": "..."
    }},
    "NPC": {{
      "角色名": "...",
      "外貌": "...",
      "性格": "...",
      "作用": "..."
    }}
  }},
  "人物对话": {{
    "开场对话": [
      {{
        "角色": "NPC",
        "内容": "..."
      }},
      {{
        "角色": "玩家",
        "内容": "..."
      }}
    ],
    "学习对话": [
      {{
        "角色": "NPC", 
        "内容": "..."
      }}
    ],
    "问答环节": {{
      "NPC": "问题内容（根据教学目标设计的具体题目）",
      "主角选项": {{
        "A": "选项A内容",
        "B": "选项B内容",
        "正确答案": "A或B"
      }},
      "反馈机制": {{
        "正确反馈": "表扬和解释为什么正确...",
        "错误反馈": "鼓励性解释和提示..."
      }}
    }},
    "场景转换": {{
      "node_id_1": "选项1描述...",
      "node_id_2": "选项2描述..."
    }}
  }},
  "剧本": {{
    "旁白": "故事情境的背景介绍，详细描述当前场景的环境、氛围、以及玩家角色所处的状况。要生动具体，让读者能够想象出完整的场景画面。",
    "情节描述": "将故事情境写得更加完整详细，不仅包含基本的故事背景，还要描述角色的心理状态、环境的细节变化、以及推动剧情发展的关键事件。要有起承转合的完整结构。",
    "互动设计": "结合故事情景和RPG框架，根据用户的互动需求来设计具体的互动环节，特别是为了解开题目而设计的情景互动。包括：玩家如何发现题目、与NPC的互动过程、解题的具体步骤、以及成功/失败后的反馈机制。要让学习过程自然融入游戏情境中。"
  }},
  "图片提示词": {{
    "视觉风格": "与场景名称、RPG框架以及教育目标配套的视觉风格描述...",
    "场景描述": "与场景名称、RPG框架以及教育目标配套的故事情景生成的场景描述...",
    "角色描述": "NPC角色和玩家角色的详细外观和特征描述...",
    "构图要求": "根据关卡所处的故事阶段起到的作用性以及符合场景内容、RPG框架的视觉元素构图要求...",
    "技术参数": "高分辨率，适合移动端呈现，以及其他技术要求..."
  }}
}}

【格式要求】
- 所有字段必须填写，不能为空或"..."
- 对话内容要具体生动，不能过于简单
- 题目要结合具体的知识点和场景背景
- 剧本的三个部分要详细完整，提供足够的实施指导
- **场景转换格式要求**：必须使用"目标节点ID: 选项描述"的格式，根据关卡数据中的"下一关选项"来生成
- 如果是结束节点，"场景转换"字段可以省略
- JSON格式必须正确，确保可以被解析

请严格按照上述要求生成分镜脚本。"""


def generate_storyboard(rpg_framework, stage_data, subject="", grade=""):
    """生成单个关卡的分镜脚本"""
    try:
        # 格式化prompt
        formatted_prompt = STORYBOARD_PROMPT.format(
            title=rpg_framework.get('标题', ''),
            worldview=rpg_framework.get('世界观', ''),
            main_plot=rpg_framework.get('主线剧情', ''),
            player_character=rpg_framework.get('主要角色', {}).get('玩家角色', ''),
            npc_character=rpg_framework.get('主要角色', {}).get('NPC', ''),
            
            stage_name=stage_data.get('关卡名称', ''),
            scene_name=stage_data.get('场景名称', ''),
            stage_id=stage_data.get('关卡编号', ''),
            teaching_goal=stage_data.get('教学目标', ''),
            story_context=stage_data.get('故事情境', ''),
            knowledge_explanation=stage_data.get('知识讲解', ''),
            next_options=json.dumps(stage_data.get('下一关选项', {}), ensure_ascii=False),
            is_final=stage_data.get('是否结束节点', False),
            
            subject=subject,
            grade=grade
        )
        
        print(f"🎬 正在生成关卡 {stage_data.get('关卡名称', '')} 的分镜脚本...")
        
        # 调用OpenAI API
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "你是专业的教育游戏分镜设计师，擅长创作生动有趣的教学游戏剧本。"
                },
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ],
            temperature=0.8,
            max_tokens=3000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ 分镜生成失败: {e}")
        return None


def clean_and_parse_json(raw_output):
    """清理并解析AI输出的JSON"""
    try:
        # 清理markdown代码块标记
        cleaned = raw_output.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        return json.loads(cleaned)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"原始输出前200字符: {raw_output[:200]}...")
        return None


def connect_redis():
    """连接Redis"""
    try:
        redis = Redis(
            url=os.getenv("UPSTASH_REDIS_URL"),
            token=os.getenv("UPSTASH_REDIS_TOKEN")
        )
        return redis
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return None


def get_story_data(redis_client, story_id=None):
    """从Redis获取故事数据"""
    try:
        if not story_id:
            # 获取最新的故事
            index_key = "eduagent:story_index"
            story_list_data = redis_client.get(index_key)
            if story_list_data:
                story_list = json.loads(story_list_data)
                if story_list:
                    story_id = story_list[-1]["story_id"]
                    print(f"📖 使用最新故事: {story_id}")
                else:
                    print("❌ 没有找到任何故事数据")
                    return None
            else:
                print("❌ 故事索引不存在")
                return None
        
        # 获取故事完整数据
        main_key = f"eduagent:stories:{story_id}"
        story_data = redis_client.get(main_key)
        if story_data:
            return json.loads(story_data)
        else:
            print(f"❌ 未找到故事数据: {story_id}")
            return None
            
    except Exception as e:
        print(f"❌ 获取故事数据失败: {e}")
        return None


def get_stage1_data(redis_client, requirement_id=None):
    """获取第一阶段数据（包含collected_info字段）"""
    try:
        if requirement_id:
            key = f"eduagent:requirements:{requirement_id}"
        else:
            # 获取最新的
            keys = redis_client.keys("eduagent:requirements:requirement_*")
            if not keys:
                print("❌ 没有找到任何第一阶段数据")
                return None
            key = keys[0]
        
        data = redis_client.get(key)
        if not data:
            print(f"❌ 未找到第一阶段数据")
            return None
        
        return json.loads(data)
    except Exception as e:
        print(f"❌ 获取第一阶段数据失败: {e}")
        return None


def generate_all_storyboards(story_id=None):
    """为指定故事生成所有关卡的分镜"""
    # 连接Redis
    redis_client = connect_redis()
    if not redis_client:
        return
    
    # 获取故事数据
    story_data = get_story_data(redis_client, story_id)
    if not story_data:
        return
    
    # 获取第一阶段数据（包含collected_info）
    stage1_data = get_stage1_data(redis_client)
    if not stage1_data:
        print("⚠️ 未找到第一阶段数据，使用默认值")
        collected_info = {}
    else:
        collected_info = stage1_data.get('collected_info', {})
    
    rpg_framework = story_data.get("rpg_framework", {})
    stages_data = story_data.get("stages_data", [])
    
    print(f"🎮 故事标题: {rpg_framework.get('标题', '未知')}")
    print(f"📚 总关卡数: {len(stages_data)}")
    print(f"🎓 学科年级: {collected_info.get('subject', '未知')} - {collected_info.get('grade', '未知')}")
    
    # 生成所有分镜
    all_storyboards = []
    for i, stage_data in enumerate(stages_data):
        print(f"\n🎬 生成第 {i+1}/{len(stages_data)} 个关卡的分镜...")
        print(f"关卡名称: {stage_data.get('关卡名称', f'关卡{i+1}')}")
        
        # 生成分镜，使用collected_info中的字段
        storyboard_raw = generate_storyboard(
            rpg_framework, 
            stage_data, 
            subject=collected_info.get('subject', '未知'),
            grade=collected_info.get('grade', '未知')
        )
        
        if storyboard_raw:
            storyboard = clean_and_parse_json(storyboard_raw)
            if storyboard:
                storyboard_with_meta = {
                    "stage_index": i + 1,
                    "stage_name": stage_data.get("关卡名称", f"关卡{i+1}"),
                    "stage_id": stage_data.get("关卡编号", f"node_{i+1}"),
                    "storyboard": storyboard
                }
                all_storyboards.append(storyboard_with_meta)
                print(f"✅ 第 {i+1} 个关卡分镜生成成功")
            else:
                print(f"❌ 第 {i+1} 个关卡JSON解析失败")
        else:
            print(f"❌ 第 {i+1} 个关卡分镜生成失败")
    
    # 保存到JSON文件
    if all_storyboards:
        output_data = {
            "story_id": story_data.get("story_id", "unknown"),
            "story_title": rpg_framework.get('标题', '未知故事'),
            "generated_time": datetime.now().isoformat(),
            "subject": collected_info.get('subject', '未知'),
            "grade": collected_info.get('grade', '未知'),
            "total_stages": len(stages_data),
            "successful_stages": len(all_storyboards),
            "storyboards": all_storyboards
        }
        
        filename = f"storyboards_{output_data['story_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 所有分镜已保存到: {filename}")
        print(f"📊 成功生成: {len(all_storyboards)}/{len(stages_data)} 个关卡分镜")
        
        return filename
    else:
        print("❌ 没有成功生成任何分镜")
        return None


def test_storyboard_generator():
    """测试分镜生成器"""
    # 示例数据
    rpg_framework = {
        "标题": "魔法王国的数学冒险",
        "世界观": "在充满魔法的王国里，数学公式是施展魔法的关键",
        "主线剧情": "小勇士需要学会各种数学魔法来拯救被诅咒的王国",
        "主要角色": {
            "玩家角色": "充满好奇心的小学生魔法师",
            "NPC": "智慧的老魔法师导师，善良耐心，喜欢用生动的比喻教学"
        }
    }
    
    stage_data = {
        "关卡名称": "加法魔法门",
        "场景名称": "魔法图书馆入口",
        "关卡编号": "node_1",
        "教学目标": "掌握两位数加法运算",
        "故事情境": "小勇士来到魔法图书馆门前，发现门上有一道加法谜题需要解答才能进入",
        "知识讲解": "通过魔法道具演示加法的竖式计算方法",
        "下一关选项": {
            "选项1": {"描述": "进入左侧的基础魔法区", "目标关卡": "关卡2"},
            "选项2": {"描述": "进入右侧的高级魔法区", "目标关卡": "关卡3"}
        },
        "是否结束节点": False
    }
    
    # 生成分镜
    storyboard_raw = generate_storyboard(rpg_framework, stage_data, "数学", "二年级")
    
    if storyboard_raw:
        print("\n" + "="*80)
        print("✅ 生成的分镜脚本:")
        print("="*80)
        
        # 解析并格式化输出
        storyboard = clean_and_parse_json(storyboard_raw)
        if storyboard:
            print(json.dumps(storyboard, ensure_ascii=False, indent=2))
        else:
            print("JSON解析失败，显示原始输出:")
            print(storyboard_raw)
    else:
        print("❌ 分镜生成失败")


if __name__ == "__main__":
    # 使用新的批量生成功能
    generate_all_storyboards()