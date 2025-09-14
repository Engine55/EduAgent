#!/usr/bin/env python3
"""
最终调试脚本 - 直接测试LLM输出和JSON解析
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

async def debug_scene_generation():
    """调试场景生成的完整流程"""

    print("开始调试场景生成...")

    try:
        # 创建推理图
        reasoning_graph = ReasoningGraph()

        # 创建测试状态
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
关卡1设计：神秘森林入口，玩家需要通过加法计算打开森林大门，解救被困的小兔子。
"""

        # 创建完整状态
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

        print("1. 初始化关卡状态...")
        state = await reasoning_graph._distribute_to_levels(state)

        print("2. 生成场景剧本...")

        # 手动调用_generate_level_scenes来捕获详细信息
        level = 1

        # 获取scene prompt模板
        from prompt_templates import create_prompt_templates
        templates = create_prompt_templates()
        scene_prompt = templates.get_level_scenes_generation_prompt()

        formatted_prompt = scene_prompt.format(
            story_framework=story_framework,
            level=level
        )

        print(f"Prompt长度: {len(formatted_prompt)}")
        print("调用LLM...")

        response = await reasoning_graph.llm.ainvoke([{"role": "user", "content": formatted_prompt}])
        scenes_content = response.content

        print(f"LLM返回长度: {len(scenes_content)}")

        # 保存原始内容到文件
        with open("raw_scene_output.txt", "w", encoding="utf-8") as f:
            f.write(scenes_content)
        print("原始输出已保存到 raw_scene_output.txt")

        # 尝试提取JSON
        print("提取JSON...")
        json_content = extract_json_safely(scenes_content)

        if json_content:
            print(f"成功提取JSON，长度: {len(json_content)}")

            # 保存提取的JSON
            with open("extracted_json.txt", "w", encoding="utf-8") as f:
                f.write(json_content)
            print("提取的JSON已保存到 extracted_json.txt")

            # 尝试解析JSON
            try:
                parsed_json = json.loads(json_content)
                print("JSON解析成功!")
                print("顶级键:", list(parsed_json.keys()))

                # 保存解析后的JSON
                with open("parsed_scene.json", "w", encoding="utf-8") as f:
                    json.dump(parsed_json, f, ensure_ascii=False, indent=2)
                print("解析后的JSON已保存到 parsed_scene.json")

            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"错误位置: {e.pos if hasattr(e, 'pos') else '未知'}")

                # 显示错误附近的内容
                if hasattr(e, 'pos') and e.pos < len(json_content):
                    start = max(0, e.pos - 100)
                    end = min(len(json_content), e.pos + 100)
                    print("错误附近内容:")
                    print("-" * 50)
                    print(json_content[start:end])
                    print("-" * 50)

        else:
            print("未能提取到JSON内容")

    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()

def extract_json_safely(content: str) -> str:
    """安全提取JSON内容"""
    content = content.strip()

    # 方法1：查找```json代码块
    if "```json" in content:
        start_marker = "```json"
        end_marker = "```"

        start_idx = content.find(start_marker)
        if start_idx != -1:
            start_idx += len(start_marker)
            # 找到下一个```
            end_idx = content.find(end_marker, start_idx)
            if end_idx != -1:
                json_str = content[start_idx:end_idx].strip()
                return json_str

    # 方法2：查找普通```代码块
    if "```" in content:
        start_idx = content.find("```")
        if start_idx != -1:
            start_idx += 3
            end_idx = content.find("```", start_idx)
            if end_idx != -1:
                json_str = content[start_idx:end_idx].strip()
                return json_str

    # 方法3：查找大括号包围的完整JSON
    if '{' in content and '}' in content:
        # 找到第一个{
        start_idx = content.find('{')
        if start_idx != -1:
            # 从这里开始计算括号匹配
            brace_count = 0
            end_idx = start_idx

            for i, char in enumerate(content[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break

            if brace_count == 0:
                json_str = content[start_idx:end_idx + 1]
                return json_str

    return ""

if __name__ == "__main__":
    asyncio.run(debug_scene_generation())