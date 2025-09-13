#!/usr/bin/env python3
"""
Stable Audio API 测试脚本
用于测试 Stability AI 的音频生成能力
"""

import requests
import json
import base64
import os
from datetime import datetime
from typing import Dict, Any, Optional

class StableAudioTester:
    def __init__(self, api_key: str):
        """
        初始化 Stable Audio API 测试器
        
        Args:
            api_key: Stability AI API key
        """
        self.api_key = 'sk-8x3ho8O0aRY30RTTB0dtndqncJ8utoLCKkuxF98O2Y3alAib'
        self.base_url = "https://api.stability.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
    def generate_audio(self, 
                      prompt: str, 
                      duration_seconds: int = 30,
                      cfg_scale: float = 7.0,
                      seed: Optional[int] = None) -> Dict[str, Any]:
        """
        生成音频
        
        Args:
            prompt: 音频描述提示词
            duration_seconds: 音频时长（秒）
            cfg_scale: CFG比例，控制遵循提示词的程度
            seed: 随机种子，用于可重复生成
            
        Returns:
            包含音频数据的字典
        """
        
        url = f"{self.base_url}/v2alpha/generation/audio"
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1.0
                }
            ],
            "duration_seconds": duration_seconds,
            "cfg_scale": cfg_scale
        }
        
        if seed is not None:
            payload["seed"] = seed
            
        print(f"🎵 开始生成音频...")
        print(f"📝 提示词: {prompt}")
        print(f"⏱️  时长: {duration_seconds}秒")
        print(f"🎛️  CFG Scale: {cfg_scale}")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ 音频生成成功!")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
                except:
                    print(f"响应内容: {e.response.text}")
            return {"error": str(e)}
    
    def save_audio(self, audio_data: str, filename: str) -> bool:
        """
        保存base64编码的音频到文件
        
        Args:
            audio_data: base64编码的音频数据
            filename: 保存的文件名（自动添加.mp3扩展名）
            
        Returns:
            是否保存成功
        """
        try:
            # 解码base64数据
            audio_bytes = base64.b64decode(audio_data)
            
            # 确保输出目录存在
            os.makedirs("generated_audio", exist_ok=True)
            
            # 确保文件名以.mp3结尾
            if not filename.endswith('.mp3'):
                filename = filename.replace('.wav', '.mp3')
                if not filename.endswith('.mp3'):
                    filename += '.mp3'
            
            # 保存文件
            filepath = os.path.join("generated_audio", filename)
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
                
            print(f"💾 音频已保存到: {filepath}")
            print(f"📁 完整路径: {os.path.abspath(filepath)}")
            return True
            
        except Exception as e:
            print(f"❌ 保存音频失败: {e}")
            return False
    
    def test_scene_music_generation(self):
        """测试场景背景音乐生成"""
        print("\n" + "="*60)
        print("🎮 测试场景背景音乐生成")
        print("="*60)
        
        test_scenes = [
            {
                "name": "magical_forest",
                "prompt": "magical forest background music, peaceful, mystical, orchestral, fantasy RPG game music, loop-friendly",
                "duration": 30
            },
            {
                "name": "battle_scene",
                "prompt": "epic battle music, intense, dramatic, orchestral, boss fight music, fast tempo",
                "duration": 20
            },
            {
                "name": "peaceful_village",
                "prompt": "peaceful village music, calm, relaxing, acoustic instruments, medieval fantasy, ambient",
                "duration": 25
            }
        ]
        
        for scene in test_scenes:
            print(f"\n🎬 测试场景: {scene['name']}")
            
            result = self.generate_audio(
                prompt=scene['prompt'],
                duration_seconds=scene['duration']
            )
            
            if "error" not in result and "audio" in result:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{scene['name']}_{timestamp}.mp3"
                self.save_audio(result["audio"], filename)
            else:
                print(f"❌ 场景 {scene['name']} 生成失败")
    
    def test_educational_audio(self):
        """测试教育场景音频生成"""
        print("\n" + "="*60)
        print("📚 测试教育场景音频生成")
        print("="*60)
        
        educational_prompts = [
            {
                "name": "math_adventure",
                "prompt": "upbeat math adventure music, curious, playful, educational game music, children friendly",
                "duration": 30
            },
            {
                "name": "puzzle_solving",
                "prompt": "puzzle solving background music, thinking music, concentration, soft instrumental",
                "duration": 20
            },
            {
                "name": "success_fanfare",
                "prompt": "success fanfare, victory music, congratulations, cheerful, short celebration music",
                "duration": 10
            }
        ]
        
        for prompt_data in educational_prompts:
            print(f"\n📖 测试教育音频: {prompt_data['name']}")
            
            result = self.generate_audio(
                prompt=prompt_data['prompt'],
                duration_seconds=prompt_data['duration']
            )
            
            if "error" not in result and "audio" in result:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"edu_{prompt_data['name']}_{timestamp}.mp3"
                self.save_audio(result["audio"], filename)
            else:
                print(f"❌ 教育音频 {prompt_data['name']} 生成失败")

def main():
    """主函数"""
    print("🎵 Stable Audio API 测试脚本")
    print("="*60)
    
    # 直接设置API密钥或从环境变量获取
    api_key = os.getenv("STABILITY_API_KEY")
    
    if not api_key:
        # 如果没有环境变量，可以直接在这里设置API密钥进行测试
        api_key = input("请输入你的 Stability AI API Key: ").strip()
        
        if not api_key:
            print("❌ API密钥不能为空")
            return
    
    # 创建测试器实例
    tester = StableAudioTester(api_key)
    
    # 执行测试
    try:
        # 测试场景音乐生成
        tester.test_scene_music_generation()
        
        # 测试教育音频生成
        tester.test_educational_audio()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("📁 生成的音频文件保存在 generated_audio/ 目录下")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()