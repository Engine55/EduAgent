#!/usr/bin/env python3
"""
调试JSON解析问题的脚本
"""

import json
import sys
import os
import asyncio
from datetime import datetime

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from reasoning_graph import ReasoningGraph, ReasoningState

async def debug_json_parsing():
    """调试JSON解析问题"""

    print("调试JSON解析问题...")

    # 创建推理图
    reasoning_graph = ReasoningGraph()

    # 简化的collected_info
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

    # 简化的故事框架
    story_framework = """
【RPG故事框架】
游戏标题：数学冒险王国
背景设定：在魔法森林中，玩家扮演一位小勇士，通过解决数学问题来拯救森林中的动物朋友们。
关卡1设计：神秘森林入口，玩家需要通过加法计算打开森林大门。
"""

    try:
        # 直接调用LLM测试场景生成
        from prompt_templates import create_prompt_templates
        templates = create_prompt_templates()
        scene_prompt = templates.get_level_scenes_generation_prompt()

        formatted_prompt = scene_prompt.format(
            story_framework=story_framework,
            level=1
        )

        print("调用LLM生成场景...")
        print(f"Prompt长度: {len(formatted_prompt)}")

        # 调用LLM
        response = await reasoning_graph.llm.ainvoke([{"role": "user", "content": formatted_prompt}])
        scenes_content = response.content

        print(f"LLM返回内容长度: {len(scenes_content)}")
        print("LLM返回内容前500字符:")
        print("-" * 50)
        print(scenes_content[:500])
        print("-" * 50)

        # 尝试提取JSON
        print("尝试提取JSON...")
        json_content = extract_json_from_content(scenes_content)

        if json_content:
            print("成功提取JSON，长度:", len(json_content))
            print("JSON前200字符:")
            print(json_content[:200])

            # 尝试解析JSON
            try:
                parsed_json = json.loads(json_content)
                print("JSON解析成功!")
                print("JSON键:", list(parsed_json.keys()))
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"错误位置: {e.pos if hasattr(e, 'pos') else '未知'}")
                # 显示错误附近的内容
                if hasattr(e, 'pos') and e.pos < len(json_content):
                    start = max(0, e.pos - 50)
                    end = min(len(json_content), e.pos + 50)
                    print("错误附近内容:")
                    print(json_content[start:end])
        else:
            print("未能提取到JSON内容")

    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()

def extract_json_from_content(content: str) -> str:
    """从LLM返回内容中提取JSON"""
    content = content.strip()

    # 方法1：查找```json代码块
    if "```json" in content:
        start_marker = "```json"
        end_marker = "```"

        start_idx = content.find(start_marker)
        if start_idx != -1:
            start_idx += len(start_marker)
            end_idx = content.find(end_marker, start_idx)
            if end_idx != -1:
                json_str = content[start_idx:end_idx].strip()
                return json_str

    # 方法2：查找普通```代码块
    if "```" in content:
        lines = content.split('\n')
        json_lines = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                if in_code_block:
                    break  # 结束代码块
                else:
                    in_code_block = True  # 开始代码块
                    continue
            elif in_code_block:
                json_lines.append(line)

        if json_lines:
            return '\n'.join(json_lines).strip()

    # 方法3：查找大括号包围的JSON
    if '{' in content and '}' in content:
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx + 1]
            return json_str

    return ""

if __name__ == "__main__":
    asyncio.run(debug_json_parsing())