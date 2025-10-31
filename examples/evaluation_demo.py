#!/usr/bin/env python3
"""
批量评估演示程序
用于评估生成的播客质量，生成详细的评估报告
"""

import requests
import json
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import time


class PodcastEvaluator:
    """播客质量评估器"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
    
    def evaluate_podcast(self, task_id: str) -> Dict:
        """评估单个播客"""
        url = f"{self.api_base_url}/api/v1/quality/assess"
        
        try:
            payload = {
                "task_id": task_id,
                "include_audio_analysis": True,
                "include_content_analysis": True
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def batch_evaluate(self, task_ids: List[str], output_dir: str = "output/evaluation"):
        """批量评估播客"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"📊 批量播客质量评估")
        print(f"{'='*60}")
        print(f"🎯 评估任务数: {len(task_ids)}")
        print(f"📁 输出目录: {output_dir}")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        results = []
        
        for i, task_id in enumerate(task_ids, 1):
            print(f"[{i}/{len(task_ids)}] 评估任务: {task_id[:8]}...")
            
            start_time = time.time()
            evaluation = self.evaluate_podcast(task_id)
            elapsed_time = time.time() - start_time
            
            result = {
                "task_id": task_id,
                "evaluation_time": elapsed_time,
                "timestamp": datetime.now().isoformat()
            }
            
            if evaluation.get("success", True):
                result.update(evaluation)
                print(f"  ✅ 评估完成 (耗时: {elapsed_time:.1f}s)")
                
                # 打印关键指标
                if "overall_score" in evaluation:
                    print(f"  📊 综合评分: {evaluation['overall_score']:.1f}/10")
                if "content_quality" in evaluation:
                    print(f"  📝 内容质量: {evaluation['content_quality']:.1f}/10")
                if "audio_quality" in evaluation:
                    print(f"  🎵 音频质量: {evaluation['audio_quality']:.1f}/10")
            else:
                result["error"] = evaluation.get("error", "Unknown error")
                print(f"  ❌ 评估失败: {result['error']}")
            
            results.append(result)
            print()
        
        # 保存详细报告
        self._save_detailed_report(results, output_dir)
        
        # 生成汇总统计
        self._generate_summary_statistics(results, output_dir)
        
        # 打印统计信息
        self._print_statistics(results)
        
        return results
    
    def _save_detailed_report(self, results: List[Dict], output_dir: str):
        """保存详细评估报告"""
        report_path = os.path.join(output_dir, "evaluation_report.json")
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📊 详细报告已保存: {report_path}")
    
    def _generate_summary_statistics(self, results: List[Dict], output_dir: str):
        """生成汇总统计"""
        successful = [r for r in results if "error" not in r]
        
        if not successful:
            return
        
        # 计算平均分数
        avg_overall = sum(r.get("overall_score", 0) for r in successful) / len(successful)
        avg_content = sum(r.get("content_quality", 0) for r in successful) / len(successful)
        avg_audio = sum(r.get("audio_quality", 0) for r in successful) / len(successful)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_evaluated": len(results),
            "successful_evaluations": len(successful),
            "failed_evaluations": len(results) - len(successful),
            "average_scores": {
                "overall": round(avg_overall, 2),
                "content_quality": round(avg_content, 2),
                "audio_quality": round(avg_audio, 2)
            },
            "score_distribution": self._get_score_distribution(successful),
            "recommendations": self._generate_recommendations(successful)
        }
        
        summary_path = os.path.join(output_dir, "evaluation_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📈 汇总统计已保存: {summary_path}")
    
    def _get_score_distribution(self, results: List[Dict]) -> Dict:
        """获取分数分布"""
        distribution = {
            "excellent (9-10分)": 0,
            "good (7-8分)": 0,
            "acceptable (5-6分)": 0,
            "poor (<5分)": 0
        }
        
        for r in results:
            score = r.get("overall_score", 0)
            if score >= 9:
                distribution["excellent (9-10分)"] += 1
            elif score >= 7:
                distribution["good (7-8分)"] += 1
            elif score >= 5:
                distribution["acceptable (5-6分)"] += 1
            else:
                distribution["poor (<5分)"] += 1
        
        return distribution
    
    def _generate_recommendations(self, results: List[Dict]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        avg_content = sum(r.get("content_quality", 0) for r in results) / len(results)
        avg_audio = sum(r.get("audio_quality", 0) for r in results) / len(results)
        
        if avg_content < 7:
            recommendations.append("建议：提升内容质量，增强话题深度和逻辑连贯性")
        
        if avg_audio < 7:
            recommendations.append("建议：优化音频处理流程，提升语音合成质量")
        
        if avg_content >= 8 and avg_audio >= 8:
            recommendations.append("优秀：整体质量优秀，可直接用于生产环境")
        
        return recommendations
    
    def _print_statistics(self, results: List[Dict]):
        """打印统计信息"""
        successful = [r for r in results if "error" not in r]
        
        print(f"\n{'='*60}")
        print(f"📊 评估统计报告")
        print(f"{'='*60}")
        print(f"✅ 成功评估: {len(successful)} / {len(results)}")
        print(f"❌ 失败评估: {len(results) - len(successful)} / {len(results)}")
        
        if successful:
            avg_overall = sum(r.get("overall_score", 0) for r in successful) / len(successful)
            avg_content = sum(r.get("content_quality", 0) for r in successful) / len(successful)
            avg_audio = sum(r.get("audio_quality", 0) for r in successful) / len(successful)
            
            print(f"\n📈 平均分数:")
            print(f"  • 综合评分: {avg_overall:.2f}/10")
            print(f"  • 内容质量: {avg_content:.2f}/10")
            print(f"  • 音频质量: {avg_audio:.2f}/10")
            
            # 分数分布
            distribution = self._get_score_distribution(successful)
            print(f"\n📊 分数分布:")
            for level, count in distribution.items():
                percentage = count / len(successful) * 100
                print(f"  • {level}: {count} ({percentage:.1f}%)")
        
        print(f"{'='*60}\n")


def load_task_ids_from_report(report_path: str) -> List[str]:
    """从批量生成报告中加载task_id"""
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    
    task_ids = []
    for result in report.get("results", []):
        if result.get("status") == "completed":
            task_ids.append(result["task_id"])
    
    return task_ids


def main():
    parser = argparse.ArgumentParser(description="AI播客批量评估演示程序")
    parser.add_argument("--api", default="http://localhost:8000", help="API服务地址")
    parser.add_argument("--output", default="output/evaluation", help="输出目录")
    parser.add_argument("--task-ids", nargs="+", help="要评估的task_id列表")
    parser.add_argument("--report", help="批量生成报告路径 (从中提取task_id)")
    
    args = parser.parse_args()
    
    # 获取task_id列表
    if args.task_ids:
        task_ids = args.task_ids
    elif args.report and os.path.exists(args.report):
        task_ids = load_task_ids_from_report(args.report)
        if not task_ids:
            print("❌ 报告中未找到已完成的任务")
            return
    else:
        print("❌ 请提供 --task-ids 或 --report 参数")
        parser.print_help()
        return
    
    # 创建评估器
    evaluator = PodcastEvaluator(api_base_url=args.api)
    
    # 批量评估
    results = evaluator.batch_evaluate(task_ids, output_dir=args.output)
    
    print("✨ 批量评估完成！")
    print(f"📁 所有文件已保存至: {args.output}")
    print(f"📊 查看详细报告: {os.path.join(args.output, 'evaluation_report.json')}")
    print(f"📈 查看汇总统计: {os.path.join(args.output, 'evaluation_summary.json')}")


if __name__ == "__main__":
    main()
