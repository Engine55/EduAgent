#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
分镜生成器：基于RPG框架和关卡数据生成详细分镜脚本
输入：RPG故事框架 + 单个关卡数据
输出：分镜基础信息、人物对话、剧本、图片提示词
"""

import json
import os
import asyncio
import concurrent.futures
from datetime import datetime
from database_client import db_client
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 分镜生成prompt模板
STORYBOARD_PROMPT = """你是一名"剧情驱动教育游戏设计师"。你的任务是创造真正的故事冒险，其中{subject}知识是解决困境、推进剧情的核心工具，而不是附加的学习任务。

【核心设计理念】
- 数学知识必须是解决剧情困境的唯一途径
- 角色有真实的动机和目标，遇到真实的困难
- 学习过程伪装成"发现世界规律"和"解谜探索"
- 避免"老师出题"模式，采用"伙伴探索"模式

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
- 是否结束节点：{is_final}

【剧情驱动设计要求】

1) **分镜基础信息**：
   - 分镜编号：按"scene_[关卡编号]"格式
   - 场景类型：如"困境发现场景"、"探索解谜场景"、"突破场景"等
   - 时长估计：预估该分镜的游戏时长（分钟）  
   - 关键事件：描述角色面临的真实困境和{subject}知识如何成为解决方案

2) **人物档案**：
   - 主角信息：角色名、外貌、性格、当前困境和目标
   - NPC信息：角色名、外貌、性格、与主角的关系、掌握的关键信息
   - 角色必须有真实的动机，不是为了学习而存在
   - 外貌和性格要适合{grade}年级学生理解和喜爱

3) **剧情驱动对话设计**：
   - **困境呈现阶段**：角色遇到真实问题，感到困惑和挫败
   - **探索发现阶段**：角色开始探索，发现问题可能有规律可循
   - **知识融合阶段**：{subject}知识自然浮现为解决方案，不是被"教授"的
   - **互动解谜环节**：玩家运用知识解决困境，推进剧情
     * 伪装成世界规律：让数学看起来是这个世界的自然法则
     * 探索式发现：玩家通过尝试和观察发现规律
     * 成就感设计：解决问题后获得剧情奖励，不只是"答对了"
   - **情感变化轨迹**：困惑 → 好奇 → 恍然大悟 → 兴奋成就
   - 对话要体现角色间的真实情感互动，不是问答关系

4) **沉浸式剧本设计**：
   - 困境设置：详细描述角色面临的具体困境，要让玩家感同身受
   - 探索过程：角色如何一步步发现问题背后的规律，体现思考过程
   - 知识自然呈现：{subject}知识如何作为"世界法则"自然出现，不显突兀
   - 解决方案实施：玩家运用知识解决问题的具体过程和步骤
   - 剧情奖励：成功后获得的故事进展，让玩家有真实的成就感

5) **沉浸式互动设计**：  
   - **世界规律探索**：将{subject}知识包装成这个世界的自然法则
   - **困境解决机制**：设计多种互动方式让玩家"破解"困境：
     * 古老机关：需要数学规律才能开启
     * 自然现象：遵循数学规律的魔法或科学现象  
     * 社交谜题：需要计算才能化解的人际困境
     * 资源管理：需要数学优化的策略决策
   - **反馈设计**：成功时获得剧情推进，失败时提供新的探索线索
   - **沉浸感维护**：始终保持角色动机和世界观的一致性

6) **视觉世界构建**：
   - 视觉风格：体现困境紧张感和解决后成就感的画面风格
   - 场景描述：展现角色困境和{subject}知识融入世界的视觉元素
   - 角色状态：体现角色当前的情感状态和动机
   - 世界细节：暗示{subject}知识在这个世界中的重要地位
   - 技术参数：高分辨率像素艺术风格，适合教育游戏

【剧情驱动核心原则】

1) **困境真实性原则**：
   - 角色面临的困境必须是他们世界中的真实问题
   - {subject}知识是解决困境的唯一合理路径
   - 困境难度适合{grade}年级学生的认知挑战
   - 解决困境后必须获得有意义的故事进展

2) **知识自然融合原则**：
   - {subject}知识看起来是这个世界的自然法则
   - 避免"教学时刻"，采用"发现时刻"
   - 知识点通过角色探索和尝试自然呈现
   - 学习过程伪装成解谜和冒险

3) **情感驱动原则**：
   - 角色有真实的情感动机和目标追求
   - 困境带来真实的挫败感和紧迫感
   - 解决问题带来真实的成就感和故事推进
   - NPC与主角是探索伙伴，不是师生关系

4) **世界观一致性原则**：
   - 每个关卡都推进主线剧情
   - {subject}知识在世界观中有合理的存在意义
   - 角色行为符合其动机和世界设定
   - 保持沉浸感，避免破坏第四堵墙

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
    "剧情解谜环节": {{
      "困境描述": "角色面临的具体困境和挑战",
      "探索过程": "角色如何逐步发现解决方案的线索",
      "世界规律": "这个世界中与{subject}知识相关的自然法则",
      "解谜机制": {{
        "机制类型": "古老机关|自然现象|社交谜题|资源管理",
        "操作说明": "玩家需要进行的具体操作",
        "知识应用": "{subject}知识如何在操作中自然体现",
        "困境线索": "帮助玩家思考的环境线索和角色提示"
      }},
      "成功奖励": {{
        "剧情进展": "解决困境后获得的故事发展",
        "角色成长": "主角在情感和能力上的成长",
        "世界变化": "解决问题对游戏世界产生的积极影响"
      }},
      "引导机制": {{
        "第一次失败": "NPC提供的第一层提示和鼓励",
        "第二次失败": "更直接的线索和思路引导",
        "持续引导": "逐步引导直到学生找到正确答案的机制",
        "最终帮助": "确保学生最终成功的兜底支持"
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
    "互动设计": "结合故事情景和RPG框架，根据用户选择/希望的互动方式来设计具体的互动环节。包括：玩家如何发现题目、与NPC的互动过程、解题的具体步骤、不同互动方式的实现方法（如选择题点击、填空题输入、操作题拖拽等）、以及成功/失败后的反馈机制。要让学习过程自然融入游戏情境中，确保互动方式符合教学目标和学生年龄特点。"
  }},
  "图片提示词": {{
    "视觉风格": "与场景名称、RPG框架以及教育目标配套的视觉风格描述...",
    "场景描述": "与场景名称、RPG框架以及教育目标配套的故事情景生成的场景描述...",
    "角色描述": "NPC角色和玩家角色的详细外观和特征描述...",
    "构图要求": "根据关卡所处的故事阶段起到的作用性以及符合场景内容、RPG框架的视觉元素构图要求...",
    "技术参数": "高分辨率，适合移动端呈现，以及其他技术要求..."
  }}
}}

【剧情驱动填写要求】
- **人物对话**：体现"困惑→探索→发现→成就"的情感轨迹，避免直接教学式问答
- **互动问答环节**：设计成解决剧情困境的关键环节，{subject}知识是突破困境的钥匙
  * NPC字段：描述困境而不是出题
  * 主角选项：体现不同的解决思路，正确答案推进剧情
  * 反馈机制：成功获得剧情奖励，失败获得新线索继续引导
- **剧本三要素**：
  * 旁白：营造困境氛围和紧张感
  * 情节描述：展现角色真实动机和情感变化
  * 互动设计：将{subject}知识包装成世界规律，避免"教学感"
- **图片提示词**：体现角色困境状态和解决后的成就感
- **场景转换**：基于解决困境后的剧情发展，格式："目标节点ID: 选项描述"
- 结束节点可省略场景转换字段
- JSON格式必须正确，所有字段必须详实填写

【核心目标】
让学生感觉在"冒险解谜推进剧情"，而不是"被要求学习做题"。{subject}知识是探索工具，困境是学习动机，成功是真实奖励。

请严格按照剧情驱动理念生成分镜脚本。"""


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
    # 使用数据库客户端
    if not db_client:
        print("❌ 数据库连接失败")
        return
    
    # 获取故事数据
    story_data = get_story_data(story_id)
    if not story_data:
        return
    
    # 获取第一阶段数据（包含collected_info）
    stage1_data = get_stage1_data()
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