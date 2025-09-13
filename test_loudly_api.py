import requests
import os
import time


def generate_and_download_music(prompt_text, filename_prefix, duration=60):
    """生成并下载指定风格的音乐"""
    api_key = "2V98aHDlehFLYlpa4ZJpdopUuPByi6iK8EtGviSJEqw"
    base_url = "https://soundtracks.loudly.com"

    headers = {"API-KEY": api_key}

    form_data = {
        "prompt": prompt_text,
        "duration": duration,
        "test": True,
        "structure_id": 0
    }

    try:
        print(f"\n🎵 生成音乐: {filename_prefix}")
        print(f"📝 Prompt: {prompt_text}")
        
        # 生成音乐
        response = requests.post(
            f"{base_url}/api/ai/prompt/songs",
            headers=headers,
            data=form_data
        )

        if response.status_code == 200:
            result = response.json()
            audio_url = result.get('music_file_path')

            if audio_url:
                # 下载为MP3到当前路径
                filename = f"{filename_prefix}.mp3"

                print(f"📥 下载音频: {audio_url}")
                audio_response = requests.get(audio_url)

                with open(filename, 'wb') as f:
                    f.write(audio_response.content)

                print(f"✅ 音乐已保存为: {filename}")
                print(f"📊 文件大小: {os.path.getsize(filename)} bytes")
                return filename
            else:
                print("❌ 未获得音频URL")
        else:
            print(f"❌ 生成失败: {response.text}")

    except Exception as e:
        print(f"❌ 错误: {e}")
    
    return None


def test_multiple_music_styles():
    """测试多种音乐风格"""
    
    # 定义多种教育RPG场景的音乐风格
    music_styles = [
        {
            "prompt": "mysterious ambient forest music for educational puzzle game, gentle and curious atmosphere, suitable for children learning",
            "filename": "forest_ambient",
            "description": "神秘森林环境音乐"
        },
        {
            "prompt": "epic adventure music for educational game, moderate intensity, inspiring and encouraging atmosphere, heroic theme",
            "filename": "epic_adventure", 
            "description": "史诗冒险音乐"
        },
        {
            "prompt": "calm peaceful background music for educational content, relaxing and focus-enhancing atmosphere, soft instrumental",
            "filename": "peaceful_study",
            "description": "平静学习音乐"
        },
        {
            "prompt": "mysterious cave exploration music, ambient and atmospheric, suitable for puzzle solving, dark and intriguing",
            "filename": "cave_mystery",
            "description": "神秘洞穴探索音乐"
        },
        {
            "prompt": "serene lakeside music with magical elements, peaceful and contemplative atmosphere for educational content, water sounds",
            "filename": "magical_lake",
            "description": "魔法湖泊音乐"
        },
        {
            "prompt": "upbeat electronic music for video game, energetic and motivating, suitable for action sequences in educational RPG",
            "filename": "electronic_action",
            "description": "电子动作音乐"
        },
        {
            "prompt": "whimsical fairy tale music, playful and magical, perfect for children's educational adventures, orchestral elements",
            "filename": "fairy_tale",
            "description": "童话风格音乐"
        },
        {
            "prompt": "medieval fantasy town music, acoustic instruments, bustling and warm atmosphere, suitable for RPG village scenes",
            "filename": "medieval_town",
            "description": "中世纪小镇音乐"
        }
    ]
    
    print("🎼 开始测试多种音乐风格")
    print("=" * 60)
    
    successful_files = []
    failed_styles = []
    
    for i, style in enumerate(music_styles, 1):
        print(f"\n📍 [{i}/{len(music_styles)}] {style['description']}")
        
        result = generate_and_download_music(
            style['prompt'], 
            style['filename'],
            duration=60  # 每首60秒
        )
        
        if result:
            successful_files.append(result)
        else:
            failed_styles.append(style['description'])
        
        # 避免API限制，等待2秒
        if i < len(music_styles):
            print("⏳ 等待2秒...")
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("=" * 60)
    
    if successful_files:
        print(f"✅ 成功生成 {len(successful_files)} 个音乐文件:")
        for file in successful_files:
            size = os.path.getsize(file)
            print(f"  📄 {file} ({size} bytes)")
    
    if failed_styles:
        print(f"\n❌ 失败的风格 ({len(failed_styles)}):")
        for style in failed_styles:
            print(f"  ❌ {style}")
    
    print(f"\n💡 你可以播放这些MP3文件来测试不同风格的音乐效果")


# 运行
if __name__ == "__main__":
    test_multiple_music_styles()