#!/usr/bin/env python3
"""
简单的LLM调用测试，绕过reasoning_graph的复杂逻辑
"""

import json
import asyncio
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def simple_llm_test():
    """简单测试LLM场景生成"""

    print("简单测试LLM场景生成...")

    # 初始化LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # 简化的prompt
    simple_prompt = """请为一个三年级数学教育游戏生成第1关卡的场景设计。

故事背景：在魔法森林中，玩家扮演小勇士，通过10以内的加法计算解救被困的小动物。

请按照以下JSON格式生成内容：

{
  "分镜基础信息": {
    "分镜编号": "scene_1",
    "分镜标题": "关卡1-神秘森林入口",
    "场景氛围": "神秘探索",
    "关键事件": "发现被困的小兔子"
  },
  "图片生成提示词": {
    "视觉风格": "卡通动画风格",
    "场景描述": "魔法森林入口，阳光透过树叶",
    "角色描述": "可爱的小勇士和小兔子"
  },
  "剧本": {
    "旁白": "你来到了神秘的魔法森林入口",
    "情节描述": "发现了被数字锁困住的小兔子笼子",
    "互动设计": "通过加法计算开启笼子"
  }
}

请严格按照JSON格式回复，不要添加其他文字说明。"""

    try:
        print("调用LLM...")
        response = await llm.ainvoke([{"role": "user", "content": simple_prompt}])
        content = response.content

        print(f"LLM返回内容长度: {len(content)}")
        print("LLM返回内容:")
        print("=" * 50)
        print(content)
        print("=" * 50)

        # 尝试解析JSON
        print("尝试解析JSON...")
        try:
            # 如果内容包含代码块，提取JSON
            json_str = content
            if "```json" in content:
                start_idx = content.find("```json") + 7
                end_idx = content.find("```", start_idx)
                if end_idx != -1:
                    json_str = content[start_idx:end_idx].strip()
            elif "```" in content:
                start_idx = content.find("```") + 3
                end_idx = content.find("```", start_idx)
                if end_idx != -1:
                    json_str = content[start_idx:end_idx].strip()

            # 尝试解析
            parsed_json = json.loads(json_str)
            print("JSON解析成功!")
            print("顶级键:", list(parsed_json.keys()))

            # 保存到文件
            with open("test_scene_output.json", "w", encoding="utf-8") as f:
                json.dump(parsed_json, f, ensure_ascii=False, indent=2)
            print("结果已保存到 test_scene_output.json")

        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print("尝试查找错误...")

            # 保存原始内容用于分析
            with open("raw_llm_output.txt", "w", encoding="utf-8") as f:
                f.write(content)
            print("原始内容已保存到 raw_llm_output.txt")

    except Exception as e:
        print(f"LLM调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_llm_test())