#!/usr/bin/env python3
"""
修复场景生成问题的脚本
从stage1_complete开始执行节点到生成scene和character
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from reasoning_graph import ReasoningGraph, ReasoningState

class SceneGenerationFixer:
    def __init__(self):
        self.reasoning_graph = ReasoningGraph()

    async def fix_scene_generation(self, collected_info: dict, story_framework: str = None):
        """从stage1_complete状态开始修复场景生成"""

        print("开始修复场景生成流程...")

        # 创建一个完成stage1的状态
        state = self._create_stage1_complete_state(collected_info, story_framework)

        print("当前状态:")
        print(f"  - stage1_complete: {state.get('stage1_complete')}")
        print(f"  - ready_for_generation: {state.get('ready_for_generation')}")
        print(f"  - story_framework_approved: {state.get('story_framework_approved')}")

        # 如果没有故事框架，先生成故事框架
        if not story_framework:
            print("生成故事框架...")
            state = await self.reasoning_graph._generate_story_framework(state)
            state = await self.reasoning_graph._review_story_framework(state)

            # 强制通过审核（调试模式）
            if not state.get('story_framework_approved'):
                print("强制通过故事框架审核（调试模式）")
                state['story_framework_approved'] = True
                state['ready_for_generation'] = True

        # 执行分发到关卡节点
        print("分发到关卡生成...")
        state = await self.reasoning_graph._distribute_to_levels(state)

        # 生成第1关卡场景
        print("生成第1关卡场景...")
        state = await self.reasoning_graph._generate_level_scenes(state, level=1)

        # 检查场景生成结果
        level_1_data = state.get('level_details', {}).get('level_1', {})
        print(f"第1关卡场景状态: {level_1_data.get('scenes_status')}")

        if level_1_data.get('scenes_status') == 'failed':
            print(f"场景生成失败: {level_1_data.get('scenes_error')}")
            return state

        # 生成第1关卡角色对话
        print("生成第1关卡角色对话...")
        state = await self.reasoning_graph._generate_level_characters(state, level=1)

        # 检查角色生成结果
        level_1_data = state.get('level_details', {}).get('level_1', {})
        print(f"第1关卡角色状态: {level_1_data.get('characters_status')}")

        if level_1_data.get('characters_status') == 'failed':
            print(f"角色生成失败: {level_1_data.get('characters_error')}")

        # 汇聚结果
        print("汇聚生成结果...")
        state = await self.reasoning_graph._collect_all_level_results(state)

        return state

    def _create_stage1_complete_state(self, collected_info: dict, story_framework: str = None) -> ReasoningState:
        """创建一个完成stage1的状态"""

        # 默认的测试数据
        if not collected_info:
            collected_info = {
                "subject": "数学",
                "grade": "三年级",
                "knowledge_points": ["10以内加法", "数数", "基础运算"],
                "teaching_goals": ["掌握10以内加法运算", "提高计算速度"],
                "teaching_difficulties": ["进位加法", "理解数的概念"],
                "game_style": "卡通RPG冒险",
                "character_design": "可爱的动物角色",
                "world_setting": "魔法森林",
                "plot_requirements": ["闯关模式", "渐进式难度"],
                "interaction_requirements": ["点击操作", "拖拽交互"]
            }

        if not story_framework:
            story_framework = """
【RPG故事框架】
游戏标题：数学冒险王国
背景设定：在魔法森林中，玩家扮演一位小勇士，通过解决数学问题来拯救森林中的动物朋友们。
主线剧情：邪恶巫师用数学咒语困住了森林动物，玩家需要通过正确的加法运算来破解咒语。
关卡设计：6个关卡，每关卡包含不同难度的10以内加法题目。
角色设定：主角小勇士、森林动物NPC、邪恶巫师Boss。
"""

        state = ReasoningState(
            messages=[],
            user_id="test_user",

            # 需求收集状态 - 已完成
            collected_info=collected_info,
            stage1_complete=True,

            # Stage1状态字段
            extracted_info=collected_info,
            current_stage="complete",

            # 详细度评估状态 - 已通过
            sufficiency_score={
                "基础信息充足性": 85.0,
                "教学信息充足性": 80.0,
                "游戏设定充足性": 90.0,
                "情节设定充足性": 85.0
            },
            overall_sufficiency=85.0,
            sufficiency_threshold=75.0,
            sufficiency_passed=True,

            # 输入适宜性检查状态 - 已通过
            input_fitness_result={"input_fitness": "passed"},
            input_fitness_passed=True,
            input_fitness_score=100,

            # 适宜性检查状态 - 已通过
            fitness_assessment={"overall_fitness": "适宜"},
            fitness_concerns=[],
            fitness_passed=True,

            # 故事框架状态 - 已完成
            story_framework=story_framework,
            story_review_result={
                "主线明确性": {"分数": 85},
                "内容一致性": {"分数": 80},
                "剧情连贯性": {"分数": 85},
                "教育融合度": {"分数": 90},
                "吸引力评估": {"分数": 80},
                "总分": 84.0,
                "是否通过": True
            },
            story_iteration_count=1,
            story_framework_approved=True,

            # 关卡详细内容状态 - 待生成
            level_details={},
            level_generation_status="pending",

            # 最终状态 - 准备生成
            ready_for_generation=True,
            final_requirements=collected_info
        )

        return state

    def print_generation_results(self, state: ReasoningState):
        """打印生成结果"""
        print("\n" + "="*50)
        print("生成结果总结")
        print("="*50)

        level_details = state.get('level_details', {})

        for level in range(1, 7):
            level_key = f"level_{level}"
            if level_key in level_details:
                level_data = level_details[level_key]
                print(f"\n第{level}关卡:")
                print(f"  场景状态: {level_data.get('scenes_status', '未知')}")
                print(f"  角色状态: {level_data.get('characters_status', '未知')}")

                if level_data.get('scenes_status') == 'failed':
                    print(f"  场景错误: {level_data.get('scenes_error', '无')}")
                if level_data.get('characters_status') == 'failed':
                    print(f"  角色错误: {level_data.get('characters_error', '无')}")

                if level_data.get('scenes_status') == 'completed':
                    scenes_content = level_data.get('scenes_script', '')
                    print(f"  场景内容长度: {len(scenes_content)} 字符")

                if level_data.get('characters_status') == 'completed':
                    characters_content = level_data.get('characters_dialogue', '')
                    print(f"  角色内容长度: {len(characters_content)} 字符")

        # 保存结果到文件
        self.save_results_to_file(state)

    def save_results_to_file(self, state: ReasoningState):
        """保存结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scene_generation_results_{timestamp}.json"

        # 准备保存的数据
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "story_framework": state.get('story_framework', ''),
            "collected_info": state.get('collected_info', {}),
            "level_details": state.get('level_details', {}),
            "level_generation_status": state.get('level_generation_status', ''),
            "ready_for_generation": state.get('ready_for_generation', False)
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {filename}")
        except Exception as e:
            print(f"\n保存文件失败: {e}")

async def main():
    """主函数"""
    print("场景生成修复工具")
    print("=" * 50)

    # 可以传入自定义的collected_info和story_framework
    collected_info = {
        "subject": "数学",
        "grade": "三年级",
        "knowledge_points": ["10以内加法", "数数"],
        "teaching_goals": ["掌握基础加法"],
        "teaching_difficulties": ["进位加法"],
        "game_style": "RPG冒险",
        "character_design": "卡通动物",
        "world_setting": "魔法森林",
        "plot_requirements": ["闯关冒险"],
        "interaction_requirements": ["点击交互"]
    }

    fixer = SceneGenerationFixer()

    try:
        # 执行修复
        final_state = await fixer.fix_scene_generation(collected_info)

        # 打印结果
        fixer.print_generation_results(final_state)

    except Exception as e:
        print(f"修复过程失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())