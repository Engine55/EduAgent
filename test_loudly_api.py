import requests
import json
import time
import base64
import os
from datetime import datetime


class StabilityAudioGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.stability.ai/v2beta/stable-audio"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def generate_audio(self, prompt, duration=30, output_format="mp3"):
        """
        生成音频

        Args:
            prompt (str): 音频描述提示词
            duration (int): 音频长度（秒），最大180秒
            output_format (str): 输出格式 "mp3" 或 "wav"

        Returns:
            dict: 包含任务ID和状态的响应
        """
        url = f"{self.base_url}/generate"

        payload = {
            "prompt": prompt,
            "duration": duration,
            "output_format": output_format
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"错误详情: {e.response.text}")
            return None

    def check_generation_status(self, generation_id):
        """检查生成状态"""
        url = f"{self.base_url}/generate/{generation_id}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"状态检查失败: {e}")
            return None

    def download_audio(self, result, filename=None):
        """下载生成的音频"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_audio_{timestamp}.mp3"

        try:
            if 'audio' in result:
                # 如果返回的是base64编码的音频
                audio_data = base64.b64decode(result['audio'])
                with open(filename, 'wb') as f:
                    f.write(audio_data)
                print(f"音频已保存为: {filename}")
                return filename
            elif 'url' in result:
                # 如果返回的是下载链接
                audio_response = requests.get(result['url'])
                audio_response.raise_for_status()
                with open(filename, 'wb') as f:
                    f.write(audio_response.content)
                print(f"音频已保存为: {filename}")
                return filename
            else:
                print("未找到音频数据")
                return None
        except Exception as e:
            print(f"下载失败: {e}")
            return None

    def generate_and_wait(self, prompt, duration=30, output_format="mp3", filename=None, max_wait=300):
        """
        生成音频并等待完成

        Args:
            prompt (str): 音频描述
            duration (int): 时长
            output_format (str): 格式
            filename (str): 输出文件名
            max_wait (int): 最大等待时间（秒）
        """
        print(f"开始生成音频...")
        print(f"提示词: {prompt}")
        print(f"时长: {duration}秒")

        # 开始生成
        result = self.generate_audio(prompt, duration, output_format)
        if not result:
            return None

        generation_id = result.get('id')
        if not generation_id:
            print("未获取到生成ID")
            return None

        print(f"生成ID: {generation_id}")
        print("等待生成完成...")

        # 轮询检查状态
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status_result = self.check_generation_status(generation_id)
            if not status_result:
                time.sleep(5)
                continue

            status = status_result.get('status', '').lower()
            print(f"当前状态: {status}")

            if status == 'complete':
                print("生成完成！开始下载...")
                return self.download_audio(status_result, filename)
            elif status == 'failed':
                print("生成失败")
                if 'error' in status_result:
                    print(f"错误信息: {status_result['error']}")
                return None
            elif status in ['in_progress', 'processing', 'queued']:
                time.sleep(5)
                continue
            else:
                print(f"未知状态: {status}")
                time.sleep(5)

        print("等待超时")
        return None


def main():
    # 在这里填入你的API密钥
    API_KEY = "sk-8x3ho8O0aRY30RTTB0dtndqncJ8utoLCKkuxF98O2Y3alAib"  # 替换为你的实际API密钥

    if API_KEY == "sk-your-api-key-here":
        print("请先设置你的API密钥！")
        print("1. 访问 https://platform.stability.ai/")
        print("2. 登录并获取API密钥")
        print("3. 将API_KEY变量替换为你的实际密钥")
        return

    # 创建生成器实例
    generator = StabilityAudioGenerator(API_KEY)

    # 示例提示词
    prompts = [
        "A peaceful piano melody with soft ambient sounds, perfect for relaxation",
        "Upbeat electronic dance music with synthesizers and strong beat",
        "Acoustic guitar folk song with a warm, nostalgic feeling",
        "Dramatic cinematic orchestral music with strings and brass",
        "Lo-fi hip hop beats with vinyl crackle and mellow vibes"
    ] 

    print("=== Stability AI 音频生成器 ===\n")

    while True:
        print("选择操作:")
        print("1. 使用预设提示词")
        print("2. 输入自定义提示词")
        print("3. 退出")

        choice = input("\n请选择 (1-3): ").strip()

        if choice == "1":
            print("\n预设提示词:")
            for i, prompt in enumerate(prompts, 1):
                print(f"{i}. {prompt}")

            try:
                prompt_choice = int(input(f"\n选择提示词 (1-{len(prompts)}): ")) - 1
                if 0 <= prompt_choice < len(prompts):
                    selected_prompt = prompts[prompt_choice]
                else:
                    print("无效选择")
                    continue
            except ValueError:
                print("请输入有效数字")
                continue

        elif choice == "2":
            selected_prompt = input("\n请输入你的音频描述 (英文): ").strip()
            if not selected_prompt:
                print("提示词不能为空")
                continue

        elif choice == "3":
            print("退出程序")
            break

        else:
            print("无效选择")
            continue

        # 设置参数
        try:
            duration = int(input("音频时长 (秒, 最大180, 默认30): ") or "30")
            duration = min(max(duration, 1), 180)  # 限制在1-180秒之间
        except ValueError:
            duration = 30

        output_format = input("输出格式 (mp3/wav, 默认mp3): ").strip().lower() or "mp3"
        if output_format not in ["mp3", "wav"]:
            output_format = "mp3"

        # 生成音频
        print("\n" + "=" * 50)
        result = generator.generate_and_wait(
            prompt=selected_prompt,
            duration=duration,
            output_format=output_format
        )

        if result:
            print(f"\n✅ 成功！音频文件: {result}")
        else:
            print("\n❌ 生成失败")

        print("\n" + "=" * 50)

        if input("\n继续生成？(y/n): ").strip().lower() != 'y':
            break


if __name__ == "__main__":
    main()