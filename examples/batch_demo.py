#!/usr/bin/env python3
"""
批量播客生成演示程序
用于演示系统的批量处理能力，适合评委快速评估模型效果
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import List, Dict
import argparse
from datetime import datetime


class PodcastBatchGenerator:
    """批量播客生成器"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.results = []
        
    def check_server_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_podcast(self, config: Dict) -> str:
        """生成单个播客并返回task_id"""
        url = f"{self.api_base_url}/api/v1/podcast/generate"
        
        try:
            response = requests.post(url, json={"custom_form": config}, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("task_id")
        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")
            return None
    
    def wait_for_completion(self, task_id: str, timeout: int = 300) -> Dict:
        """等待任务完成"""
        url = f"{self.api_base_url}/api/v1/podcast/status/{task_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=10)
                status = response.json()
                
                if status["status"] == "completed":
                    return status
                elif status["status"] == "failed":
                    return status
                
                print(f"  ⏳ 任务 {task_id[:8]} 进行中... ({int(time.time() - start_time)}s)")
                time.sleep(5)
                
            except Exception as e:
                print(f"  ⚠️  查询状态失败: {str(e)}")
                time.sleep(5)
        
        return {"status": "timeout", "message": "任务超时"}
    
    def download_audio(self, task_id: str, output_dir: str) -> str:
        """下载音频文件"""
        url = f"{self.api_base_url}/api/v1/podcast/download/{task_id}"
        output_path = os.path.join(output_dir, f"podcast_{task_id}.mp3")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            return output_path
        except Exception as e:
            print(f"  ❌ 下载失败: {str(e)}")
            return None
    
    def batch_generate(self, configs: List[Dict], output_dir: str = "output/batch_demo"):
        """批量生成播客"""
        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"🚀 批量播客生成演示")
        print(f"{'='*60}")
        print(f"📊 任务数量: {len(configs)}")
        print(f"📁 输出目录: {output_dir}")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 检查服务器
        print("🔍 检查服务器状态...")
        if not self.check_server_health():
            print("❌ 服务器未响应，请先启动服务: python run_server.py")
            return
        print("✅ 服务器运行正常\n")
        
        # 批量提交任务
        task_ids = []
        for i, config in enumerate(configs, 1):
            print(f"📝 [{i}/{len(configs)}] 提交任务: {config.get('topic', 'Unknown')}")
            task_id = self.generate_podcast(config)
            
            if task_id:
                print(f"  ✅ 任务创建成功: {task_id}")
                task_ids.append((task_id, config))
            else:
                print(f"  ❌ 任务创建失败")
            
            time.sleep(1)  # 避免请求过快
        
        print(f"\n{'='*60}")
        print(f"⏳ 等待任务完成 (共 {len(task_ids)} 个任务)")
        print(f"{'='*60}\n")
        
        # 等待所有任务完成
        results = []
        for i, (task_id, config) in enumerate(task_ids, 1):
            print(f"[{i}/{len(task_ids)}] 处理任务: {task_id[:8]}... - {config.get('topic')}")
            
            start_time = time.time()
            status = self.wait_for_completion(task_id)
            elapsed_time = time.time() - start_time
            
            result = {
                "task_id": task_id,
                "topic": config.get("topic"),
                "status": status["status"],
                "generation_time": elapsed_time,
                "config": config
            }
            
            if status["status"] == "completed":
                print(f"  ✅ 生成成功 (耗时: {elapsed_time:.1f}s)")
                
                # 下载音频
                print(f"  ⬇️  下载音频...")
                audio_path = self.download_audio(task_id, output_dir)
                if audio_path:
                    result["audio_path"] = audio_path
                    result["audio_size"] = os.path.getsize(audio_path) / 1024 / 1024  # MB
                    print(f"  💾 已保存: {audio_path} ({result['audio_size']:.2f} MB)")
                
                # 保存剧本
                if status.get("script"):
                    script_path = os.path.join(output_dir, f"script_{task_id}.json")
                    with open(script_path, "w", encoding="utf-8") as f:
                        json.dump(status["script"], f, ensure_ascii=False, indent=2)
                    result["script_path"] = script_path
                    print(f"  📄 剧本已保存: {script_path}")
                
            else:
                print(f"  ❌ 生成失败: {status.get('message', 'Unknown error')}")
                result["error"] = status.get("message")
            
            results.append(result)
            print()
        
        # 保存汇总报告
        self._save_summary_report(results, output_dir)
        
        # 打印统计信息
        self._print_statistics(results)
        
        return results
    
    def _save_summary_report(self, results: List[Dict], output_dir: str):
        """保存汇总报告"""
        report_path = os.path.join(output_dir, "batch_report.json")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tasks": len(results),
            "successful": sum(1 for r in results if r["status"] == "completed"),
            "failed": sum(1 for r in results if r["status"] != "completed"),
            "results": results
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📊 汇总报告已保存: {report_path}")
    
    def _print_statistics(self, results: List[Dict]):
        """打印统计信息"""
        successful = [r for r in results if r["status"] == "completed"]
        failed = [r for r in results if r["status"] != "completed"]
        
        print(f"\n{'='*60}")
        print(f"📈 批量生成统计报告")
        print(f"{'='*60}")
        print(f"✅ 成功: {len(successful)} / {len(results)}")
        print(f"❌ 失败: {len(failed)} / {len(results)}")
        print(f"📊 成功率: {len(successful) / len(results) * 100:.1f}%")
        
        if successful:
            avg_time = sum(r["generation_time"] for r in successful) / len(successful)
            total_size = sum(r.get("audio_size", 0) for r in successful)
            print(f"⏱️  平均生成时间: {avg_time:.1f}s")
            print(f"💾 总音频大小: {total_size:.2f} MB")
        
        print(f"{'='*60}\n")


def get_demo_configs() -> List[Dict]:
    """获取演示配置"""
    return [
        {
            "topic": "人工智能的未来发展趋势",
            "title": "AI前沿对话",
            "atmosphere": "serious_deep",
            "target_duration": "3分钟",
            "language_style": "formal",
            "characters": [
                {
                    "name": "李明",
                    "persona": "资深AI研究员，深度学习专家",
                    "core_viewpoint": "AI将深刻改变人类社会，但需要关注伦理和安全",
                    "voice_description": "longwan_v2",
                    "tone_description": "专业、理性、略带热情",
                    "language_habits": "喜欢用技术术语，解释问题条理清晰"
                },
                {
                    "name": "王芳",
                    "persona": "科技记者，关注AI伦理和社会影响",
                    "core_viewpoint": "技术进步需要与人文关怀并重",
                    "voice_description": "longxiaochun_v2",
                    "tone_description": "好奇、客观、富有同理心",
                    "language_habits": "善于提问，引导讨论深入"
                }
            ],
            "background_materials": "人工智能技术在近年来取得了显著进展，从自然语言处理到计算机视觉，各个领域都在快速发展。"
        },
        {
            "topic": "在线教育的机遇与挑战",
            "atmosphere": "relaxed_humorous",
            "target_duration": "3分钟",
            "language_style": "colloquial",
            "characters": [
                {
                    "name": "张老师",
                    "persona": "资深教育工作者，有20年教学经验",
                    "core_viewpoint": "在线教育是趋势，但不能完全取代传统教育",
                    "voice_description": "longyuan_v2",
                    "tone_description": "亲切、温和、有耐心"
                },
                {
                    "name": "小林",
                    "persona": "在线教育平台产品经理，90后创业者",
                    "core_viewpoint": "技术可以让教育更加公平和高效",
                    "voice_description": "longxiaoyuan_v2",
                    "tone_description": "活力、热情、充满信心"
                }
            ]
        },
        {
            "topic": "健康生活方式的重要性",
            "atmosphere": "warm_healing",
            "target_duration": "3分钟",
            "language_style": "colloquial",
            "characters": [
                {
                    "name": "陈医生",
                    "persona": "营养学专家，倡导健康生活",
                    "core_viewpoint": "健康是一切幸福的基础",
                    "voice_description": "longxiaoxia_v2",
                    "tone_description": "温暖、关怀、专业"
                },
                {
                    "name": "李健",
                    "persona": "健身教练，分享健康知识",
                    "core_viewpoint": "运动和饮食同等重要",
                    "voice_description": "longwan_v2",
                    "tone_description": "积极、鼓励、富有感染力"
                }
            ]
        }
    ]


def main():
    parser = argparse.ArgumentParser(description="AI播客批量生成演示程序")
    parser.add_argument("--api", default="http://localhost:8000", help="API服务地址")
    parser.add_argument("--output", default="output/batch_demo", help="输出目录")
    parser.add_argument("--config", help="自定义配置文件路径 (JSON格式)")
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config and os.path.exists(args.config):
        with open(args.config, "r", encoding="utf-8") as f:
            configs = json.load(f)
    else:
        configs = get_demo_configs()
    
    # 创建生成器
    generator = PodcastBatchGenerator(api_base_url=args.api)
    
    # 批量生成
    results = generator.batch_generate(configs, output_dir=args.output)
    
    print("✨ 批量生成完成！")
    print(f"📁 所有文件已保存至: {args.output}")
    print(f"📊 查看详细报告: {os.path.join(args.output, 'batch_report.json')}")


if __name__ == "__main__":
    main()
