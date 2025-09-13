import requests


def generate_rpg_music_with_prompt():
    api_key = "2V98aHDlehFLYlpa4ZJpdopUuPByi6iK8EtGviSJEqw"
    base_url = "https://soundtracks.loudly.com"

    headers = {
        "API-KEY": api_key,
        # 不设置Content-Type，让requests处理multipart/form-data
    }

    # 为"迷失的数字"场景创建描述性prompt
    form_data = {
        "prompt": "mysterious ambient forest music for educational puzzle game, gentle and curious atmosphere, suitable for children learning math, soft magical elements",
        "duration": 90,
        "test": True,
        "structure_id": 0  # Classic结构
    }

    print(f"生成教育RPG音乐...")
    print(f"Prompt: {form_data['prompt']}")

    try:
        response = requests.post(
            f"{base_url}/api/ai/prompt/songs",
            headers=headers,
            data=form_data
        )

        print(f"API状态: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("音乐生成成功!")
            print(f"标题: {result.get('title')}")
            print(f"时长: {result.get('duration')}ms ({result.get('duration') // 1000}秒)")
            print(f"音频文件: {result.get('music_file_path')}")
            return result
        else:
            print(f"失败响应: {response.text}")

    except Exception as e:
        print(f"请求异常: {e}")


if __name__ == "__main__":
    generate_rpg_music_with_prompt()