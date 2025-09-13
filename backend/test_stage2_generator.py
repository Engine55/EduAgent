#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第二阶段测试脚本：RPG故事框架生成
简单测试：从Redis读取第一阶段数据 -> 生成第二阶段故事框架
"""

import json
import os
import uuid
from datetime import datetime
from upstash_redis import Redis
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# 第二阶段prompt模板（新版本）
STAGE_2_PROMPT = """你是一名"中小学教育游戏关卡设计师 + 教学法专家 + RPG 剧情编剧"。请基于【输入数据】生成一个"寓教于乐"的完整 RPG 故事框架，并按关卡拆分（**必须生成6个关卡**，难度递增），最终只输出一个 JSON 对象，**不要**输出任何解释或多余文本。

【输入数据】
- 学科：{subject}
- 年级：{grade}
- 知识点：{knowledge_points}      # 列表，示例：["等量相加","乘法交换律",...]
- 教学目标：{teaching_goals}       # 面向本单元整体目标的表述
- 教学难点：{teaching_difficulties}
- 游戏风格：{game_style}          # 如"童话/蒸汽朋克/科幻探险/地城探险"等
- 角色设计：{character_design}     # 仅两个：玩家 + 1 位 NPC（向导/导师/同伴）
- 世界背景：{world_setting}        # 故事设定、主线矛盾、任务缘由
- 场景需求：{scene_requirements}   # "场景=大的关卡舞台"，同一关可内含多个分镜
- 互动需求：{interaction_requirements}

【输出要求】
1) **整体RPG故事框架**（必须包含）：
   - 标题、世界观、主线剧情（3–4句概述）
   - 主要角色：玩家角色 + NPC（各用1句简述外观、性格、功能）
   - 故事推进逻辑：如何通过6个关卡完成教学目标

2) **关卡设计**（**必须生成6个关卡**，每关包含）：
   - 关卡名称 + 教学目标（直接对应 {knowledge_points} 中的某项）
   - 场景名称：具体的游戏场景名称，如"魔法森林入口"、"智慧神殿"等
   - 关卡编号：唯一标识符，格式为"node_1"、"node_2"等
   - 故事情境：2–3句旁白 + NPC/玩家对话，营造学习氛围
   - 知识讲解：以"生活化例子/可视化描述 + 小操作提示"的形式，从**不同维度**解释同一知识点（如：直观演示/操作探索/类比故事/图形化/情境应用/易错纠正）。
   - 难度标签：例如"入门/基础/进阶/强化/综合/Boss复盘"之一。
   - 衔接逻辑：本关与上一关/下一关的知识与剧情连接点。
   - 下一关选项：根据关卡类型提供选择分支（详见下方分支规则）
   - 是否结束节点：标识是否为游戏结束关卡

3) **关卡流转逻辑**：
   - 设计有限非线性的关卡流程，平衡复杂度与可玩性
   - **分支比例规则**：约1/3的关卡设置为"分支关卡"（提供2个下一关选项），其余关卡为"线性关卡"（1个下一关选项）
   - 必须有1-2个结束节点作为游戏终点
   - 所有路径最终都能到达结束节点
   - 关卡编号必须唯一且按"node_1"、"node_2"格式命名

4) **叙事表达**：每关用 2–4 句"故事化旁白 + 角色对话"呈现学习情境（避免艰深术语），与 {game_style}/{world_setting} 一致。

5) **语言风格**：简洁、积极、鼓励式反馈；使用 {grade} 能理解的比喻与词汇。

6) **只输出 JSON 对象**，严格按照以下结构：
{{
  "整体rpg故事框架": {{
    "标题": "...",
    "世界观": "...",
    "主线剧情": "...",
    "主要角色": {{
      "玩家角色": "...",
      "NPC": "..."
    }},
    "故事推进逻辑": "..."
  }},
  "关卡1": {{
    "关卡名称": "...",
    "场景名称": "...",
    "关卡编号": "node_1",
    "教学目标": "...",
    "故事情境": "...",
    "知识讲解": "...",
    "难度标签": "...",
    "衔接逻辑": "...",
    "下一关选项": {{
      "选项1": {{
        "描述": "...",
        "目标关卡": "关卡2",
        "目标节点": "node_2"
      }},
      "选项2": {{
        "描述": "...",
        "目标关卡": "关卡3", 
        "目标节点": "node_3"
      }}
    }},
    "是否结束节点": false
  }},
  "关卡2-关卡6": {{ 同上结构 }},
}}

【严格格式要求】
- **必须生成完整的6个关卡，从"关卡1"到"关卡6"**
- 必须严格按照上述JSON结构输出，不能缺少任何字段
- "难度标签"必须从以下选项中选择：入门/基础/进阶/强化/综合/Boss复盘
- "关卡编号"必须唯一，格式为"node_1"到"node_6"，不能重复
- **分支关卡有2个"下一关选项"，线性关卡有1个"下一关选项"（按照1/3分支比例规则）**
- "下一关选项"中的"目标关卡"和"目标节点"必须对应实际存在的关卡
- 必须至少有1个"是否结束节点"为true的关卡（建议在关卡5或关卡6）
- 结束节点不需要"下一关选项"字段
- 所有字段都必须有实际内容，不能为空或"..."

【评分与自检（由你在生成时内部自查）】
- 教学对齐：本关"教学目标"能被"知识讲解"直接验证。
- 难度递增：后续关卡在题型、情境复杂度、推理步数、易错点上逐步增加。
- 叙事连贯：同一世界观与画风关键词贯穿始终，NPC 语气前后一致。
- 适龄性：删除超出 {grade} 认知的术语或改为比喻解释。
- 格式完整：确保所有必需字段都已填写，JSON结构正确无误。
- 流程完整：检查所有关卡的跳转逻辑，确保没有死路，所有路径都能到达结束节点。
- 分支合理：按照1/3分支比例规则，确保分支关卡提供有意义的选择，线性关卡推进剧情。

请按以上要求直接输出最终 JSON，确保格式完全符合标准。"""


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


def get_stage1_data(redis_client, requirement_id=None):
    """从Redis获取第一阶段数据"""
    try:
        if requirement_id:
            key = f"eduagent:requirements:{requirement_id}"
        else:
            # 获取最新的
            keys = redis_client.keys("eduagent:requirements:requirement_*")
            if not keys:
                print("❌ 没有找到任何数据")
                return None
            key = keys[0]
        
        data = redis_client.get(key)
        if not data:
            print(f"❌ 未找到数据")
            return None
        
        return json.loads(data)
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return None


def generate_story_framework(stage1_data):
    """生成第二阶段故事框架"""
    try:
        # 提取数据
        collected_info = stage1_data.get('collected_info', {})
        
        # 格式化prompt
        formatted_prompt = STAGE_2_PROMPT.format(
            subject=collected_info.get('subject', '未指定'),
            grade=collected_info.get('grade', '未指定'),
            knowledge_points=', '.join(collected_info.get('knowledge_points', [])),
            teaching_goals=', '.join(collected_info.get('teaching_goals', [])),
            teaching_difficulties=', '.join(collected_info.get('teaching_difficulties', [])),
            game_style=collected_info.get('game_style', '未指定'),
            character_design=collected_info.get('character_design', '未指定'),
            world_setting=collected_info.get('world_setting', '未指定'),
            scene_requirements=', '.join(collected_info.get('scene_requirements', [])),
            interaction_requirements=', '.join(collected_info.get('interaction_requirements', []))
        )
        
        print("🎮 正在生成RPG故事框架...")
        
        # 调用OpenAI (新版本API)
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system", 
                    "content": "你是专业的教育游戏故事设计师。"
                },
                {
                    "role": "user", 
                    "content": formatted_prompt
                }
            ],
            temperature=0.8,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return None


def save_to_redis(redis_client, rpg_framework, stages_data):
    """将RPG框架和关卡数据保存到Redis"""
    try:
        # 生成唯一ID
        story_id = f"story_{str(uuid.uuid4())[:8]}"
        timestamp = datetime.now().isoformat()
        
        # 构建保存数据
        story_data = {
            "story_id": story_id,
            "timestamp": timestamp,
            "status": "stage2_complete",
            "rpg_framework": rpg_framework,
            "stages_data": stages_data,
            "total_stages": len(stages_data)
        }
        
        # 保存主数据
        main_key = f"eduagent:stories:{story_id}"
        redis_client.set(main_key, json.dumps(story_data, ensure_ascii=False))
        
        # 保存RPG框架（单独索引）
        rpg_key = f"eduagent:rpg_frameworks:{story_id}"
        redis_client.set(rpg_key, json.dumps(rpg_framework, ensure_ascii=False))
        
        # 保存每个关卡数据（单独索引）
        for i, stage in enumerate(stages_data):
            stage_key = f"eduagent:stages:{story_id}:stage_{i+1}"
            stage_data_with_meta = {
                "story_id": story_id,
                "stage_index": i+1,
                "stage_data": stage,
                "timestamp": timestamp
            }
            redis_client.set(stage_key, json.dumps(stage_data_with_meta, ensure_ascii=False))
        
        # 更新索引列表
        index_key = "eduagent:story_index"
        try:
            current_index = redis_client.get(index_key)
            if current_index:
                story_list = json.loads(current_index)
            else:
                story_list = []
        except:
            story_list = []
        
        # 添加新故事到索引
        story_list.append({
            "story_id": story_id,
            "title": rpg_framework.get("标题", "未命名故事"),
            "timestamp": timestamp,
            "total_stages": len(stages_data),
            "status": "stage2_complete"
        })
        
        # 保存更新的索引
        redis_client.set(index_key, json.dumps(story_list, ensure_ascii=False))
        
        print(f"💾 故事ID: {story_id}")
        print(f"💾 主键: {main_key}")
        print(f"💾 RPG框架键: {rpg_key}")
        print(f"💾 关卡数量: {len(stages_data)}")
        
        return story_id
        
    except Exception as e:
        print(f"❌ 保存到Redis失败: {e}")
        return None


def main():
    """主测试函数"""
    print("🎮 第二阶段测试：RPG故事框架生成")
    print("=" * 50)
    
    # 连接Redis
    redis_client = connect_redis()
    if not redis_client:
        return
    
    # 获取第一阶段数据
    print("📊 获取第一阶段数据...")
    stage1_data = get_stage1_data(redis_client)
    if not stage1_data:
        return
    
    # 显示输入数据概览
    collected_info = stage1_data.get('collected_info', {})
    print(f"📚 学科: {collected_info.get('subject', '未指定')}")
    print(f"🎓 年级: {collected_info.get('grade', '未指定')}")
    print(f"🎨 游戏风格: {collected_info.get('game_style', '未指定')}")
    
    # 生成故事框架
    story_framework = generate_story_framework(stage1_data)
    
    if story_framework:
        print("\n" + "=" * 80)
        print("📄 原始AI输出:")
        print("=" * 80)
        print(f"输出长度: {len(story_framework)}")
        print(f"前100个字符: {story_framework[:100]}...")
        print(f"输出类型: {type(story_framework)}")
        
        try:
            # 尝试清理输出内容
            cleaned_output = story_framework.strip()
            if not cleaned_output:
                print("❌ AI输出为空")
                return
                
            # 移除markdown代码块标记
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:]  # 移除 "```json"
            if cleaned_output.startswith("```"):
                cleaned_output = cleaned_output[3:]   # 移除 "```"
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]  # 移除结尾的 "```"
            
            # 再次清理空白字符
            cleaned_output = cleaned_output.strip()
            
            print(f"🧹 清理后的前100个字符: {cleaned_output[:100]}...")
                
            # 解析JSON结果
            framework_data = json.loads(cleaned_output)
            
            # 分离RPG框架和关卡数据
            rpg_framework = framework_data.get("整体rpg故事框架", {})
            stages_data = []
            
            # 提取所有关卡数据
            for key, value in framework_data.items():
                if key.startswith("关卡") and isinstance(value, dict):
                    stages_data.append(value)
            
            # 分别打印
            print("\n" + "=" * 80)
            print("✅ RPG故事框架:")
            print("=" * 80)
            print(json.dumps(rpg_framework, ensure_ascii=False, indent=2))
            
            print("\n" + "=" * 80)
            print("✅ 关卡数据:")
            print("=" * 80)
            print(json.dumps(stages_data, ensure_ascii=False, indent=2))
            
            # 保存到Redis数据库
            save_success = save_to_redis(redis_client, rpg_framework, stages_data)
            if save_success:
                print(f"\n✅ 数据已成功保存到Redis数据库")
            else:
                print(f"\n❌ 数据保存失败")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"❌ 错误位置: 第{e.lineno}行，第{e.colno}列")
            print("\n完整原始输出:")
            print(story_framework)
    else:
        print("❌ 生成失败 - story_framework为空或None")


if __name__ == "__main__":
    main()