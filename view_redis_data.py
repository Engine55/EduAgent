#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from upstash_redis import Redis
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def connect_redis():
    """连接到Upstash Redis"""
    try:
        redis = Redis(
            url=os.getenv("UPSTASH_REDIS_URL"),
            token=os.getenv("UPSTASH_REDIS_TOKEN")
        )
        return redis
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return None

def list_all_requirements(redis, user_id=None):
    """列出所有保存的需求数据"""
    user_filter = f" (用户ID: {user_id})" if user_id else ""
    print("\n" + "="*60)
    print(f"📋 教育游戏需求数据{user_filter}")
    print("="*60)
    
    try:
        # 获取所有eduagent相关的键
        pattern = "eduagent:requirements:requirement_*"
        keys = redis.keys(pattern)
        
        if not keys:
            print("❌ 没有找到任何保存的数据")
            return
        
        # 如果指定了user_id，过滤数据
        filtered_requirements = []
        for key in keys:
            data = redis.get(key)
            if data:
                requirement = json.loads(data)
                if user_id is None or requirement.get('user_id') == str(user_id):
                    filtered_requirements.append((key, requirement))
        
        if not filtered_requirements:
            print(f"❌ 没有找到用户ID为 {user_id} 的数据")
            return
            
        print(f"📊 找到 {len(filtered_requirements)} 条记录\n")
        
        for i, (key, requirement) in enumerate(filtered_requirements, 1):
            print(f"--- 记录 {i} ---")
            print_requirement_summary(requirement)
            print()
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")

def print_requirement_summary(requirement):
    """打印需求数据摘要"""
    print(f"🆔 ID: {requirement.get('id', 'N/A')}")
    print(f"👤 用户ID: {requirement.get('user_id', 'N/A')}")
    print(f"⏰ 时间: {requirement.get('timestamp', 'N/A')}")
    
    # 打印摘要信息
    summary = requirement.get('summary', {})
    print(f"📚 学科: {summary.get('subject', 'N/A')}")
    print(f"🎓 年级: {summary.get('grade', 'N/A')}")
    print(f"📖 知识点数量: {summary.get('knowledge_points_count', 0)}")
    print(f"✅ 状态: {summary.get('completion_status', 'N/A')}")

def print_detailed_requirement(redis, requirement_id=None):
    """打印详细的需求数据"""
    if not requirement_id:
        # 获取最新的一条记录
        keys = redis.keys("eduagent:requirements:requirement_*")
        if not keys:
            print("❌ 没有找到任何数据")
            return
        requirement_id = keys[0].split(":")[-1]  # 取键名的最后部分
    
    key = f"eduagent:requirements:{requirement_id}"
    data = redis.get(key)
    
    if not data:
        print(f"❌ 未找到ID为 {requirement_id} 的数据")
        return
    
    requirement = json.loads(data)
    collected_info = requirement.get('collected_info', {})
    
    print("\n" + "="*60)
    print("📋 详细需求信息")
    print("="*60)
    
    print(f"🆔 ID: {requirement.get('id')}")
    print(f"⏰ 创建时间: {requirement.get('timestamp')}")
    print()
    
    # 基础信息
    print("📚 基础信息:")
    print(f"  学科: {collected_info.get('subject', '未设置')}")
    print(f"  年级: {collected_info.get('grade', '未设置')}")
    knowledge_points = collected_info.get('knowledge_points', [])
    if knowledge_points:
        print(f"  知识点: {', '.join(knowledge_points)}")
    else:
        print(f"  知识点: 未设置")
    print()
    
    # 教学信息
    print("🎯 教学信息:")
    teaching_goals = collected_info.get('teaching_goals', [])
    if teaching_goals:
        print(f"  教学目标: {', '.join(teaching_goals)}")
    else:
        print(f"  教学目标: 未设置")
    
    teaching_difficulties = collected_info.get('teaching_difficulties', [])
    if teaching_difficulties:
        print(f"  教学难点: {', '.join(teaching_difficulties)}")
    else:
        print(f"  教学难点: 未设置")
    print()
    
    # 游戏风格
    print("🎮 游戏风格:")
    print(f"  游戏风格: {collected_info.get('game_style', '未设置')}")
    print(f"  角色设计: {collected_info.get('character_design', '未设置')}")
    print(f"  世界背景: {collected_info.get('world_setting', '未设置')}")
    print()
    
    # 场景信息
    print("🏞️ 场景信息:")
    scene_requirements = collected_info.get('scene_requirements', [])
    if scene_requirements:
        print(f"  场景需求: {', '.join(scene_requirements)}")
    else:
        print(f"  场景需求: 未设置")
    
    interaction_requirements = collected_info.get('interaction_requirements', [])
    if interaction_requirements:
        print(f"  互动方式: {', '.join(interaction_requirements)}")
    else:
        print(f"  互动方式: 未设置")
    print()
    
    # 元数据
    metadata = requirement.get('metadata', {})
    print("📊 统计信息:")
    print(f"  已收集字段数: {metadata.get('total_fields_collected', 0)}")
    print(f"  完成的阶段: {', '.join(metadata.get('stages_completed', []))}")

def print_daily_index(redis, date=None):
    """打印指定日期的索引"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    date_key = f"eduagent:requirements:index:{date}"
    requirement_ids = redis.smembers(date_key)
    
    print(f"\n📅 {date} 的需求记录:")
    if requirement_ids:
        print(f"共 {len(requirement_ids)} 条记录")
        for req_id in requirement_ids:
            print(f"  - {req_id}")
    else:
        print("  无记录")

def main():
    """主函数"""
    print("🔍 EduAgent Redis 数据查看器")
    
    redis = connect_redis()
    if not redis:
        return
    
    while True:
        print("\n" + "="*40)
        print("请选择操作:")
        print("1. 查看所有需求摘要")
        print("2. 查看最新需求详情")
        print("3. 查看指定需求详情")
        print("4. 查看今日索引")
        print("5. 查看指定日期索引")
        print("0. 退出")
        print("="*40)
        
        choice = input("请输入选择 (0-5): ").strip()
        
        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            list_all_requirements(redis)
        elif choice == "2":
            print_detailed_requirement(redis)
        elif choice == "3":
            req_id = input("请输入需求ID: ").strip()
            print_detailed_requirement(redis, req_id)
        elif choice == "4":
            print_daily_index(redis)
        elif choice == "5":
            date = input("请输入日期 (YYYY-MM-DD): ").strip()
            print_daily_index(redis, date)
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main()