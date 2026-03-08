#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome插件机会发现器主脚本
负责整合各个模块，执行完整的分析流程
支持单个插件分析和基于状态的增量分析
"""

import time
import argparse
from crawler.plugin_crawler import crawl_plugins
from crawler.review_crawler import crawl_reviews
from analyzer.review_analyzer import analyze_plugins
from analyzer.opportunity_generator import generate_opportunities
from analyzer.comment_analyzer import CommentAnalyzer, analyze_plugin_reviews, analyze_all_pending
from analyzer.product_opportunity_generator import ProductOpportunityGenerator, generate_product_opportunity, generate_all_opportunities
from storage.excel_writer import save_to_excel
from storage.db_manager import DBManager
from utils.status_manager import StatusManager
from utils.data_viewer import DataViewer


def parse_args():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 命令行参数
    """
    parser = argparse.ArgumentParser(description='Chrome插件机会发现器')
    parser.add_argument('--crawl', action='store_true', help='爬取插件信息')
    parser.add_argument('--reviews', action='store_true', help='抓取评论')
    parser.add_argument('--analyze', action='store_true', help='分析评论')
    parser.add_argument('--generate', action='store_true', help='生成产品机会')
    parser.add_argument('--export', action='store_true', help='导出到Excel')
    parser.add_argument('--visualize', action='store_true', help='生成数据可视化')
    parser.add_argument('--all', action='store_true', help='执行完整流程')
    parser.add_argument('--plugin-id', type=int, help='单个插件ID')
    parser.add_argument('--status', action='store_true', help='查看分析状态')
    parser.add_argument('--show-plugins', action='store_true', help='显示插件列表')
    parser.add_argument('--show-reviews', type=int, help='显示插件评论 (需要插件ID)')
    parser.add_argument('--show-analysis', type=int, help='显示分析结果 (需要插件ID)')
    parser.add_argument('--show-opportunity', type=int, help='显示产品机会 (需要插件ID)')
    parser.add_argument('--show-details', type=int, help='显示插件完整信息 (需要插件ID)')
    parser.add_argument('--show-top', action='store_true', help='显示最佳产品机会')
    parser.add_argument('--limit', type=int, default=10, help='显示数量限制')
    return parser.parse_args()


def main():
    """
    主函数，执行分析流程
    """
    start_time = time.time()
    args = parse_args()
    
    print("===== Chrome插件机会发现器 =====")
    
    # 查看分析状态
    if args.status:
        print("\n=== 分析状态 ===")
        status_manager = StatusManager()
        
        pending_reviews = status_manager.get_pending_reviews()
        print(f"待抓取评论: {len(pending_reviews)} 个插件")
        
        pending_analysis = status_manager.get_pending_analysis()
        print(f"待分析评论: {len(pending_analysis)} 个插件")
        
        pending_opportunities = status_manager.get_pending_opportunities()
        print(f"待生成机会: {len(pending_opportunities)} 个插件")
        
        completed = status_manager.get_completed_plugins()
        print(f"已完成分析: {len(completed)} 个插件")
        
        status_manager.close()
        return
    
    # 显示插件列表
    if args.show_plugins:
        print("\n=== 插件列表 ===")
        viewer = DataViewer()
        viewer.show_plugins(limit=args.limit)
        viewer.close()
        return
    
    # 显示插件评论
    if args.show_reviews:
        print(f"\n=== 插件评论 (ID: {args.show_reviews}) ===")
        viewer = DataViewer()
        viewer.show_reviews(args.show_reviews, limit=args.limit)
        viewer.close()
        return
    
    # 显示分析结果
    if args.show_analysis:
        print(f"\n=== 分析结果 (ID: {args.show_analysis}) ===")
        viewer = DataViewer()
        viewer.show_analysis(args.show_analysis)
        viewer.close()
        return
    
    # 显示产品机会
    if args.show_opportunity:
        print(f"\n=== 产品机会 (ID: {args.show_opportunity}) ===")
        viewer = DataViewer()
        viewer.show_opportunity(args.show_opportunity)
        viewer.close()
        return
    
    # 显示插件完整信息
    if args.show_details:
        print(f"\n=== 插件完整信息 (ID: {args.show_details}) ===")
        viewer = DataViewer()
        viewer.show_plugin_details(args.show_details)
        viewer.close()
        return
    
    # 显示最佳产品机会
    if args.show_top:
        print("\n=== 最佳产品机会 ===")
        viewer = DataViewer()
        viewer.show_top_opportunities(limit=args.limit)
        viewer.close()
        return
    
    # 执行完整流程
    if args.all:
        # 1. 爬取插件信息
        print("\n1. 正在爬取Chrome插件信息...")
        plugins = crawl_plugins()
        
        if not plugins:
            print("没有找到符合条件的插件，程序退出")
            return
        
        # 2. 抓取用户评论
        print("\n2. 正在抓取用户评论...")
        plugins_with_reviews = crawl_reviews(plugins)
        
        # 3. 分析评论
        print("\n3. 正在分析用户评论...")
        plugins_with_analysis = analyze_plugins(plugins_with_reviews)
        
        # 4. 生成产品机会
        print("\n4. 正在生成产品机会...")
        plugins_with_opportunities = generate_opportunities(plugins_with_analysis)
        
        # 5. 保存到Excel
        print("\n5. 正在保存分析结果...")
        output_file = save_to_excel(plugins_with_opportunities)
    
    # 只爬取插件
    elif args.crawl:
        print("\n正在爬取Chrome插件信息...")
        crawl_plugins()
    
    # 只抓取评论
    elif args.reviews:
        print("\n正在抓取用户评论...")
        status_manager = StatusManager()
        pending_plugins = status_manager.get_pending_reviews()
        if pending_plugins:
            crawl_reviews(pending_plugins)
        else:
            print("没有待抓取评论的插件")
        status_manager.close()
    
    # 只分析评论
    elif args.analyze:
        print("\n正在分析用户评论...")
        analyze_all_pending()
    
    # 只生成产品机会
    elif args.generate:
        print("\n正在生成产品机会...")
        generate_all_opportunities()
    
    # 只导出到Excel
    elif args.export:
        print("\n正在导出分析结果...")
        save_to_excel()
    
    # 生成数据可视化
    elif args.visualize:
        print("\n正在生成数据可视化...")
        from utils.visualizer import generate_visualizations
        generate_visualizations()
    
    # 单个插件分析
    elif args.plugin_id:
        print(f"\n正在分析插件ID: {args.plugin_id}")
        db = DBManager()
        plugin = db.get_plugin(args.plugin_id)
        
        if not plugin:
            print(f"未找到插件ID: {args.plugin_id}")
            db.close()
            return
        
        # 抓取评论
        print(f"1. 正在抓取 {plugin['name']} 的评论...")
        plugins = [plugin]
        plugins_with_reviews = crawl_reviews(plugins)
        
        # 分析评论
        print(f"2. 正在分析 {plugin['name']} 的评论...")
        plugins_with_analysis = analyze_plugins(plugins_with_reviews)
        
        # 生成产品机会
        print(f"3. 正在为 {plugin['name']} 生成产品机会...")
        plugins_with_opportunities = generate_opportunities(plugins_with_analysis)
        
        # 保存到Excel
        print("4. 正在保存分析结果...")
        save_to_excel(plugins_with_opportunities)
        
        db.close()
    
    # 默认执行完整流程
    else:
        # 1. 爬取插件信息
        print("\n1. 正在爬取Chrome插件信息...")
        plugins = crawl_plugins()
        
        if not plugins:
            print("没有找到符合条件的插件，程序退出")
            return
        
        # 2. 抓取用户评论
        print("\n2. 正在抓取用户评论...")
        plugins_with_reviews = crawl_reviews(plugins)
        
        # 3. 分析评论
        print("\n3. 正在分析用户评论...")
        plugins_with_analysis = analyze_plugins(plugins_with_reviews)
        
        # 4. 生成产品机会
        print("\n4. 正在生成产品机会...")
        plugins_with_opportunities = generate_opportunities(plugins_with_analysis)
        
        # 5. 保存到Excel
        print("\n5. 正在保存分析结果...")
        output_file = save_to_excel(plugins_with_opportunities)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n===== 分析完成 =====")
    print(f"总用时: {total_time:.2f} 秒")


if __name__ == "__main__":
    main()
