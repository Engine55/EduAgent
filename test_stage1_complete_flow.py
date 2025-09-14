#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试从Stage1 Complete状态开始到流程结束的完整流程
模拟已有的Stage1数据，然后测试关卡生成和数据处理是否正常
验证requirement_id传递和前端数据映射是否正确
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 添加backend路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from agent_service import AgentService
from database_client import DatabaseClient

async def test_complete_flow():
    """测试从stage1_complete开始的完整流程"""

    print("=" * 60)
    print("测试Stage1 Complete到流程结束")
    print("=" * 60)

    try:
        # 1. 初始化服务
        print("\n1. 初始化服务...")
        agent_service = AgentService()
        db_client = DatabaseClient()

        # 2. 模拟已有的Stage1完成数据
        print("\n2. 模拟Stage1完成状态...")

        # 创建模拟的Stage1数据
        mock_collected_info = {
            "subject": "数学",
            "grade": "三年级",
            "knowledge_points": ["10以内加减法", "进位退位计算"],
            "teaching_goals": ["掌握10以内加减法的基本运算", "解决进位退位计算难点"],
            "teaching_difficulties": ["进位退位时容易出错", "计算速度慢"],
            "game_style": "RPG冒险风格",
            "character_design": "勇敢的小冒险家主角",
            "world_setting": "魔法森林探险",
            "plot_requirements": "遇到各种数学谜题才能前进",
            "interaction_requirements": "智慧老人或森林精灵引导思考"
        }

        # 初始化推理状态并直接设置为stage1_complete状态
        reasoning_state = agent_service.reasoning_graph.initialize_reasoning_state(
            session_id=agent_service.session_id,
            user_id=agent_service.user_id,
            collected_info=mock_collected_info
        )

        # 设置为已完成状态
        reasoning_state["collected_info"] = mock_collected_info
        reasoning_state["ready_for_generation"] = True
        reasoning_state["story_framework"] = "测试RPG故事框架..."
        reasoning_state["requirement_analysis_report"] = "模拟的需求分析报告..."

        # 更新agent的状态
        agent_service.reasoning_state = reasoning_state
        agent_service.collected_info = mock_collected_info

        # 模拟Stage1完成的结果
        stage1_complete_result = {
            "response": "太好了！我已经收集到足够的信息。现在开始生成您的RPG教育游戏...",
            "ready_for_stage2": True,
            "stage": "stage1_complete",
            "requirement_id": reasoning_state["requirement_id"],
            "final_requirements": mock_collected_info,
            "collected_info": mock_collected_info,
            "analysis_report": "模拟的需求分析报告...",
            "story_framework": "测试RPG故事框架...",
            "level_details": {},
            "storyboards_data": {},
            "level_generation_status": "pending",
            "action": "stage1_completed"
        }

        print("模拟的Stage1完成数据创建成功")

        # 3. 触发关卡生成（这是stage1_complete之后的关键步骤）
        print("\n3. 触发关卡生成流程...")

        # 模拟用户发送一个触发生成的请求（空输入通常会触发生成）
        print("模拟用户输入空字符串来触发关卡生成...")
        generation_result = await agent_service.process_request("")

        if generation_result:
            print(f"生成阶段: {generation_result.get('stage', 'unknown')}")
            print(f"Level生成状态: {generation_result.get('level_generation_status', 'unknown')}")
            print(f"Action: {generation_result.get('action', 'unknown')}")

            # 检查是否完成了所有关卡生成
            if generation_result.get('stage') == 'all_levels_complete':
                print("*** 所有关卡生成完成! ***")
                stage1_complete_result = generation_result
            elif generation_result.get('level_generation_status') == 'completed':
                print("*** 关卡生成完成! ***")
                stage1_complete_result = generation_result
            else:
                print(f"关卡生成状态: {generation_result.get('level_generation_status', 'pending')}")
                # 可能需要多次调用来完成生成
                max_attempts = 5
                for attempt in range(max_attempts):
                    print(f"\n尝试第 {attempt + 1} 次获取生成结果...")
                    retry_result = await agent_service.process_request("")

                    if retry_result and retry_result.get('level_generation_status') == 'completed':
                        print("*** 关卡生成完成! ***")
                        stage1_complete_result = retry_result
                        break
                    elif retry_result:
                        print(f"状态: {retry_result.get('level_generation_status', 'pending')}")
                    else:
                        print("未收到响应")
        else:
            print("警告: 生成请求未收到响应")

        print("\n4. 验证Stage1完成数据...")
        requirement_id = stage1_complete_result.get('requirement_id')
        collected_info = stage1_complete_result.get('collected_info', {})
        analysis_report = stage1_complete_result.get('analysis_report')
        story_framework = stage1_complete_result.get('story_framework')

        print(f"Requirement ID: {requirement_id}")
        print(f"收集信息字段数: {len(collected_info)}")
        print(f"分析报告存在: {bool(analysis_report)}")
        print(f"故事框架存在: {bool(story_framework)}")

        if not requirement_id:
            print("错误: requirement_id缺失")
            return False

        # 5. 验证数据库保存
        print("\n5. 验证数据库中的需求数据...")
        db_result = db_client.get_requirement(requirement_id)
        if db_result.get('success'):
            print("数据库中找到需求数据")
            saved_data = db_result.get('data', {})
            print(f"保存的收集信息字段数: {len(saved_data.get('collected_info', {}))}")
        else:
            print(f"警告: 数据库中未找到需求数据: {db_result.get('error')}")

        # 6. 测试故事板生成API调用
        print("\n6. 测试故事板生成...")

        # 模拟前端调用generate_complete_storyboards API
        print(f"模拟API调用: /generate_complete_storyboards")
        print(f"参数: requirement_id = {requirement_id}")

        # 检查故事数据是否已存在
        story_id = f"story_{requirement_id}"
        story_result = db_client.get_story(story_id)

        if story_result.get('success'):
            print("数据库中找到完整故事数据")
            story_data = story_result['data']

            # 验证故事数据结构
            storyboards_data = story_data.get('storyboards_data', {})
            storyboards_list = storyboards_data.get('storyboards', [])

            print(f"故事标题: {story_data.get('story_title', '未知')}")
            print(f"故事板数量: {len(storyboards_list)}")

            # 检查每个故事板的数据完整性
            for i, storyboard in enumerate(storyboards_list[:3], 1):
                print(f"\n检查故事板 {i}:")
                print(f"  场景名称: {storyboard.get('stage_name')}")
                print(f"  故事板数据: {bool(storyboard.get('storyboard'))}")

                # 检查新合并后的数据结构
                sb_data = storyboard.get('storyboard', {})
                print(f"  分镜基础信息: {bool(sb_data.get('分镜基础信息'))}")
                print(f"  人物档案: {bool(sb_data.get('人物档案'))}")
                print(f"  人物对话: {bool(sb_data.get('人物对话'))}")
                print(f"  图片提示词: {bool(sb_data.get('图片提示词'))}")
                print(f"  剧本: {bool(sb_data.get('剧本'))}")

                # 检查人物档案结构
                characters = sb_data.get('人物档案', {})
                if characters:
                    print(f"  主角数据: {bool(characters.get('主角'))}")
                    print(f"  NPC数据: {bool(characters.get('NPC'))}")

                    if characters.get('主角'):
                        print(f"    主角名称: {characters['主角'].get('角色名', '未知')}")
                    if characters.get('NPC'):
                        print(f"    NPC名称: {characters['NPC'].get('角色名', '未知')}")

                # 检查对话数据
                dialogue = sb_data.get('人物对话', [])
                if isinstance(dialogue, list):
                    print(f"  对话轮次: {len(dialogue)}")
        else:
            print("数据库中未找到完整故事数据")
            print("这表明故事生成尚未完成或出现问题")

        # 7. 测试前端数据映射
        print("\n7. 测试前端数据映射...")
        if story_result.get('success'):
            story_data = story_result['data']

            # 模拟前端的数据解析逻辑
            response_data = {
                "requirement_id": requirement_id,
                "story_data": story_data,
                "storyboards_data": story_data.get("storyboards_data", {}),
                "story_framework": story_data.get("story_framework", ""),
                "from_database": True
            }

            # 模拟前端节点数据构建
            storyboards_data = response_data.get("storyboards_data", {})
            storyboards_list = storyboards_data.get("storyboards", [])

            print(f"前端接收到故事板数量: {len(storyboards_list)}")

            # 测试第一个节点的数据映射
            if storyboards_list:
                first_storyboard = storyboards_list[0]

                # 模拟CustomStoryboardNode的数据映射
                node_data = {
                    "sceneName": first_storyboard.get("stage_name"),
                    "stageId": first_storyboard.get("stage_id"),
                    "characters": first_storyboard.get("storyboard", {}).get("人物档案"),
                    "dialogue": first_storyboard.get("storyboard", {}).get("人物对话"),
                    "script": first_storyboard.get("storyboard", {}).get("剧本"),
                    "imagePrompt": first_storyboard.get("storyboard", {}).get("图片提示词", ""),
                    "sceneInfo": first_storyboard.get("storyboard", {}).get("分镜基础信息"),
                }

                print("节点数据映射测试:")
                print(f"  场景名称: {node_data['sceneName']}")
                print(f"  角色数据存在: {bool(node_data['characters'])}")

                # 测试可能导致TypeError的访问
                try:
                    if node_data['characters']:
                        main_char = node_data['characters'].get('主角')
                        npc_char = node_data['characters'].get('NPC')
                        print(f"  主角访问成功: {bool(main_char)}")
                        print(f"  NPC访问成功: {bool(npc_char)}")

                        if main_char:
                            print(f"    主角名称: {main_char.get('角色名')}")
                        if npc_char:
                            print(f"    NPC名称: {npc_char.get('角色名')}")
                    else:
                        print("  警告: 角色数据为空，这可能导致前端TypeError")

                except Exception as e:
                    print(f"  错误: 前端数据访问失败: {e}")
                    return False

        print("\n8. 流程测试总结...")
        print("Stage1 Complete流程测试完成")

        # 检查关键指标
        success_indicators = [
            ("Stage1完成", bool(stage1_complete_result)),
            ("Requirement ID存在", bool(requirement_id)),
            ("数据库需求保存", db_result.get('success', False)),
            ("故事数据存在", story_result.get('success', False)),
            ("前端数据映射", len(storyboards_list) > 0 if story_result.get('success') else False),
        ]

        print("\n成功指标:")
        all_success = True
        for indicator, status in success_indicators:
            status_text = "通过" if status else "失败"
            print(f"  {indicator}: {status_text}")
            if not status:
                all_success = False

        return all_success

    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("Stage1 Complete流程完整性测试")
    print("模拟Stage1已完成状态，测试后续关卡生成和故事板处理的完整流程")
    print()

    # 运行异步测试
    success = asyncio.run(test_complete_flow())

    print("\n" + "=" * 60)
    if success:
        print("测试结果: 通过")
        print("Stage1 Complete流程运行正常，无报错")
    else:
        print("测试结果: 失败")
        print("发现问题，需要进一步检查")
    print("=" * 60)

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)