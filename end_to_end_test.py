#!/usr/bin/env python3
"""
端到端完整测试脚本
从开始对话到生成完整故事板，验证数据保存
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加backend路径到sys.path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from agent_service import AgentService

async def end_to_end_test():
    """完整的端到端测试"""

    print("=" * 80)
    print("开始端到端完整测试")
    print("=" * 80)

    try:
        # 1. 初始化AgentService
        print("\n1. 初始化AgentService...")
        agent = AgentService()

        # 2. 开始对话
        print("\n2. 开始对话...")
        start_result = agent.start_conversation()
        print(f"开始对话结果: {start_result['status']}")
        print(f"欢迎消息: {start_result['message'][:100]}...")

        # 3. 模拟完整的用户输入序列
        user_inputs = [
            # 基础信息
            "我想为三年级学生设计一个数学游戏，主要教10以内的加法运算",

            # 教学目标和难点
            "教学目标是让学生熟练掌握10以内的加法，特别是进位加法比较困难",

            # 游戏风格和设定
            "我希望是RPG冒险风格，主角是可爱的小动物，背景设定在魔法森林",

            # 情节和交互需求
            "故事情节希望是闯关冒险模式，每关解救一个小动物，交互方式主要是点击选择"
        ]

        print(f"\n3. 开始对话交互，共{len(user_inputs)}轮...")

        final_result = None
        for i, user_input in enumerate(user_inputs, 1):
            print(f"\n--- 第{i}轮对话 ---")
            print(f"用户输入: {user_input}")

            # 处理用户输入
            result = await agent.process_request(user_input)

            print(f"处理状态: {result.get('action', '未知')}")
            print(f"当前阶段: {result.get('stage', '未知')}")
            print(f"完成度: {result.get('ready_for_stage2', False)}")

            if result.get('response'):
                print(f"助手回复: {result['response'][:150]}...")

            if result.get('error'):
                print(f"错误: {result['error']}")
                break

            # 检查是否完成Stage1
            if result.get('ready_for_stage2'):
                print("Stage1完成，准备生成内容!")
                final_result = result
                break

        if not final_result:
            print("Stage1未完成，测试失败")
            return

        # 4. 验证收集的信息
        print(f"\n4. 验证收集的信息...")
        collected_info = final_result.get('collected_info', {})
        requirement_id = final_result.get('requirement_id')

        print(f"需求ID: {requirement_id}")
        print("收集的信息:")
        for key, value in collected_info.items():
            if value:
                print(f"  {key}: {value}")

        # 5. 验证故事框架
        story_framework = final_result.get('story_framework')
        if story_framework:
            print(f"\n5. 故事框架生成成功:")
            print(f"故事框架长度: {len(story_framework)} 字符")
            print(f"故事框架片段: {story_framework[:200]}...")
        else:
            print("\n5. 故事框架未生成")

        # 6. 验证关卡详细内容
        level_details = final_result.get('level_details', {})
        storyboards_data = final_result.get('storyboards_data', {})

        print(f"\n6. 关卡内容验证:")
        print(f"关卡数量: {len(level_details)}")

        for level_key, level_data in level_details.items():
            print(f"  {level_key}:")
            print(f"    场景状态: {level_data.get('scenes_status', '未知')}")
            print(f"    角色状态: {level_data.get('characters_status', '未知')}")

            if level_data.get('scenes_script'):
                scenes_length = len(level_data['scenes_script'])
                print(f"    场景内容: {scenes_length} 字符")

            if level_data.get('characters_dialogue'):
                characters_length = len(level_data['characters_dialogue'])
                print(f"    角色内容: {characters_length} 字符")

        # 7. 验证前端格式数据
        print(f"\n7. 前端格式数据验证:")
        if storyboards_data:
            print(f"故事ID: {storyboards_data.get('story_id')}")
            print(f"故事标题: {storyboards_data.get('story_title')}")
            print(f"学科: {storyboards_data.get('subject')}")
            print(f"年级: {storyboards_data.get('grade')}")

            storyboards = storyboards_data.get('storyboards', [])
            print(f"故事板数量: {len(storyboards)}")

            for i, storyboard in enumerate(storyboards, 1):
                print(f"  故事板{i}: {storyboard.get('stage_name', '未知')}")
                generation_status = storyboard.get('generation_status', {})
                print(f"    生成状态: {generation_status}")
        else:
            print("❌ 前端格式数据未生成")

        # 8. 验证数据库保存
        print(f"\n8. 验证数据库保存...")
        if requirement_id:
            # 检查数据库中是否保存了数据
            try:
                from database_client import db_client

                if db_client:
                    # 尝试从数据库获取数据
                    saved_data = db_client.get_requirement(requirement_id)
                    if saved_data:
                        print("数据库保存成功")
                        print(f"保存的数据ID: {saved_data.get('id')}")
                        print(f"保存时间: {saved_data.get('timestamp')}")
                        print(f"用户ID: {saved_data.get('user_id')}")
                        print(f"状态: {saved_data.get('status')}")

                        # 验证保存的内容
                        saved_collected_info = saved_data.get('collected_info', {})
                        print(f"保存的信息项数: {len(saved_collected_info)}")
                    else:
                        print(f"数据库中未找到数据: {requirement_id}")
                else:
                    print("数据库客户端未初始化")
            except Exception as e:
                print(f"数据库验证失败: {e}")

        # 9. 保存测试结果到文件
        print(f"\n9. 保存测试结果...")
        test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_result_file = f"end_to_end_test_result_{test_timestamp}.json"

        test_result = {
            "test_timestamp": datetime.now().isoformat(),
            "requirement_id": requirement_id,
            "stage1_completed": final_result.get('ready_for_stage2', False),
            "collected_info": collected_info,
            "story_framework_length": len(story_framework) if story_framework else 0,
            "level_details_count": len(level_details),
            "storyboards_count": len(storyboards_data.get('storyboards', [])),
            "final_result": final_result
        }

        with open(test_result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)

        print(f"测试结果已保存到: {test_result_file}")

        # 10. 测试总结
        print(f"\n10. 测试总结:")
        print("=" * 60)

        success_count = 0
        total_checks = 0

        checks = [
            ("AgentService初始化", True),
            ("对话开始", start_result['status'] == 'session_started'),
            ("Stage1完成", final_result.get('ready_for_stage2', False)),
            ("信息收集", bool(collected_info)),
            ("需求ID生成", bool(requirement_id)),
            ("故事框架生成", bool(story_framework)),
            ("关卡内容生成", len(level_details) > 0),
            ("前端数据格式化", bool(storyboards_data))
        ]

        for check_name, check_result in checks:
            total_checks += 1
            if check_result:
                success_count += 1
                print(f"✅ {check_name}: 成功")
            else:
                print(f"❌ {check_name}: 失败")

        success_rate = (success_count / total_checks) * 100
        print(f"\n总体成功率: {success_count}/{total_checks} ({success_rate:.1f}%)")

        if success_rate >= 80:
            print("🎉 端到端测试基本成功!")
        else:
            print("⚠️ 端到端测试存在问题，需要进一步调试")

        return test_result

    except Exception as e:
        print(f"❌ 端到端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """主函数"""
    print("开始端到端完整测试...")
    result = await end_to_end_test()

    if result:
        print("\n测试完成！")
    else:
        print("\n测试失败！")

if __name__ == "__main__":
    asyncio.run(main())