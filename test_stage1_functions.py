#!/usr/bin/env python3
"""
测试stage1完成后的函数是否能正确处理部分state数据
主要测试：
1. get_level_scenes_generation_prompt 函数
2. get_level_characters_generation_prompt 函数
"""

import sys
import os
import json
from typing import Dict, Any

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database_client import db_client
from prompt_templates import create_prompt_templates
from reasoning_graph import ReasoningGraph


def create_test_state() -> Dict[str, Any]:
    """创建一个模拟的stage1完成状态"""
    return {
        "conversation_stage": "stage1_complete",
        "session_id": "test_session_001",
        "requirement_id": "test_req_001",
        "basic_info": {
            "grade": "三年级",
            "subject": "数学",
            "knowledge_point": "乘法口诀"
        },
        "story_framework": """
        【RPG教育游戏框架】

        标题：魔法数学王国大冒险

        【背景设定】
        在遥远的魔法王国里，数字精灵掌管着世界的秩序。邪恶的混沌之王偷走了乘法口诀石，导致王国陷入混乱。小勇士必须重新掌握乘法口诀，才能恢复王国的和谐。

        【关卡1 - 森林入口】
        教学目标：掌握2的乘法口诀
        剧情概述：进入魔法森林，遇到被困的数字精灵，需要用2的乘法口诀解救它们
        节奏类型：探索型

        【关卡2 - 水晶洞穴】
        教学目标：掌握3的乘法口诀
        剧情概述：在水晶洞穴中寻找魔法水晶，需要用3的乘法口诀激活水晶能量
        节奏类型：紧张型

        【关卡3 - 魔法城堡】
        教学目标：掌握4和5的乘法口诀
        剧情概述：最终决战混沌之王，需要综合运用乘法口诀
        节奏类型：轻松型
        """,
        "level_details": {
            "level_1": {
                "scene_name": "森林入口探索",
                "scene_data": "小勇士来到魔法森林入口，发现数字精灵2被藤蔓困住..."
            },
            "level_2": {
                "scene_name": "水晶洞穴冒险",
                "scene_data": "洞穴深处闪烁着神秘的光芒，需要找到正确的水晶组合..."
            },
            "level_3": {
                "scene_name": "魔法城堡决战",
                "scene_data": "城堡顶层，混沌之王正在施展邪恶法术..."
            }
        }
    }


def create_partial_state(full_state: Dict[str, Any], keys_to_keep: list) -> Dict[str, Any]:
    """创建部分state数据，模拟某些情况下只传递部分数据的场景"""
    partial_state = {}
    for key in keys_to_keep:
        if key in full_state:
            partial_state[key] = full_state[key]
    return partial_state


def test_scene_generation_function():
    """测试场景生成函数"""
    print("=" * 60)
    print("测试 get_level_scenes_generation_prompt 函数")
    print("=" * 60)

    templates = create_prompt_templates()
    full_state = create_test_state()

    # 测试场景1：完整state数据
    print("\n测试场景1：完整state数据")
    try:
        scene_prompt = templates.get_level_scenes_generation_prompt()
        story_framework = full_state.get("story_framework", "")

        formatted_prompt = scene_prompt.format(
            story_framework=story_framework,
            level=1
        )

        print("完整state数据 - 成功生成prompt")
        print(f"Prompt长度: {len(formatted_prompt)} 字符")
        print("Story framework获取成功:", "是" if story_framework else "否")

    except Exception as e:
        print(f"完整state数据测试失败: {e}")

    # 测试场景2：只有story_framework的部分数据
    print("\n测试场景2：只有story_framework的部分数据")
    partial_state = create_partial_state(full_state, ["story_framework", "conversation_stage"])

    try:
        scene_prompt = templates.get_level_scenes_generation_prompt()
        story_framework = partial_state.get("story_framework", "")

        formatted_prompt = scene_prompt.format(
            story_framework=story_framework,
            level=1
        )

        print("✅ 部分state数据 - 成功生成prompt")
        print(f"Prompt长度: {len(formatted_prompt)} 字符")
        print("Story framework获取成功:", "是" if story_framework else "否")

    except Exception as e:
        print(f"❌ 部分state数据测试失败: {e}")

    # 测试场景3：空的state数据
    print("\n📊 测试场景3：空state数据")
    empty_state = {}

    try:
        scene_prompt = templates.get_level_scenes_generation_prompt()
        story_framework = empty_state.get("story_framework", "")

        formatted_prompt = scene_prompt.format(
            story_framework=story_framework,
            level=1
        )

        print("✅ 空state数据 - 成功生成prompt")
        print(f"Prompt长度: {len(formatted_prompt)} 字符")
        print("Story framework获取成功:", "是" if story_framework else "否")

    except Exception as e:
        print(f"❌ 空state数据测试失败: {e}")


def test_character_generation_function():
    """测试角色对话生成函数"""
    print("\n" + "=" * 60)
    print("测试 get_level_characters_generation_prompt 函数")
    print("=" * 60)

    templates = create_prompt_templates()
    full_state = create_test_state()

    # 测试场景1：完整state数据
    print("\n📊 测试场景1：完整state数据")
    try:
        character_prompt = templates.get_level_characters_generation_prompt()
        story_framework = full_state.get("story_framework", "")

        # 模拟获取场景数据的逻辑
        level = 1
        scene_data = ""
        if "level_details" in full_state and f"level_{level}" in full_state["level_details"]:
            scene_data = full_state["level_details"][f"level_{level}"].get("scene_data", "")

        formatted_prompt = character_prompt.format(
            story_framework=story_framework,
            scene_data=scene_data,
            level=level
        )

        print("✅ 完整state数据 - 成功生成prompt")
        print(f"Prompt长度: {len(formatted_prompt)} 字符")
        print("Story framework获取成功:", "是" if story_framework else "否")
        print("Scene data获取成功:", "是" if scene_data else "否")

    except Exception as e:
        print(f"❌ 完整state数据测试失败: {e}")

    # 测试场景2：缺少level_details的部分数据
    print("\n📊 测试场景2：缺少level_details的部分数据")
    partial_state = create_partial_state(full_state, ["story_framework", "conversation_stage"])

    try:
        character_prompt = templates.get_level_characters_generation_prompt()
        story_framework = partial_state.get("story_framework", "")

        # 模拟获取场景数据的逻辑
        level = 1
        scene_data = ""
        if "level_details" in partial_state and f"level_{level}" in partial_state["level_details"]:
            scene_data = partial_state["level_details"][f"level_{level}"].get("scene_data", "")

        formatted_prompt = character_prompt.format(
            story_framework=story_framework,
            scene_data=scene_data,
            level=level
        )

        print("✅ 部分state数据 - 成功生成prompt")
        print(f"Prompt长度: {len(formatted_prompt)} 字符")
        print("Story framework获取成功:", "是" if story_framework else "否")
        print("Scene data获取成功:", "是" if scene_data else "否")

    except Exception as e:
        print(f"❌ 部分state数据测试失败: {e}")

    # 测试场景3：空的state数据
    print("\n📊 测试场景3：空state数据")
    empty_state = {}

    try:
        character_prompt = templates.get_level_characters_generation_prompt()
        story_framework = empty_state.get("story_framework", "")

        level = 1
        scene_data = ""
        if "level_details" in empty_state and f"level_{level}" in empty_state["level_details"]:
            scene_data = empty_state["level_details"][f"level_{level}"].get("scene_data", "")

        formatted_prompt = character_prompt.format(
            story_framework=story_framework,
            scene_data=scene_data,
            level=level
        )

        print("✅ 空state数据 - 成功生成prompt")
        print(f"Prompt长度: {len(formatted_prompt)} 字符")
        print("Story framework获取成功:", "是" if story_framework else "否")
        print("Scene data获取成功:", "是" if scene_data else "否")

    except Exception as e:
        print(f"❌ 空state数据测试失败: {e}")


def test_reasoning_graph_integration():
    """测试ReasoningGraph中相关函数的集成"""
    print("\n" + "=" * 60)
    print("测试 ReasoningGraph 集成")
    print("=" * 60)

    try:
        graph = ReasoningGraph()
        full_state = create_test_state()

        # 测试从stage1_complete状态开始的处理
        print("\n📊 模拟从stage1_complete开始处理")
        print("State包含的关键信息:")
        print(f"- conversation_stage: {full_state.get('conversation_stage')}")
        print(f"- story_framework存在: {'story_framework' in full_state}")
        print(f"- level_details存在: {'level_details' in full_state}")
        print(f"- level_details关卡数: {len(full_state.get('level_details', {}))}")

        # 模拟部分state数据传递的情况
        partial_state = create_partial_state(full_state, ["story_framework", "conversation_stage", "level_details"])
        print(f"\n📊 模拟部分state传递")
        print(f"- 保留的keys: {list(partial_state.keys())}")
        print("- 这种情况下函数应该仍能正常工作")

    except Exception as e:
        print(f"❌ ReasoningGraph集成测试失败: {e}")


def main():
    """主测试函数"""
    print("开始测试Stage1完成后的函数处理能力")
    print("测试目标：验证get_level_scenes_prompt和get_character函数在处理部分state数据时是否稳定")

    # 运行所有测试
    test_scene_generation_function()
    test_character_generation_function()
    test_reasoning_graph_integration()

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print("如果上述所有测试都显示'成功'，说明函数能够正确处理部分state数据")
    print("如果有任何测试失败，说明需要增加对缺失数据的防护处理")
    print("\n建议：")
    print("1. 确保所有函数都有适当的默认值处理")
    print("2. 在访问嵌套字典时使用.get()方法而不是直接索引")
    print("3. 添加数据验证步骤，在处理前检查必需的字段是否存在")


if __name__ == "__main__":
    main()