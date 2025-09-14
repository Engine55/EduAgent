#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试图片显示问题的脚本
检查数据库中的图片URL和前端显示逻辑
"""

import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database_client import db_client

def check_story_image_data():
    """检查数据库中故事的图片数据"""
    print("检查数据库中的图片数据")
    print("=" * 50)

    # 获取最新需求
    latest_req = db_client.get_latest_requirement()
    if not latest_req.get("success"):
        print("未找到需求数据")
        return

    requirement_id = latest_req["requirement_id"]
    story_id = f"story_{requirement_id}"

    print(f"需求ID: {requirement_id}")
    print(f"故事ID: {story_id}")

    # 获取故事数据
    story_result = db_client.get_story(story_id)
    if not story_result.get("success"):
        print("未找到故事数据")
        return

    story_data = story_result["data"]
    print("\n故事数据结构:")
    print(f"顶级字段: {list(story_data.keys())}")

    # 检查storyboards_data
    storyboards_data = story_data.get("storyboards_data", {})
    if storyboards_data:
        print(f"\nstoryboards_data字段: {list(storyboards_data.keys())}")

        storyboards = storyboards_data.get("storyboards", [])
        print(f"故事板数量: {len(storyboards)}")

        for i, storyboard in enumerate(storyboards[:2]):  # 只检查前2个
            print(f"\n故事板 {i+1}:")
            print(f"  字段: {list(storyboard.keys())}")

            # 检查图片相关字段
            image_fields = [k for k in storyboard.keys() if 'image' in k.lower()]
            print(f"  图片相关字段: {image_fields}")

            for field in image_fields:
                value = storyboard.get(field)
                if isinstance(value, str):
                    print(f"  {field}: {value[:100]}...")
                elif isinstance(value, dict):
                    print(f"  {field}: {list(value.keys())}")
                else:
                    print(f"  {field}: {type(value)}")

    else:
        print("没有找到storyboards_data字段")

def simulate_frontend_mapping():
    """模拟前端的数据映射逻辑"""
    print("\n" + "=" * 50)
    print("模拟前端数据映射")
    print("=" * 50)

    # 获取数据
    latest_req = db_client.get_latest_requirement()
    if not latest_req.get("success"):
        return

    requirement_id = latest_req["requirement_id"]
    story_id = f"story_{requirement_id}"
    story_result = db_client.get_story(story_id)

    if not story_result.get("success"):
        return

    # 模拟后端API返回的数据结构
    mock_api_response = {
        "success": True,
        "data": {
            "requirement_id": requirement_id,
            "story_data": story_result["data"],
            "storyboards_data": story_result["data"].get("storyboards_data", {}),
            "story_framework": story_result["data"].get("story_framework", ""),
            "from_database": True
        }
    }

    # 模拟前端处理逻辑
    result = mock_api_response
    story_data = result["data"]["story_data"] or {}
    storyboards_data = result["data"]["storyboards_data"] or story_data.get("storyboards_data", {})
    storyboards_list = storyboards_data.get("storyboards", [])

    print(f"解析结果:")
    print(f"  故事板数量: {len(storyboards_list)}")

    # 检查图片URL映射
    for i, storyboard in enumerate(storyboards_list[:2]):
        print(f"\n故事板 {i+1} 图片映射:")

        # 模拟前端映射逻辑
        generated_image_url = (
            storyboard.get("generated_image_data", {}).get("original_url") or
            storyboard.get("generated_image_url") or
            None
        )

        print(f"  generated_image_data: {bool(storyboard.get('generated_image_data'))}")
        if storyboard.get("generated_image_data"):
            image_data = storyboard["generated_image_data"]
            print(f"    keys: {list(image_data.keys()) if isinstance(image_data, dict) else 'not dict'}")
            if isinstance(image_data, dict) and "original_url" in image_data:
                print(f"    original_url: {image_data['original_url'][:100] if image_data['original_url'] else 'None'}")

        print(f"  generated_image_url: {storyboard.get('generated_image_url', 'None')}")
        print(f"  最终映射URL: {generated_image_url}")

def check_image_url_validity():
    """检查图片URL的有效性"""
    print("\n" + "=" * 50)
    print("检查图片URL有效性")
    print("=" * 50)

    latest_req = db_client.get_latest_requirement()
    if not latest_req.get("success"):
        return

    requirement_id = latest_req["requirement_id"]
    story_id = f"story_{requirement_id}"
    story_result = db_client.get_story(story_id)

    if not story_result.get("success"):
        return

    storyboards_data = story_result["data"].get("storyboards_data", {})
    storyboards = storyboards_data.get("storyboards", [])

    import requests

    for i, storyboard in enumerate(storyboards[:3]):
        print(f"\n检查故事板 {i+1}:")

        # 尝试所有可能的图片URL字段
        urls_to_check = []

        if storyboard.get("generated_image_data", {}).get("original_url"):
            urls_to_check.append(("generated_image_data.original_url",
                                storyboard["generated_image_data"]["original_url"]))

        if storyboard.get("generated_image_url"):
            urls_to_check.append(("generated_image_url", storyboard["generated_image_url"]))

        if not urls_to_check:
            print("  未找到图片URL")
            continue

        for field_name, url in urls_to_check:
            print(f"  检查 {field_name}:")
            print(f"    URL: {url[:80]}...")

            try:
                response = requests.head(url, timeout=10)
                print(f"    状态码: {response.status_code}")
                print(f"    Content-Type: {response.headers.get('Content-Type', 'Unknown')}")

                if response.status_code == 200:
                    print(f"    ✅ URL有效")
                else:
                    print(f"    ❌ URL无效")

            except Exception as e:
                print(f"    ❌ 请求失败: {str(e)[:100]}")

def main():
    """主函数"""
    print("图片显示问题诊断工具")
    print("这个脚本将检查:")
    print("1. 数据库中的图片数据结构")
    print("2. 前端数据映射逻辑")
    print("3. 图片URL的有效性")
    print()

    try:
        check_story_image_data()
        simulate_frontend_mapping()
        check_image_url_validity()
    except Exception as e:
        print(f"检查过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("诊断完成")
    print("如果发现问题，请检查:")
    print("1. 数据库中是否存储了正确的图片URL")
    print("2. 前端映射逻辑是否正确读取了URL字段")
    print("3. 图片URL是否可访问（可能需要代理或已过期）")

if __name__ == "__main__":
    main()