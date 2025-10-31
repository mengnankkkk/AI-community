#!/usr/bin/env python3
"""
交互式播客生成演示程序
提供简化的命令行交互界面，方便快速测试和演示
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Optional


class InteractivePodcastDemo:
    """交互式播客演示"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.output_dir = "output/interactive_demo"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def display_header(self):
        """显示标题"""
        print("\n" + "="*70)
        print("🎙️  AI虚拟播客工作室 - 交互式演示")
        print("="*70)
        print("📖 快速生成高质量播客，展示AI多模态内容生成能力")
        print("="*70 + "\n")
    
    def check_server(self) -> bool:
        """检查服务器状态"""
        print("🔍 检查服务器状态...")
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ 服务器运行正常\n")
                return True
            else:
                print("❌ 服务器响应异常\n")
                return False
        except:
            print("❌ 无法连接到服务器")
            print("💡 请先启动服务: python run_server.py\n")
            return False
    
    def show_preset_scenarios(self):
        """显示预设场景"""
        print("📋 预设场景:")
        print("  1. 科技前沿 - AI技术发展讨论")
        print("  2. 教育话题 - 在线教育的未来")
        print("  3. 健康生活 - 健康饮食与运动")
        print("  4. 商业洞察 - 创业与投资机遇")
        print("  5. 文化艺术 - 传统文化的现代传承")
        print("  6. 自定义 - 输入自己的话题\n")
    
    def get_preset_config(self, choice: str) -> Optional[Dict]:
        """获取预设配置"""
        configs = {
            "1": {
                "topic": "人工智能技术的突破与应用",
                "title": "AI前沿对话",
                "atmosphere": "serious_deep",
                "target_duration": "3分钟",
                "language_style": "formal",
                "characters": [
                    {
                        "name": "李博士",
                        "persona": "AI研究员，专注深度学习和大模型",
                        "core_viewpoint": "AI将成为第四次工业革命的核心驱动力",
                        "voice_description": "longwan_v2",
                        "tone_description": "专业、严谨、充满热情",
                        "language_habits": "善用类比，喜欢从原理层面解释问题"
                    },
                    {
                        "name": "王记者",
                        "persona": "科技媒体资深记者，关注AI伦理",
                        "core_viewpoint": "技术发展需要平衡效率与人文关怀",
                        "voice_description": "longxiaochun_v2",
                        "tone_description": "客观、理性、善于提问",
                        "language_habits": "提出犀利问题，引导深入思考"
                    }
                ],
                "background_materials": "近年来，大语言模型、计算机视觉、自动驾驶等AI技术取得突破性进展，正在深刻改变各行各业。"
            },
            "2": {
                "topic": "在线教育如何实现教育公平",
                "atmosphere": "relaxed_humorous",
                "target_duration": "3分钟",
                "language_style": "colloquial",
                "characters": [
                    {
                        "name": "张老师",
                        "persona": "资深教育工作者，30年教学经验",
                        "core_viewpoint": "技术是手段，教育的本质是关注每个学生成长",
                        "voice_description": "longyuan_v2",
                        "tone_description": "亲切、温和、富有耐心"
                    },
                    {
                        "name": "小林",
                        "persona": "在线教育平台创始人，90后创业者",
                        "core_viewpoint": "互联网可以让优质教育资源触达更多人",
                        "voice_description": "longxiaoyuan_v2",
                        "tone_description": "活力、热情、乐观向上"
                    }
                ]
            },
            "3": {
                "topic": "健康饮食与科学运动",
                "atmosphere": "warm_healing",
                "target_duration": "3分钟",
                "language_style": "colloquial",
                "characters": [
                    {
                        "name": "陈医生",
                        "persona": "营养学专家，倡导健康生活方式",
                        "core_viewpoint": "健康是幸福生活的基础",
                        "voice_description": "longxiaoxia_v2",
                        "tone_description": "温暖、专业、关怀备至"
                    },
                    {
                        "name": "李教练",
                        "persona": "健身教练，分享科学运动知识",
                        "core_viewpoint": "运动和饮食同等重要",
                        "voice_description": "longwan_v2",
                        "tone_description": "积极、鼓励、充满能量"
                    }
                ]
            },
            "4": {
                "topic": "创业者如何抓住时代机遇",
                "atmosphere": "serious_deep",
                "target_duration": "3分钟",
                "language_style": "formal",
                "characters": [
                    {
                        "name": "赵总",
                        "persona": "连续创业者，三次成功创业经验",
                        "core_viewpoint": "创业要顺势而为，找准市场痛点",
                        "voice_description": "longwan_v2",
                        "tone_description": "自信、果断、富有感染力"
                    },
                    {
                        "name": "孙投资人",
                        "persona": "知名投资人，专注早期项目",
                        "core_viewpoint": "好的创业者要有格局和执行力",
                        "voice_description": "longyuan_v2",
                        "tone_description": "理性、犀利、一针见血"
                    }
                ]
            },
            "5": {
                "topic": "传统文化的现代传承与创新",
                "atmosphere": "warm_healing",
                "target_duration": "3分钟",
                "language_style": "formal",
                "characters": [
                    {
                        "name": "刘教授",
                        "persona": "文化学者，研究传统文化多年",
                        "core_viewpoint": "传承不是简单复制，要创造性转化",
                        "voice_description": "longyuan_v2",
                        "tone_description": "儒雅、深邃、富有文化底蕴"
                    },
                    {
                        "name": "小雅",
                        "persona": "文创设计师，将传统元素融入现代设计",
                        "core_viewpoint": "传统文化需要年轻化表达",
                        "voice_description": "longxiaoyuan_v2",
                        "tone_description": "充满创意、年轻活力"
                    }
                ]
            }
        }
        
        return configs.get(choice)
    
    def get_custom_config(self) -> Dict:
        """获取自定义配置"""
        print("\n📝 自定义播客配置")
        print("-" * 70)
        
        topic = input("  主题 (必填): ").strip()
        while not topic:
            print("  ❌ 主题不能为空")
            topic = input("  主题 (必填): ").strip()
        
        title = input("  标题 (可选，回车跳过): ").strip() or None
        
        print("\n  选择讨论氛围:")
        print("    1. 轻松幽默 (relaxed_humorous)")
        print("    2. 严肃深度 (serious_deep)")
        print("    3. 激烈辩论 (heated_debate)")
        print("    4. 温暖治愈 (warm_healing)")
        atmosphere_choice = input("  请选择 [1-4]: ").strip() or "1"
        atmosphere_map = {
            "1": "relaxed_humorous",
            "2": "serious_deep",
            "3": "heated_debate",
            "4": "warm_healing"
        }
        atmosphere = atmosphere_map.get(atmosphere_choice, "relaxed_humorous")
        
        duration = input("  目标时长 (如: 3分钟) [默认3分钟]: ").strip() or "3分钟"
        
        print("\n  选择语言风格:")
        print("    1. 口语化 (colloquial)")
        print("    2. 正式 (formal)")
        language_choice = input("  请选择 [1-2]: ").strip() or "1"
        language_map = {"1": "colloquial", "2": "formal"}
        language_style = language_map.get(language_choice, "colloquial")
        
        # 简化版角色配置
        characters = [
            {
                "name": "主持人",
                "persona": "专业主持人，善于引导话题",
                "core_viewpoint": "客观中立，追求真理",
                "voice_description": "longwan_v2",
                "tone_description": "专业、友好"
            },
            {
                "name": "嘉宾",
                "persona": "行业专家，有深刻见解",
                "core_viewpoint": "专业权威，经验丰富",
                "voice_description": "longxiaochun_v2",
                "tone_description": "专业、热情"
            }
        ]
        
        background = input("\n  背景资料 (可选，回车跳过): ").strip() or None
        
        return {
            "topic": topic,
            "title": title,
            "atmosphere": atmosphere,
            "target_duration": duration,
            "language_style": language_style,
            "characters": characters,
            "background_materials": background
        }
    
    def generate_podcast(self, config: Dict) -> Optional[str]:
        """生成播客"""
        print("\n" + "="*70)
        print("🚀 开始生成播客...")
        print("="*70)
        
        # 提交任务
        try:
            url = f"{self.api_base_url}/api/v1/podcast/generate"
            response = requests.post(url, json={"custom_form": config}, timeout=30)
            response.raise_for_status()
            result = response.json()
            task_id = result.get("task_id")
            
            print(f"✅ 任务创建成功")
            print(f"📝 任务ID: {task_id}")
            print(f"📊 主题: {config['topic']}\n")
            
        except Exception as e:
            print(f"❌ 任务创建失败: {str(e)}")
            return None
        
        # 等待完成
        print("⏳ 生成中，请稍候...")
        print("   预计耗时: 2-5分钟\n")
        
        status_url = f"{self.api_base_url}/api/v1/podcast/status/{task_id}"
        start_time = time.time()
        
        while time.time() - start_time < 600:  # 10分钟超时
            try:
                response = requests.get(status_url, timeout=10)
                status = response.json()
                
                elapsed = int(time.time() - start_time)
                print(f"  ⏱️  已耗时: {elapsed}s", end="\r")
                
                if status["status"] == "completed":
                    print(f"\n\n✅ 生成完成！(总耗时: {elapsed}s)")
                    return task_id
                elif status["status"] == "failed":
                    print(f"\n\n❌ 生成失败: {status.get('message', 'Unknown error')}")
                    return None
                
                time.sleep(3)
                
            except Exception as e:
                print(f"\n⚠️  查询状态失败: {str(e)}")
                time.sleep(5)
        
        print("\n\n⏰ 任务超时")
        return None
    
    def download_results(self, task_id: str):
        """下载结果"""
        print("\n" + "="*70)
        print("📥 下载生成结果...")
        print("="*70 + "\n")
        
        # 下载音频
        try:
            audio_url = f"{self.api_base_url}/api/v1/podcast/download/{task_id}"
            response = requests.get(audio_url, timeout=30)
            response.raise_for_status()
            
            audio_path = os.path.join(self.output_dir, f"podcast_{task_id}.mp3")
            with open(audio_path, "wb") as f:
                f.write(response.content)
            
            size_mb = os.path.getsize(audio_path) / 1024 / 1024
            print(f"✅ 音频文件: {audio_path}")
            print(f"   大小: {size_mb:.2f} MB\n")
            
        except Exception as e:
            print(f"❌ 下载音频失败: {str(e)}\n")
            audio_path = None
        
        # 获取剧本
        try:
            status_url = f"{self.api_base_url}/api/v1/podcast/status/{task_id}"
            response = requests.get(status_url, timeout=10)
            status = response.json()
            
            if status.get("script"):
                script_path = os.path.join(self.output_dir, f"script_{task_id}.json")
                with open(script_path, "w", encoding="utf-8") as f:
                    json.dump(status["script"], f, ensure_ascii=False, indent=2)
                
                print(f"✅ 剧本文件: {script_path}\n")
                
                # 显示部分剧本
                self._display_script_preview(status["script"])
            
        except Exception as e:
            print(f"❌ 获取剧本失败: {str(e)}\n")
    
    def _display_script_preview(self, script: Dict):
        """显示剧本预览"""
        print("="*70)
        print("📄 剧本预览 (前3段对话)")
        print("="*70 + "\n")
        
        dialogues = script.get("dialogues", [])[:3]
        for i, dialogue in enumerate(dialogues, 1):
            print(f"[{i}] {dialogue.get('character_name', 'Unknown')}")
            print(f"    {dialogue.get('content', '')}")
            if dialogue.get('emotion'):
                print(f"    (情感: {dialogue['emotion']})")
            print()
        
        if len(script.get("dialogues", [])) > 3:
            print(f"... 还有 {len(script.get('dialogues', [])) - 3} 段对话\n")
    
    def run(self):
        """运行交互式演示"""
        self.display_header()
        
        if not self.check_server():
            return
        
        while True:
            self.show_preset_scenarios()
            
            choice = input("请选择场景 [1-6] (输入 q 退出): ").strip()
            
            if choice.lower() == 'q':
                print("\n👋 感谢使用！再见！\n")
                break
            
            if choice == "6":
                config = self.get_custom_config()
            else:
                config = self.get_preset_config(choice)
            
            if not config:
                print("❌ 无效的选择，请重试\n")
                continue
            
            # 显示配置
            print("\n" + "="*70)
            print("📋 配置信息")
            print("="*70)
            print(f"主题: {config['topic']}")
            print(f"氛围: {config['atmosphere']}")
            print(f"时长: {config['target_duration']}")
            print(f"角色: {', '.join(c['name'] for c in config['characters'])}")
            print("="*70)
            
            confirm = input("\n确认生成？[Y/n]: ").strip().lower()
            if confirm and confirm != 'y':
                print("❌ 已取消\n")
                continue
            
            # 生成播客
            task_id = self.generate_podcast(config)
            
            if task_id:
                self.download_results(task_id)
                
                print("="*70)
                print("✨ 本次生成完成！")
                print("="*70)
                print(f"📁 输出目录: {self.output_dir}")
                print(f"🎯 任务ID: {task_id}")
                print("="*70 + "\n")
            
            again = input("继续生成？[Y/n]: ").strip().lower()
            if again and again != 'y':
                print("\n👋 感谢使用！再见！\n")
                break


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AI播客交互式演示程序")
    parser.add_argument("--api", default="http://localhost:8000", help="API服务地址")
    
    args = parser.parse_args()
    
    demo = InteractivePodcastDemo(api_base_url=args.api)
    demo.run()


if __name__ == "__main__":
    main()
