#!/usr/bin/env python3
"""
简化的场景生成修复脚本
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

async def simple_scene_generation():
    """简单的场景生成测试"""

    print("开始场景生成测试...")

    # 创建推理图
    reasoning_graph = ReasoningGraph()

    # 模拟一个stage1完成的状态
    collected_info = {
        "subject": "数学",
        "grade": "三年级",
        "knowledge_points": ["10以内加法"],
        "teaching_goals": ["掌握基础加法"],
        "teaching_difficulties": ["进位加法"],
        "game_style": "RPG冒险",
        "character_design": "卡通动物",
        "world_setting": "魔法森林",
        "plot_requirements": ["闯关冒险"],
        "interaction_requirements": ["点击交互"]
    }

    story_framework = """
【RPG故事框架】
游戏标题：数学冒险王国
背景设定：在魔法森林中，玩家扮演一位小勇士，通过解决数学问题来拯救森林中的动物朋友们。
主线剧情：邪恶巫师用数学咒语困住了森林动物，玩家需要通过正确的加法运算来破解咒语。
关卡设计：6个关卡，每关卡包含不同难度的10以内加法题目。
角色设定：主角小勇士、森林动物NPC、邪恶巫师Boss。
"""

    # 创建初始状态
    state = ReasoningState(
        messages=[],
        user_id="test_user",
        collected_info=collected_info,
        stage1_complete=True,
        extracted_info=collected_info,
        current_stage="complete",
        sufficiency_score={"基础信息充足性": 85.0},
        overall_sufficiency=85.0,
        sufficiency_threshold=75.0,
        sufficiency_passed=True,
        input_fitness_result={"input_fitness": "passed"},
        input_fitness_passed=True,
        input_fitness_score=100,
        fitness_assessment={"overall_fitness": "适宜"},
        fitness_concerns=[],
        fitness_passed=True,
        story_framework=story_framework,
        story_review_result={"是否通过": True},
        story_iteration_count=1,
        story_framework_approved=True,
        level_details={},
        level_generation_status="pending",
        ready_for_generation=True,
        final_requirements=collected_info
    )

    try:
        print("1. 分发到关卡...")
        state = await reasoning_graph._distribute_to_levels(state)

        print("2. 生成第1关卡场景...")
        state = await reasoning_graph._generate_level_scenes(state, level=1)

        # 检查场景生成结果
        level_1_data = state.get('level_details', {}).get('level_1', {})
        print(f"   场景状态: {level_1_data.get('scenes_status')}")

        if level_1_data.get('scenes_status') == 'completed':
            print("   场景生成成功！")
            scenes_content = level_1_data.get('scenes_script', '')
            print(f"   内容长度: {len(scenes_content)} 字符")

            print("3. 生成第1关卡角色对话...")
            state = await reasoning_graph._generate_level_characters(state, level=1)

            # 检查角色生成结果
            level_1_data = state.get('level_details', {}).get('level_1', {})
            print(f"   角色状态: {level_1_data.get('characters_status')}")

            if level_1_data.get('characters_status') == 'completed':
                print("   角色生成成功！")
                characters_content = level_1_data.get('characters_dialogue', '')
                print(f"   内容长度: {len(characters_content)} 字符")
            else:
                print(f"   角色生成失败: {level_1_data.get('characters_error')}")

        else:
            print(f"   场景生成失败: {level_1_data.get('scenes_error')}")

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scene_results_{timestamp}.json"

        save_data = {
            "timestamp": datetime.now().isoformat(),
            "level_details": state.get('level_details', {}),
            "story_framework": story_framework,
            "collected_info": collected_info
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        print(f"结果已保存到: {filename}")

        # 打印详细结果
        print("\n=== 生成结果详情 ===")
        level_details = state.get('level_details', {})
        for level_key, level_data in level_details.items():
            print(f"\n{level_key}:")
            for key, value in level_data.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {len(value)} 字符")
                else:
                    print(f"  {key}: {value}")

    except Exception as e:
        print(f"生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_scene_generation())