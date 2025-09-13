#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
from agent_service import create_agent_service

class InteractiveChat:
    def __init__(self):
        """初始化交互式对话"""
        self.agent = create_agent_service()
        self.session_active = False
        
    def print_welcome(self):
        """打印欢迎信息"""
        print("\n" + "=" * 60)
        print("🎮 教育游戏设计助手 - 交互式对话")
        print("=" * 60)
        print("💡 输入命令:")
        print("   /start  - 开始新对话")
        print("   /status - 查看当前状态") 
        print("   /reset  - 重置会话")
        print("   /quit   - 退出程序")
        print("   其他    - 与助手对话")
        print("=" * 60)
        print()

    async def start_session(self):
        """开始新的对话会话"""
        if self.session_active:
            print("⚠️ 会话已经激活，使用 /reset 重新开始")
            return
            
        try:
            result = self.agent.start_conversation()
            print(f"🤖 {result['message']}")
            self.session_active = True
            print("\n💬 请开始与助手对话...")
        except Exception as e:
            print(f"❌ 启动会话失败: {e}")

    async def process_user_input(self, user_input: str):
        """处理用户输入"""
        if not self.session_active:
            print("⚠️ 请先使用 /start 开始对话")
            return
            
        try:
            print("🤔 助手思考中...")
            result = await self.agent.process_request(user_input)
            
            print(f"\n🤖 {result['response']}")
            
            # 显示进度信息
            if result.get('completion_rate'):
                progress = result['completion_rate'] * 100
                print(f"📊 当前进度: {progress:.1f}%")
                
            if result.get('stage'):
                stage_names = {
                    'stage1_collecting': '信息收集中',
                    'stage1_complete': '需求收集完成',
                    'stage2_generation': '内容生成中'
                }
                stage_display = stage_names.get(result['stage'], result['stage'])
                print(f"🎯 当前阶段: {stage_display}")
            
            # 如果完成了Stage1
            if result.get('next_action') == 'generate_content':
                print("\n🎉 信息收集完成！可以使用 /status 查看收集到的信息")
                
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")

    def show_status(self):
        """显示当前状态"""
        if not self.session_active:
            print("⚠️ 当前没有激活的会话")
            return
            
        try:
            status = self.agent.get_session_status()
            
            print("\n" + "=" * 50)
            print("📋 当前状态")
            print("=" * 50)
            
            if status['status'] == 'active':
                print(f"🎯 当前阶段: {status['current_stage']}")
                print(f"📊 完成度: {status['completion_rate']*100:.1f}%")
                
                if status['missing_fields']:
                    print(f"❓ 还需要: {', '.join(status['missing_fields'])}")
                
                print("\n📝 已收集信息:")
                collected = status['collected_info']
                for key, value in collected.items():
                    if value:
                        display_key = {
                            'subject': '学科',
                            'grade': '年级', 
                            'knowledge_points': '知识点',
                            'teaching_goals': '教学目标',
                            'teaching_difficulties': '教学难点',
                            'game_style': '游戏风格',
                            'character_design': '角色设计',
                            'world_setting': '世界背景',
                            'plot_requirements': '情节需求',
                            'interaction_requirements': '互动方式'
                        }.get(key, key)
                        
                        if isinstance(value, list):
                            value_str = '、'.join(value)
                        else:
                            value_str = str(value)
                        print(f"  ✅ {display_key}: {value_str}")
            else:
                print(f"状态: {status['status']}")
                
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ 获取状态失败: {e}")

    def reset_session(self):
        """重置会话"""
        try:
            result = self.agent.reset_session()
            print(f"🔄 {result['message']}")
            self.session_active = True
        except Exception as e:
            print(f"❌ 重置失败: {e}")

    async def run(self):
        """运行主循环"""
        self.print_welcome()
        
        print("👋 欢迎！输入 /start 开始对话")
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n💬 您: ").strip()
                
                if not user_input:
                    continue
                    
                # 处理命令
                if user_input == '/quit':
                    print("👋 再见！")
                    break
                elif user_input == '/start':
                    await self.start_session()
                elif user_input == '/status':
                    self.show_status()
                elif user_input == '/reset':
                    self.reset_session()
                elif user_input.startswith('/'):
                    print("❓ 未知命令，输入 /quit 退出")
                else:
                    # 正常对话
                    await self.process_user_input(user_input)
                    
            except KeyboardInterrupt:
                print("\n👋 程序被中断，再见！")
                break
            except EOFError:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")

async def main():
    """主函数"""
    chat = InteractiveChat()
    await chat.run()

if __name__ == "__main__":
    # 运行交互式对话
    asyncio.run(main())