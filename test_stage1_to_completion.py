#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：从Stage1 Complete状态运行到完全结束
获取 analysis_report, story_framework, education_assessment 并保存到JSON文件
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 添加backend路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from agent_service import AgentService

async def test_stage1_to_completion():
    """从Stage1完成状态运行到完全结束，获取目标数据"""

    print("=" * 60)
    print("Stage1 Complete到完全结束测试")
    print("=" * 60)

    try:
        # 1. 初始化服务
        print("\n1. 初始化AgentService...")
        agent_service = AgentService()

        # 2. 创建模拟的Stage1完成数据
        print("\n2. 创建模拟Stage1数据...")
        mock_collected_info = {
            "subject": "数学",
            "grade": "三年级",
            "knowledge_points": ["10以内加减法", "进位退位计算", "数学应用题"],
            "teaching_goals": ["掌握10以内加减法运算规律", "提高进位退位计算准确性", "培养数学应用能力"],
            "teaching_difficulties": ["进位退位时容易出错", "计算速度慢", "应用题理解困难"],
            "game_style": "RPG冒险风格",
            "character_design": "勇敢的小数学家主角",
            "world_setting": "神秘的数字王国",
            "plot_requirements": "通过解决数学难题拯救王国",
            "interaction_requirements": "智慧导师NPC引导探索"
        }

        # 3. 初始化推理状态为Stage1完成状态
        print("\n3. 设置推理状态为Stage1完成...")
        reasoning_state = agent_service.reasoning_graph.initialize_reasoning_state(
            session_id=agent_service.session_id,
            user_id=agent_service.user_id,
            collected_info=mock_collected_info
        )

        # 设置为需要进入完成流程的状态
        reasoning_state["collected_info"] = mock_collected_info
        reasoning_state["stage1_complete"] = True  # 这很关键
        reasoning_state["sufficiency_score"] = {  # 添加充足性评分
            "基础信息充足性": 85,
            "教学信息充足性": 80,
            "游戏设定充足性": 88,
            "情节设定充足性": 82
        }
        reasoning_state["sufficiency_passed"] = True  # 通过充足性检查
        reasoning_state["fitness_passed"] = True     # 通过适宜性检查
        reasoning_state["fitness_concerns"] = []     # 没有适宜性问题

        # 更新agent状态
        agent_service.reasoning_state = reasoning_state
        agent_service.collected_info = mock_collected_info

        print(f"Requirement ID: {reasoning_state['requirement_id']}")

        # 4. 触发生成流程（通过空输入）
        print("\n4. 触发生成流程...")
        generation_result = await agent_service.process_request("")

        if generation_result:
            print(f"初次生成结果:")
            print(f"  阶段: {generation_result.get('stage', 'unknown')}")
            print(f"  关卡生成状态: {generation_result.get('level_generation_status', 'unknown')}")
            print(f"  Action: {generation_result.get('action', 'unknown')}")

        # 5. 持续检查直到完成
        print("\n5. 等待生成完成...")
        max_attempts = 10
        final_result = generation_result

        for attempt in range(max_attempts):
            if final_result and final_result.get('level_generation_status') == 'completed':
                print("*** 生成完成! ***")
                break

            print(f"  尝试 {attempt + 1}/{max_attempts}...")
            retry_result = await agent_service.process_request("")

            if retry_result:
                print(f"    状态: {retry_result.get('level_generation_status', 'pending')}")
                final_result = retry_result

            # 添加小延迟避免过快请求
            await asyncio.sleep(1)

        # 6. 提取目标数据
        print("\n6. 提取目标数据...")
        if not final_result:
            raise Exception("未能获取最终结果")

        # 调试：打印final_result的结构
        print(f"\n调试信息:")
        print(f"  final_result keys: {list(final_result.keys()) if final_result else 'None'}")
        if final_result:
            for key, value in final_result.items():
                print(f"    {key}: {type(value)} - {'存在' if value else '空'}")

        # 提取三个目标值
        analysis_report = final_result.get('analysis_report', '')
        story_framework = final_result.get('story_framework', '')
        education_assessment_report = final_result.get('education_assessment_report', {})

        print(f"Analysis Report: {'存在' if analysis_report else '空'}")
        print(f"Story Framework: {'存在' if story_framework else '空'}")
        print(f"Education Assessment: {'存在' if education_assessment_report else '空'}")

        # 7. 构建输出数据
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "test_info": {
                "requirement_id": reasoning_state['requirement_id'],
                "session_id": agent_service.session_id,
                "final_stage": final_result.get('stage', 'unknown'),
                "level_generation_status": final_result.get('level_generation_status', 'unknown')
            },
            "collected_info": mock_collected_info,
            "extracted_data": {
                "analysis_report": analysis_report,
                "story_framework": story_framework,
                "education_assessment_report": education_assessment_report
            },
            "additional_info": {
                "level_details_count": len(final_result.get('level_details', {})),
                "storyboards_data": final_result.get('storyboards_data', {}),
                "action": final_result.get('action', 'unknown')
            }
        }

        # 8. 保存到JSON文件
        output_filename = f"stage1_completion_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = os.path.join(os.getcwd(), output_filename)

        print(f"\n7. 保存结果到文件...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"结果已保存到: {output_path}")

        # 9. 显示摘要信息
        print(f"\n8. 数据摘要:")
        print(f"  Requirement ID: {output_data['test_info']['requirement_id']}")
        print(f"  最终阶段: {output_data['test_info']['final_stage']}")
        print(f"  关卡数量: {output_data['additional_info']['level_details_count']}")

        # 显示内容长度
        analysis_len = len(analysis_report) if analysis_report else 0
        framework_len = len(story_framework) if story_framework else 0
        assessment_keys = len(education_assessment_report) if isinstance(education_assessment_report, dict) else 0

        print(f"  Analysis Report长度: {analysis_len} 字符")
        print(f"  Story Framework长度: {framework_len} 字符")
        print(f"  Education Assessment字段数: {assessment_keys}")

        return True, output_path

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

        # 即使失败也尝试保存错误信息
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

        error_filename = f"stage1_completion_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        error_path = os.path.join(os.getcwd(), error_filename)

        with open(error_path, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)

        print(f"错误信息已保存到: {error_path}")
        return False, error_path

def main():
    """主函数"""
    print("Stage1 Complete到完全结束测试")
    print("目标：获取 analysis_report, story_framework, education_assessment")
    print()

    # 运行异步测试
    success, output_file = asyncio.run(test_stage1_to_completion())

    print("\n" + "=" * 60)
    if success:
        print("测试完成！")
        print(f"结果文件: {output_file}")
        print("\n请检查JSON文件中的以下字段:")
        print("- extracted_data.analysis_report")
        print("- extracted_data.story_framework")
        print("- extracted_data.education_assessment_report")
    else:
        print("测试失败")
        print(f"错误文件: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()