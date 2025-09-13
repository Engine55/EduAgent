#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from backend.prompt_templates import PromptTemplates

# 加载环境变量
load_dotenv()

async def test_llm_fitness():
    """测试LLM fitness check功能"""
    
    print("🧪 开始测试LLM fitness check...")
    
    # 初始化LLM
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        print("✅ LLM初始化成功")
    except Exception as e:
        print(f"❌ LLM初始化失败: {e}")
        return
    
    # 初始化PromptTemplates
    try:
        prompts = PromptTemplates()
        print("✅ PromptTemplates初始化成功")
    except Exception as e:
        print(f"❌ PromptTemplates初始化失败: {e}")
        return
    
    # 准备测试数据
    collected_info = {
        "subject": "数学",
        "grade": "三年级",
        "knowledge_points": ["10以内加法", "数字大小比较"],
        "teaching_goals": ["提高计算准确性", "培养数学思维"],
        "teaching_difficulties": ["进位加法容易出错", "专注力不够"],
        "game_style": "魔法冒险",
        "character_design": "小魔法师",
        "world_setting": "魔法森林",
        "plot_requirements": ["寻找魔法宝物的旅程", "解救被困的小动物"],
        "interaction_requirements": ["选择题答题", "获得虚拟奖励"]
    }
    
    conversation_context = """用户: 我想为三年级学生做一个数学游戏
助手: 好的！请告诉我更多详情...
用户: 重点是10以内的加法，很多学生容易算错
助手: 明白了，那游戏风格有什么偏好吗？
用户: 想做成魔法冒险主题的"""
    
    def format_collected_info(collected_info):
        """格式化收集的信息"""
        formatted_parts = []
        
        # 基础信息
        if any([collected_info.get("subject"), collected_info.get("grade"), collected_info.get("knowledge_points")]):
            formatted_parts.append("【基础信息】")
            if collected_info.get("subject"):
                formatted_parts.append(f"  学科: {collected_info['subject']}")
            if collected_info.get("grade"):
                formatted_parts.append(f"  年级: {collected_info['grade']}")
            if collected_info.get("knowledge_points"):
                points = collected_info['knowledge_points']
                if isinstance(points, list):
                    points = "、".join(points)
                formatted_parts.append(f"  知识点: {points}")
        
        # 教学信息
        if any([collected_info.get("teaching_goals"), collected_info.get("teaching_difficulties")]):
            formatted_parts.append("\n【教学信息】")
            if collected_info.get("teaching_goals"):
                goals = collected_info['teaching_goals']
                if isinstance(goals, list):
                    goals = "、".join(goals)
                formatted_parts.append(f"  教学目标: {goals}")
            if collected_info.get("teaching_difficulties"):
                difficulties = collected_info['teaching_difficulties']
                if isinstance(difficulties, list):
                    difficulties = "、".join(difficulties)
                formatted_parts.append(f"  教学难点: {difficulties}")
        
        # 游戏设定
        if any([collected_info.get("game_style"), collected_info.get("character_design"), collected_info.get("world_setting")]):
            formatted_parts.append("\n【游戏设定】")
            if collected_info.get("game_style"):
                formatted_parts.append(f"  游戏风格: {collected_info['game_style']}")
            if collected_info.get("character_design"):
                formatted_parts.append(f"  角色设计: {collected_info['character_design']}")
            if collected_info.get("world_setting"):
                formatted_parts.append(f"  世界背景: {collected_info['world_setting']}")
        
        # 情节设定
        if any([collected_info.get("plot_requirements"), collected_info.get("interaction_requirements")]):
            formatted_parts.append("\n【情节设定】")
            if collected_info.get("plot_requirements"):
                plots = collected_info['plot_requirements']
                if isinstance(plots, list):
                    plots = "、".join(plots)
                formatted_parts.append(f"  情节需求: {plots}")
            if collected_info.get("interaction_requirements"):
                interactions = collected_info['interaction_requirements']
                if isinstance(interactions, list):
                    interactions = "、".join(interactions)
                formatted_parts.append(f"  互动方式: {interactions}")
        
        return "\n".join(formatted_parts) if formatted_parts else "暂无详细信息"
    
    def extract_json_from_markdown(content):
        """从markdown代码块中提取JSON内容"""
        content = content.strip()
        if content.startswith("```json") and content.endswith("```"):
            lines = content.split('\n')
            json_lines = lines[1:-1]
            return '\n'.join(json_lines)
        elif content.startswith("```") and content.endswith("```"):
            lines = content.split('\n')
            json_lines = lines[1:-1]
            return '\n'.join(json_lines)
        else:
            return content
    
    # 测试1: 获取prompt模板
    print("\n📝 测试1: 获取fitness check prompt模板...")
    try:
        prompt_template = prompts.get_fitness_check_prompt()
        print("✅ 获取prompt模板成功")
        print(f"模板输入变量: {prompt_template.input_variables}")
    except Exception as e:
        print(f"❌ 获取prompt模板失败: {e}")
        return
    
    # 测试2: 格式化prompt
    print("\n📝 测试2: 格式化prompt...")
    try:
        formatted_info = format_collected_info(collected_info)
        print("格式化信息预览:")
        print(formatted_info[:200] + "..." if len(formatted_info) > 200 else formatted_info)
        
        fitness_prompt = prompt_template.format(
            collected_info=formatted_info,
            conversation_context=conversation_context
        )
        print("✅ 格式化prompt成功")
        print(f"Prompt长度: {len(fitness_prompt)} 字符")
        print("Prompt开头:")
        print(fitness_prompt[:300] + "..." if len(fitness_prompt) > 300 else fitness_prompt)
    except Exception as e:
        print(f"❌ 格式化prompt失败: {e}")
        return
    
    # 测试3: 调用LLM (使用apredict)
    print("\n🤖 测试3: 调用LLM (使用apredict方法)...")
    try:
        response = await llm.apredict(fitness_prompt)
        print("✅ LLM调用成功 (apredict)")
        print(f"响应类型: {type(response)}")
        print(f"响应长度: {len(str(response))} 字符")
        print("响应内容:")
        print(response)
        
        # 尝试解析JSON
        try:
            json_content = extract_json_from_markdown(str(response))
            result = json.loads(json_content)
            print("✅ JSON解析成功")
            print("解析结果键:")
            for key in result.keys():
                print(f"  - {key}: {type(result[key])}")
            
            # 检查关键字段
            if "overall_fitness" in result:
                print(f"overall_fitness值: {result['overall_fitness']}")
            if "concerns" in result:
                print(f"concerns数量: {len(result['concerns'])}")
        except json.JSONDecodeError as je:
            print(f"❌ JSON解析失败: {je}")
            print(f"提取的JSON内容: {json_content[:500]}")
            
    except Exception as e:
        print(f"❌ LLM调用失败 (apredict): {e}")
    
    # 测试4: 调用LLM (使用ainvoke)
    print("\n🤖 测试4: 调用LLM (使用ainvoke方法)...")
    try:
        response = await llm.ainvoke([{"role": "user", "content": fitness_prompt}])
        print("✅ LLM调用成功 (ainvoke)")
        print(f"响应类型: {type(response)}")
        
        # 检查content属性
        if hasattr(response, 'content'):
            content = response.content
            print(f"content长度: {len(str(content))} 字符")
            print("content内容:")
            print(content)
            
            # 尝试解析JSON
            try:
                json_content = extract_json_from_markdown(str(content))
                result = json.loads(json_content)
                print("✅ JSON解析成功")
                print("解析结果键:")
                for key in result.keys():
                    print(f"  - {key}: {type(result[key])}")
                
                # 检查关键字段
                if "overall_fitness" in result:
                    print(f"overall_fitness值: {result['overall_fitness']}")
                if "concerns" in result:
                    print(f"concerns数量: {len(result['concerns'])}")
            except json.JSONDecodeError as je:
                print(f"❌ JSON解析失败: {je}")
                print(f"提取的JSON内容: {json_content[:500]}")
        else:
            print("❌ 响应对象没有content属性")
            
    except Exception as e:
        print(f"❌ LLM调用失败 (ainvoke): {e}")
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_llm_fitness())