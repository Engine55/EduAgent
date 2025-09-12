#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
场景生成器：Stage2 RPG框架生成和Stage3场景生成
基于Stage1收集的信息生成完整的教育游戏内容
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from upstash_redis import Redis
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量
load_dotenv()

# Stage2 RPG框架生成prompt
STAGE_2_PROMPT = """你是一名"剧情驱动教育游戏设计师"。你的任务是创造一个真正的故事冒险，其中{subject}知识是解决困境、推进剧情的核心工具，而不是附加的学习任务。**必须生成6个关卡**，每个关卡都有真实的困境需要数学知识才能突破。

【核心设计理念】
- 每个关卡角色都面临真实困境，{subject}知识是解决困境的唯一途径
- 避免"老师出题学生答题"模式，营造"冒险者遇到困难并解决"氛围
- 知识点要融入世界观，成为这个世界的自然法则
- 学习过程伪装成"发现世界规律"和"解谜探索"

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

【剧情驱动框架设计】
1) **整体RPG冒险框架**：
   - 标题：体现冒险感和{subject}融合的标题
   - 世界观：{subject}知识是这个世界运行的核心规律
   - 主线剧情：角色有明确目标，遇到真实困境，必须学会{subject}规律才能达成目标
   - 主要角色：玩家是冒险者，NPC是探索伙伴（不是老师）
   - 故事推进逻辑：每个困境的解决都推进主线剧情

2) **关卡困境设计**（**必须生成6个关卡**）：
   - 关卡名称：体现困境性质，如"失控的魔法阵"、"古老机关的秘密"
   - 场景名称：具体的冒险场景，营造紧迫感
   - 关卡编号：唯一标识符，格式为"node_1"、"node_2"等  
   - 教学目标：对应{knowledge_points}，但包装成"需要掌握的世界规律"
   - 故事情境：描述角色面临的真实困境，制造紧张感和探索欲望
   - 知识讲解：将{subject}知识包装成"世界法则"，通过角色探索自然发现
   - 困境解决：具体说明{subject}知识如何成为解决困境的关键
   - 难度标签：困境复杂程度递增
   - 衔接逻辑：前一个困境的解决为下一个困境埋下伏笔
   - 下一关选项：基于解决困境后的剧情发展提供选择
   - 是否结束节点：标识是否达成最终目标

3) **关卡流转逻辑**：
   - 设计非线性的关卡流程，允许玩家根据选择走不同路径
   - 确保每个关卡都有2个下一关选项（除结束节点外）
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
      "玩家角色": {{
        "角色名": "...",
        "外貌特征": "详细的外貌描述，适合全程使用",
        "核心性格": "3-4个关键性格特质",
        "背景故事": "角色的来历和动机",
        "成长轨迹": "在6个关卡中的能力和心理成长路线",
        "特殊能力": "随剧情发展的能力变化"
      }},
      "NPC": {{
        "角色名": "...",
        "外貌特征": "详细的外貌描述，适合全程使用",
        "核心性格": "3-4个关键性格特质", 
        "背景故事": "与玩家的关系和个人经历",
        "在剧情中的作用": "不同阶段的功能变化",
        "知识背景": "掌握哪些世界法则和智慧"
      }}
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
- **每个非结束关卡必须有且仅有2个"下一关选项"（选项1和选项2）**
- "下一关选项"中的"目标关卡"和"目标节点"必须对应实际存在的关卡
- 必须至少有1个"是否结束节点"为true的关卡（建议在关卡5或关卡6）
- 结束节点不需要"下一关选项"字段
- 所有字段都必须有实际内容，不能为空或"..."

【剧情驱动自检标准】
- 困境真实性：每个关卡的困境都是角色世界中的真实问题，不是为了学习而设计的
- 知识融合度：{subject}知识看起来是世界的自然法则，解决困境的必备工具
- 情感动机：角色有真实的目标追求，困境带来挫败感，解决带来成就感
- 冒险氛围：避免"课堂感"，营造"探索解谜"的紧张和兴奋
- 伙伴关系：NPC与玩家是探索伙伴关系，共同面对困境，不是师生关系
- 剧情推进：每个困境的解决都获得有意义的故事进展，不只是"答对了"
- 世界一致性：{subject}知识在世界观中有合理存在意义，不显突兀
- 适龄挑战：困境难度符合{grade}年级认知水平，但有真实的紧迫感

请按以上要求直接输出最终 JSON，确保格式完全符合标准。"""


class SceneGenerator:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """初始化场景生成器"""
        self.model_name = model_name
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.redis_client = self._connect_redis()

    def _get_stage1_data(self, requirement_id: str) -> Optional[Dict]:
        """从Redis获取Stage1数据"""
        if not self.redis_client:
            return None

        try:
            key = f"eduagent:requirements:{requirement_id}"
            data = self.redis_client.get(key)
            if not data:
                print(f"❌ 未找到数据: {key}")
                return None

            return json.loads(data)
        except Exception as e:
            print(f"❌ 获取Stage1数据失败: {e}")
            return None

    def _connect_redis(self) -> Optional[Redis]:
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
    
    def generate_rpg_framework(self, requirement_id: str) -> Tuple[Optional[Dict], Optional[List[Dict]]]:
        """
        生成RPG框架和关卡数据
        
        Args:
            requirement_id: Stage1收集的需求ID
            
        Returns:
            Tuple[rpg_framework, stages_list]: (RPG框架字典, 关卡列表)
        """
        try:
            # 从Redis获取Stage1数据
            stage1_data = self._get_stage1_data(requirement_id)
            if not stage1_data:
                print(f"❌ 未找到需求数据: {requirement_id}")
                return None, None
                
            # 生成RPG框架
            raw_response = self._generate_story_framework(stage1_data)
            if not raw_response:
                print("❌ AI生成失败")
                return None, None
                
            # 解析和分离数据
            rpg_framework, stages_list = self._parse_framework_response(raw_response)
            if not rpg_framework or not stages_list:
                print("❌ 数据解析失败")
                return None, None
                
            # 保存到Redis
            story_id = self._save_to_redis(rpg_framework, stages_list)
            if story_id:
                print(f"✅ 成功生成并保存，故事ID: {story_id}")
                
            return rpg_framework, stages_list
            
        except Exception as e:
            print(f"❌ 生成RPG框架失败: {e}")
            return None, None
    

    
    def _generate_story_framework(self, stage1_data: Dict) -> Optional[str]:
        """调用OpenAI生成故事框架"""
        try:
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
            
            # 调用OpenAI
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是专业的教育游戏故事设计师。"},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.8,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ OpenAI调用失败: {e}")
            return None
    
    def _parse_framework_response(self, raw_response: str) -> Tuple[Optional[Dict], Optional[List[Dict]]]:
        """解析AI响应，分离RPG框架和关卡数据"""
        try:
            # 清理响应内容
            cleaned_output = raw_response.strip()
            
            # 移除markdown代码块标记
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:]
            if cleaned_output.startswith("```"):
                cleaned_output = cleaned_output[3:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]
                
            cleaned_output = cleaned_output.strip()
            
            # 解析JSON
            framework_data = json.loads(cleaned_output)
            
            # 分离RPG框架和关卡数据
            rpg_framework = framework_data.get("整体rpg故事框架", {})
            stages_list = []
            
            # 提取所有关卡数据
            for key, value in framework_data.items():
                if key.startswith("关卡") and isinstance(value, dict):
                    stages_list.append(value)
            
            # 按关卡编号排序
            stages_list.sort(key=lambda x: x.get("关卡编号", "node_0"))
            
            return rpg_framework, stages_list
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"原始响应前500字符: {raw_response[:500]}")
            return None, None
        except Exception as e:
            print(f"❌ 解析响应失败: {e}")
            return None, None
    
    def _save_to_redis(self, rpg_framework: Dict, stages_list: List[Dict]) -> Optional[str]:
        """保存RPG框架和关卡数据到Redis"""
        if not self.redis_client:
            return None
            
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
                "stages_data": stages_list,
                "total_stages": len(stages_list)
            }
            
            # 保存主数据
            main_key = f"eduagent:stories:{story_id}"
            self.redis_client.set(main_key, json.dumps(story_data, ensure_ascii=False))
            
            # 保存RPG框架（单独索引）
            rpg_key = f"eduagent:rpg_frameworks:{story_id}"
            self.redis_client.set(rpg_key, json.dumps(rpg_framework, ensure_ascii=False))
            
            # 保存每个关卡数据（单独索引）
            for i, stage in enumerate(stages_list):
                stage_key = f"eduagent:stages:{story_id}:stage_{i+1}"
                stage_data_with_meta = {
                    "story_id": story_id,
                    "stage_index": i+1,
                    "stage_data": stage,
                    "timestamp": timestamp
                }
                self.redis_client.set(stage_key, json.dumps(stage_data_with_meta, ensure_ascii=False))
            
            # 更新索引列表
            self._update_story_index(story_id, rpg_framework, stages_list, timestamp)
            
            return story_id
            
        except Exception as e:
            print(f"❌ 保存到Redis失败: {e}")
            return None
    
    def _update_story_index(self, story_id: str, rpg_framework: Dict, stages_list: List[Dict], timestamp: str):
        """更新故事索引"""
        try:
            index_key = "eduagent:story_index"
            
            # 获取当前索引
            try:
                current_index = self.redis_client.get(index_key)
                story_list = json.loads(current_index) if current_index else []
            except:
                story_list = []
            
            # 添加新故事到索引
            story_list.append({
                "story_id": story_id,
                "title": rpg_framework.get("标题", "未命名故事"),
                "timestamp": timestamp,
                "total_stages": len(stages_list),
                "status": "stage2_complete"
            })
            
            # 保存更新的索引
            self.redis_client.set(index_key, json.dumps(story_list, ensure_ascii=False))
            
        except Exception as e:
            print(f"❌ 更新故事索引失败: {e}")
    
    def get_story_by_id(self, story_id: str) -> Optional[Dict]:
        """根据ID获取完整故事数据"""
        if not self.redis_client:
            return None
            
        try:
            key = f"eduagent:stories:{story_id}"
            data = self.redis_client.get(key)
            if not data:
                return None
                
            return json.loads(data)
        except Exception as e:
            print(f"❌ 获取故事数据失败: {e}")
            return None
    
    def list_all_stories(self) -> List[Dict]:
        """列出所有故事"""
        if not self.redis_client:
            return []
            
        try:
            index_key = "eduagent:story_index"
            data = self.redis_client.get(index_key)
            if not data:
                return []
                
            return json.loads(data)
        except Exception as e:
            print(f"❌ 获取故事列表失败: {e}")
            return []
    
    def generate_complete_storyboards(self, requirement_id: str) -> Tuple[Optional[Dict], Optional[List[Dict]], Optional[List[Dict]]]:
        """
        生成完整的RPG框架、关卡数据和所有故事板
        
        Args:
            requirement_id: Stage1收集的需求ID
            
        Returns:
            Tuple[rpg_framework, stages_list, storyboards_list]: (RPG框架, 关卡列表, 故事板列表)
        """
        # 先生成RPG框架
        rpg_framework, stages_list = self.generate_rpg_framework(requirement_id)
        if not rpg_framework or not stages_list:
            return None, None, None
            
        # 获取Stage1数据（用于故事板生成）
        stage1_data = self._get_stage1_data(requirement_id)
        if not stage1_data:
            print("❌ 无法获取Stage1数据用于故事板生成")
            return rpg_framework, stages_list, None
            
        collected_info = stage1_data.get('collected_info', {})
        
        # 生成所有关卡的故事板
        print(f"\n🎬 开始生成 {len(stages_list)} 个关卡的故事板...")
        storyboards_list = []
        
        for i, stage_data in enumerate(stages_list):
            print(f"\n🎬 生成第 {i+1}/{len(stages_list)} 个关卡的分镜...")
            print(f"关卡名称: {stage_data.get('关卡名称', f'关卡{i+1}')}")
            
            # 生成单个关卡的故事板
            storyboard_data = self._generate_single_storyboard(
                rpg_framework, 
                stage_data,
                collected_info.get('subject', '未知'),
                collected_info.get('grade', '未知'),
                ', '.join(collected_info.get('interaction_requirements', []))
            )
            
            if storyboard_data:
                storyboard_with_meta = {
                    "stage_index": i + 1,
                    "stage_name": stage_data.get("关卡名称", f"关卡{i+1}"),
                    "stage_id": stage_data.get("关卡编号", f"node_{i+1}"),
                    "storyboard": storyboard_data
                }
                storyboards_list.append(storyboard_with_meta)
                print(f"✅ 第 {i+1} 个关卡分镜生成成功")
            else:
                print(f"❌ 第 {i+1} 个关卡分镜生成失败")
                
        print(f"\n📊 故事板生成完成: {len(storyboards_list)}/{len(stages_list)} 个关卡成功")
        
        return rpg_framework, stages_list, storyboards_list
    
    def _generate_single_storyboard(self, rpg_framework: Dict, stage_data: Dict, subject: str, grade: str, interaction_requirements: str = '') -> Optional[Dict]:
        """生成单个关卡的故事板"""
        try:
            # 格式化prompt
            formatted_prompt = STORYBOARD_PROMPT.format(
                title=rpg_framework.get('标题', ''),
                worldview=rpg_framework.get('世界观', ''),
                main_plot=rpg_framework.get('主线剧情', ''),
                player_character=rpg_framework.get('主要角色', {}).get('玩家角色', {}).get('角色名', ''),
                npc_character=rpg_framework.get('主要角色', {}).get('NPC', {}).get('角色名', ''),
                
                stage_name=stage_data.get('关卡名称', ''),
                scene_name=stage_data.get('场景名称', ''),
                stage_id=stage_data.get('关卡编号', ''),
                teaching_goal=stage_data.get('教学目标', ''),
                story_context=stage_data.get('故事情境', ''),
                knowledge_explanation=stage_data.get('知识讲解', ''),
                next_options=json.dumps(stage_data.get('下一关选项', {}), ensure_ascii=False),
                is_final=stage_data.get('是否结束节点', False),
                
                subject=subject,
                grade=grade,
                interaction_requirements=interaction_requirements
            )
            
            # 调用OpenAI生成故事板
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是专业的教育游戏分镜设计师，擅长创作生动有趣的教学游戏剧本。"},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.8,
                max_tokens=3000
            )
            
            raw_storyboard = response.choices[0].message.content
            
            # 解析JSON
            return self._parse_storyboard_response(raw_storyboard)
            
        except Exception as e:
            print(f"❌ 故事板生成失败: {e}")
            return None
    
    def _parse_storyboard_response(self, raw_response: str) -> Optional[Dict]:
        """解析故事板响应"""
        try:
            # 清理响应内容
            cleaned_output = raw_response.strip()
            
            # 移除markdown代码块标记
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:]
            if cleaned_output.startswith("```"):
                cleaned_output = cleaned_output[3:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]
                
            cleaned_output = cleaned_output.strip()
            
            # 解析JSON
            return json.loads(cleaned_output)
            
        except json.JSONDecodeError as e:
            print(f"❌ 故事板JSON解析失败: {e}")
            print(f"原始响应前200字符: {raw_response[:200]}")
            return None
        except Exception as e:
            print(f"❌ 解析故事板响应失败: {e}")
            return None


# Stage3 故事板生成prompt（剧情驱动版本）
STORYBOARD_PROMPT = """你是一名"剧情驱动教育游戏分镜设计师"。你的任务是为这个关卡创造沉浸式的冒险分镜，其中{subject}知识是解决困境、推进剧情的核心工具，而不是附加的学习任务。

【核心设计理念】
- {subject}知识必须是解决剧情困境的唯一途径
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
  请在"场景转换"中使用格式：目标节点ID: 选项描述
- 是否结束节点：{is_final}

【角色关系发展】
- 主角姓名：{player_character}
- NPC姓名：{npc_character}
- 当前信任度：[基于前几关的交互历史]
- 默契程度：[共同经历后的配合度]
- 情感深度：[友谊或师徒关系的深化]

【玩家互动需求】
- 用户期望的互动方式：{interaction_requirements}
- 必须在设计中体现用户的互动偏好
- 互动形式要与剧情自然融合，不能生硬植入

【剧情衔接要求】
- 如果不是第一关，开场要简单回顾上一关的结果和角色状态
- 不要每关都是紧急危机，可以有探索、准备、过渡类的轻松时刻
- 角色间的对话要体现关系的渐进发展

【剧情驱动分镜设计】

1) **分镜基础信息**：
   - 分镜编号：按"scene_[关卡编号]"格式
   - 场景类型：如"困境发现场景"、"探索解谜场景"、"突破场景"等
   - 时长估计：预估该分镜的游戏时长（分钟）  
   - 关键事件：描述角色面临的真实困境和{subject}知识如何成为解决方案

2) **人物档案**：
   - **重要**：角色基本信息必须从RPG框架中严格继承，保持全程一致性
   - 主角信息：使用RPG框架中的角色名、外貌特征、核心性格（不可修改）
   - NPC信息：使用RPG框架中的角色名、外貌特征、核心性格（不可修改）
   - 仅可发展：当前关卡的具体状态、情感深度、能力成长
   - 角色关系：基于前几关的共同经历，展现信任度和默契度的变化

3) **剧情驱动对话设计**：
   - **困境呈现阶段**：角色遇到真实问题，感到困惑和挫败
   - **探索发现阶段**：角色开始探索，发现问题可能有规律可循
   - **知识融合阶段**：{subject}知识自然浮现为解决方案，不是被"教授"的
   - **互动解谜环节**：根据用户的互动偏好设计具体的互动方式
     * 必须结合用户期望的互动形式（如选择分支、操作任务、推理解谜等）
     * 伪装成世界规律：让{subject}看起来是这个世界的自然法则
     * 探索式发现：玩家通过尝试和观察发现规律
     * 成就感设计：解决问题后获得剧情奖励，不只是"答对了"
     * 失败引导：失败时提供探索线索，引导直到成功
   - **情感变化轨迹**：困惑 → 好奇 → 恍然大悟 → 兴奋成就
   - 对话要体现角色间的真实情感互动，不是问答关系

4) **剧本**：
   - 旁白：冒险情境的沉浸式开场 - 营造紧张、神秘或兴奋的冒险氛围。描述角色面临的真实困境和环境威胁，让玩家感受到"必须行动"的紧迫感。避免教学痕迹，专注于故事张力。
   - 情节描述：完整的冒险弧线 - 从"困境发现"到"探索尝试"到"突破成功"的情感起伏。重点刻画角色的真实动机和情感变化，{subject}知识作为"世界规律"自然出现。要让玩家感到自己是在冒险，不是在上课。
   - 互动设计：伪装成冒险解谜的学习机制 - {subject}知识被包装为"古老智慧"、"神秘法则"或"重要线索"。设计探索式发现过程：玩家通过观察、实验、推理逐步掌握规律。失败时NPC提供情感支持和探索提示，成功时获得真实的剧情奖励和角色成长。

5) **图片提示词**：
   - 视觉风格：与场景名称、RPG框架以及教育目标配套的视觉风格
   - 场景描述：与场景名称、RPG框架以及教育目标配套的故事情景生成的场景
   - 角色描述：NPC和玩家两个角色的详细介绍（合并为一句话描述）
   - 构图要求：根据关卡所处的故事阶段起到的作用性以及符合场景内容、RPG框架的视觉元素
   - 技术参数：高分辨率，适合移动端呈现

【特殊要求】

1) **困境驱动设计原则**：
   - {subject}知识必须是解决剧情困境的唯一有效途径，不是额外考试
   - 困境要有真实的威胁感和紧迫感，角色有强烈的解决动机
   - 知识点伪装成"世界法则"、"古老智慧"或"关键线索"自然出现
   - 选择错误时角色遭遇挫折但获得新线索，引导继续探索直到成功
   - 成功时角色获得真实的剧情进展、能力提升或重要物品奖励

2) **沉浸式对话风格**：
   - NPC是平等的冒险伙伴，不是权威老师，使用探讨式而非教授式语气
   - 失败时表达理解和鼓励："我们再仔细观察一下..."、"或许还有其他线索..."
   - 成功时展现真实的兴奋和感激："太好了！有了你的发现，我们终于..."
   - 语言符合角色身份和{grade}年级理解水平，但要有冒险感和情感深度

3) **剧情连贯性**：
   - 每个场景都推进主线剧情，{subject}知识融入故事发展
   - 角色间的关系和信任随着冒险深入而加深
   - 失败和成功都对后续剧情产生影响，增强选择的意义感
   - 保持世界观一致性，避免破坏第四堵墙

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
      "角色名": "{player_character}",
      "外貌": "从RPG框架中复制外貌特征，保持一致",
      "性格": "从RPG框架中复制核心性格，保持一致",
      "当前状态": "本关卡中角色的具体情况和情感状态",
      "能力成长": "相比前几关获得的新能力或认知"
    }},
    "NPC": {{
      "角色名": "{npc_character}",
      "外貌": "从RPG框架中复制外貌特征，保持一致",
      "性格": "从RPG框架中复制核心性格，保持一致",
      "当前状态": "本关卡中NPC的具体情况和情感状态",
      "与主角关系": "基于共同经历的信任度和默契程度变化"
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
    "探索对话": [
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
    "旁白": "冒险情境的沉浸式开场，营造紧张、神秘或兴奋的冒险氛围。描述角色面临的真实困境和环境威胁，让玩家感受到必须行动的紧迫感。避免教学痕迹，专注于故事张力。",
    "情节描述": "完整的冒险弧线，从困境发现到探索尝试到突破成功的情感起伏。重点刻画角色的真实动机和情感变化，知识作为世界规律自然出现。要让玩家感到自己是在冒险，不是在上课。",
    "互动设计": "伪装成冒险解谜的学习机制，知识被包装为古老智慧、神秘法则或重要线索。设计探索式发现过程：玩家通过观察、实验、推理逐步掌握规律。失败时NPC提供情感支持和探索提示，引导玩家重新尝试直到答对，成功时获得真实的剧情奖励和角色成长。"
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
- 对话内容要具体生动，体现真实的冒险伙伴关系
- 问答环节要伪装成冒险解谜，知识点包装为世界法则或重要线索
- **错误反馈机制**：必须设计引导式提示，让玩家在NPC帮助下重新尝试直到答对
- 剧本三个部分要详细完整，突出冒险氛围和情感张力
- **场景转换格式要求**：必须使用"目标节点ID: 选项描述"的格式，根据关卡数据中的"下一关选项"来生成
- 如果是结束节点，"场景转换"字段可以省略
- JSON格式必须正确，确保可以被解析

请严格按照上述要求生成分镜脚本。"""


# 便利函数
def create_scene_generator(model_name: str = "gpt-4o-mini") -> SceneGenerator:
    """创建场景生成器实例"""
    return SceneGenerator(model_name)


# 测试函数
def test_rpg_generation(requirement_id: str = None):
    """测试RPG框架生成"""
    print("🎮 测试RPG框架生成")
    print("=" * 50)

    generator = create_scene_generator()

    if not requirement_id:
        # 如果没有指定ID，获取最新的
        if not generator.redis_client:
            print("❌ Redis连接失败")
            return

        keys = generator.redis_client.keys("eduagent:requirements:requirement_*")
        if not keys:
            print("❌ 没有找到任何Stage1数据")
            return
        requirement_id = keys[0].split(":")[-1]  # 提取ID部分

    print(f"📊 使用需求ID: {requirement_id}")

    # 生成RPG框架
    rpg_framework, stages_list = generator.generate_rpg_framework(requirement_id)

    if rpg_framework and stages_list:
        print("\n" + "=" * 80)
        print("✅ RPG故事框架:")
        print("=" * 80)
        print(json.dumps(rpg_framework, ensure_ascii=False, indent=2))

        print("\n" + "=" * 80)
        print(f"✅ 关卡数据 (共{len(stages_list)}个关卡):")
        print("=" * 80)
        for i, stage in enumerate(stages_list):
            print(f"\n--- 关卡 {i+1} ---")
            print(json.dumps(stage, ensure_ascii=False, indent=2))
    else:
        print("❌ 生成失败")


def test_complete_generation(requirement_id: str = None):
    """测试完整的内容生成（RPG框架 + 关卡 + 故事板）"""
    print("🎬 测试完整内容生成 (Stage2 + Stage3)")
    print("=" * 60)

    generator = create_scene_generator()

    if not requirement_id:
        # 如果没有指定ID，获取最新的
        if not generator.redis_client:
            print("❌ Redis连接失败")
            return

        keys = generator.redis_client.keys("eduagent:requirements:requirement_*")
        if not keys:
            print("❌ 没有找到任何Stage1数据")
            return
        requirement_id = keys[0].split(":")[-1]  # 提取ID部分

    print(f"📊 使用需求ID: {requirement_id}")

    # 生成完整内容
    rpg_framework, stages_list, storyboards_list = generator.generate_complete_storyboards(requirement_id)

    if rpg_framework and stages_list:
        print("\n" + "=" * 80)
        print("✅ RPG故事框架:")
        print("=" * 80)
        print(json.dumps(rpg_framework, ensure_ascii=False, indent=2))

        print("\n" + "=" * 80)
        print(f"✅ 关卡数据 (共{len(stages_list)}个关卡):")
        print("=" * 80)
        for i, stage in enumerate(stages_list):
            print(f"\n--- 关卡 {i+1} ---")
            print(json.dumps(stage, ensure_ascii=False, indent=2))

        if storyboards_list:
            print("\n" + "=" * 80)
            print(f"✅ 故事板数据 (共{len(storyboards_list)}个关卡):")
            print("=" * 80)
            for storyboard_meta in storyboards_list:
                print(f"\n--- {storyboard_meta['stage_name']} ({storyboard_meta['stage_id']}) ---")
                print(json.dumps(storyboard_meta['storyboard'], ensure_ascii=False, indent=2))
        else:
            print("❌ 故事板生成失败")
    else:
        print("❌ RPG框架生成失败")


if __name__ == "__main__":
    # 运行完整测试
    test_complete_generation('requirement_2025-09-12T10:32:47.628450_ae2dfabe')