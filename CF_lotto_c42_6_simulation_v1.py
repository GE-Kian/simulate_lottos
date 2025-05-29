# -*- coding: utf-8 -*-
"""
Created on Tue May 13 16:30:10 2025

@author: Kevin
"""
from flask import Flask, request, jsonify, current_app, send_file
from flask_cors import CORS
import json
import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import deque
import psutil
import os
import gc
import time
import csv
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from flask_socketio import SocketIO

def cleanup_memory():
    """执行内存清理"""
    gc.collect()
    return psutil.Process().memory_info().rss / 1024 / 1024  # 返回当前内存使用量（MB）

def get_memory_usage():
    """获取当前内存使用情况"""
    return psutil.Process().memory_info().rss / 1024 / 1024  # MB

def validate_batch_results(batch_results):
    """验证批次结果的完整性"""
    required_fields = ['total_players', 'total_bets', 'total_payouts', 'prize_counts', 'rounds_data']
    for field in required_fields:
        if field not in batch_results:
            raise ValueError(f"批次结果缺少必要字段: {field}")
    
    if not isinstance(batch_results['rounds_data'], list):
        raise ValueError("rounds_data 必须是列表类型")
    
    for round_data in batch_results['rounds_data']:
        validate_round_data(round_data)

def validate_round_data(round_data):
    """验证轮次数据的完整性"""
    required_fields = ['round', 'players', 'bets', 'payouts', 'prizes', 'rtp']
    for field in required_fields:
        if field not in round_data:
            raise ValueError(f"轮次数据缺少必要字段: {field}")
    
    if not isinstance(round_data['prizes'], dict):
        raise ValueError("prizes 必须是字典类型")
    
    for level in ['1', '2', '3', '4']:
        if level not in round_data['prizes']:
            raise ValueError(f"prizes 缺少奖级: {level}")

# 游戏参数设置
BET_AMOUNT = 2.0  # 每注金额
PRIZE_TABLE = {
    1: 5000000.0,  # 一等奖
    2: 100000.0,   # 二等奖
    3: 3000.0,     # 三等奖
    4: 100.0       # 四等奖
}

# 其他常量
MAX_MEMORY_USAGE = 1024  # 最大内存使用量（MB）
MAX_DETAILED_DATA = 10000  # 最大保存的详细数据条数

# 游戏参数设置
BET_AMOUNT = 2.0  # 每注金额
PRIZE_TABLE = {
    1: 5000000.0,  # 一等奖
    2: 100000.0,   # 二等奖
    3: 3000.0,     # 三等奖
    4: 100.0       # 四等奖
}

def generate_random_numbers(count, max_num):
    """生成指定数量的不重复随机数字"""
    return sorted(random.sample(range(1, max_num + 1), count))

def generate_biased_numbers():
    """生成偏向于小数字的号码（模拟使用生日等特殊数字的情况）"""
    numbers = set()
    while len(numbers) < 6:
        if random.random() < 0.7:  # 70%概率选择小数字
            num = random.randint(1, 31)  # 偏向于1-31（月份和日期范围）
        else:
            num = random.randint(32, 42)
        numbers.add(num)
    return sorted(list(numbers))

def generate_player_numbers():
    """生成玩家投注号码"""
    return sorted(random.sample(range(1, 43), 6))

def check_matches(winning_numbers, player_numbers):
    """检查匹配数量"""
    return len(set(winning_numbers) & set(player_numbers))

def get_memory_usage():
    """获取当前进程的内存使用情况（MB）"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def cleanup_memory():
    """清理内存"""
    gc.collect()
    
def cleanup_progress():
    """清理进度文件"""
    try:
        if os.path.exists('progress.json'):
            os.remove('progress.json')
    except Exception as e:
        current_app.logger.error(f"清理进度文件失败: {str(e)}")

def convert_to_serializable(obj):
    """转换数据为可序列化的格式"""
    if isinstance(obj, dict):
        return {str(k): convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(x) for x in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif isinstance(obj, (datetime, timedelta)):
        return str(obj)
    else:
        return str(obj)
def get_memory_usage():
    """获取当前进程的内存使用情况"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # 转换为MB

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32,
                          np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        return super().default(obj)

app = Flask(__name__)
CORS(app)
app.json_encoder = CustomJSONEncoder

def analyze_stats(stats_list):
    """分析统计数据趋势"""
    if not stats_list:
        return {}
    
    analysis = {
        'trends': {
            'rtp': [],
            'players_per_round': [],
            'bets_per_round': [],
            'payouts_per_round': [],
            'jackpot_frequency': []
        },
        'averages': {},
        'peaks': {},
        'total_duration': ''
    }
    
    # 计算趋势
    for stats in stats_list:
        completed_rounds = stats['completed_rounds']
        if completed_rounds > 0:
            analysis['trends']['rtp'].append(stats['stats']['rtp'])
            analysis['trends']['players_per_round'].append(
                stats['stats']['total_players'] / completed_rounds)
            analysis['trends']['bets_per_round'].append(
                stats['stats']['total_bets'] / completed_rounds)
            analysis['trends']['payouts_per_round'].append(
                stats['stats']['total_payouts'] / completed_rounds)
            analysis['trends']['jackpot_frequency'].append(
                stats['stats']['jackpot_hits'] / completed_rounds if stats['stats']['jackpot_hits'] > 0 else 0)
    
    # 计算平均值
    for key, values in analysis['trends'].items():
        if values:
            analysis['averages'][key] = sum(values) / len(values)
    
    # 计算峰值
    for key, values in analysis['trends'].items():
        if values:
            analysis['peaks'][key] = max(values)
    
    # 计算总持续时间
    if len(stats_list) >= 2:
        start_time = datetime.strptime(stats_list[0]['timestamp'], "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(stats_list[-1]['timestamp'], "%Y-%m-%d %H:%M:%S")
        analysis['total_duration'] = str(end_time - start_time).split('.')[0]
    
    return analysis

@app.route('/stats_analysis')
def get_stats_analysis():
    """获取统计数据分析结果"""
    try:
        stats_dir = ensure_stats_dir()
        all_stats = []
        
        # 读取所有统计文件
        for file in sorted(os.listdir(stats_dir)):
            if file.startswith('stats_') and file.endswith('.json'):
                with open(os.path.join(stats_dir, file), 'r') as f:
                    stats = json.load(f)
                    all_stats.append(stats)
        
        if not all_stats:
            return jsonify({"error": "No statistics available for analysis"})
        
        # 执行分析
        analysis = analyze_stats(all_stats)
        
        return jsonify({
            "analysis": analysis,
            "total_stats": len(all_stats),
            "time_range": {
                "start": all_stats[0]['timestamp'] if all_stats else None,
                "end": all_stats[-1]['timestamp'] if all_stats else None
            }
        })
    except Exception as e:
        current_app.logger.error(f"统计数据分析失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/export_stats')
def export_stats():
    """导出统计数据为CSV格式"""
    try:
        stats_dir = ensure_stats_dir()
        all_stats = []
        
        # 读取所有统计文件
        for file in sorted(os.listdir(stats_dir)):
            if file.startswith('stats_') and file.endswith('.json'):
                with open(os.path.join(stats_dir, file), 'r') as f:
                    stats = json.load(f)
                    all_stats.append(stats)
        
        if not all_stats:
            return jsonify({"error": "No statistics available for export"})
        
        # 创建CSV文件
        csv_filename = f'stats_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        csv_path = os.path.join(stats_dir, csv_filename)
        
        # 写入CSV数据
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:  # 使用UTF-8-SIG编码支持Excel
            writer = csv.writer(f)
            # 写入表头
            writer.writerow([
                'Timestamp', 'Elapsed Time', 'Completed Rounds', 'Total Rounds',
                'Completion %', 'Total Players', 'Total Bets', 'Total Payouts',
                'Jackpot Hits', 'RTP', 'Prize Count 1', 'Prize Count 2',
                'Prize Count 3', 'Prize Count 4'
            ])
            
            # 写入数据行
            for stat in all_stats:
                writer.writerow([
                    stat['timestamp'],
                    stat['elapsed_time'],
                    stat['completed_rounds'],
                    stat['total_rounds'],
                    stat['completion_percentage'],
                    stat['stats']['total_players'],
                    stat['stats']['total_bets'],
                    stat['stats']['total_payouts'],
                    stat['stats']['jackpot_hits'],
                    stat['stats']['rtp'],
                    stat['stats']['prize_counts'].get('1', 0),
                    stat['stats']['prize_counts'].get('2', 0),
                    stat['stats']['prize_counts'].get('3', 0),
                    stat['stats']['prize_counts'].get('4', 0)
                ])
        
        # 返回文件下载
        return send_file(
            csv_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=csv_filename
        )
        
    except Exception as e:
        current_app.logger.error(f"导出统计数据失败: {str(e)}")
        return jsonify({"error": str(e)}), 500
@app.route('/download_stats/<filename>')
def download_stats(filename):
    """下载统计数据文件"""
    try:
        stats_dir = ensure_stats_dir()
        file_path = os.path.join(stats_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # 检查文件是否是允许下载的类型
        if not (filename.startswith('stats_') and 
                (filename.endswith('.json') or filename.endswith('.csv'))):
            return jsonify({"error": "Invalid file type"}), 400
        
        return send_file(
            file_path,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"下载文件失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/latest_stats')
def get_latest_stats():
    """获取最新的统计数据"""
    try:
        stats_dir = ensure_stats_dir()
        stats_files = []
        for file in os.listdir(stats_dir):
            if file.startswith('stats_') and file.endswith('.json'):
                file_path = os.path.join(stats_dir, file)
                stats_files.append((file, os.path.getmtime(file_path)))
        
        if not stats_files:
            return jsonify({"error": "No statistics available"})
        
        # 获取最新的统计文件
        latest_file = max(stats_files, key=lambda x: x[1])[0]
        with open(os.path.join(stats_dir, latest_file), 'r') as f:
            stats = json.load(f)
        
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"获取最新统计数据失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/all_stats')
def get_all_stats():
    """获取所有统计数据"""
    try:
        stats_dir = ensure_stats_dir()
        all_stats = []
        for file in sorted(os.listdir(stats_dir)):
            if file.startswith('stats_') and file.endswith('.json'):
                with open(os.path.join(stats_dir, file), 'r') as f:
                    stats = json.load(f)
                    all_stats.append(stats)
        
        return jsonify(all_stats)
    except Exception as e:
        current_app.logger.error(f"获取所有统计数据失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

def convert_to_serializable(obj):
    """转换数据为可序列化的格式"""
    if isinstance(obj, dict):
        return {str(k): convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(x) for x in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif isinstance(obj, (datetime, timedelta)):
        return str(obj)
    else:
        return str(obj)

def save_progress(progress):
    """保存进度信息"""
    try:
        # 确保数据可以序列化
        serializable_progress = convert_to_serializable(progress)
        
        # 添加调试日志
        current_app.logger.info(f"Saving progress: current_round={serializable_progress['current_round']}, "
                              f"total_rounds={serializable_progress['total_rounds']}")
        current_app.logger.info(f"Stats: {serializable_progress['stats']}")
        
        # 添加时间戳
        serializable_progress['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 计算完成百分比
        if serializable_progress['total_rounds'] > 0:
            serializable_progress['completion_percentage'] = \
                (serializable_progress['current_round'] / serializable_progress['total_rounds']) * 100
        else:
            serializable_progress['completion_percentage'] = 0
            
        with open('progress.json', 'w') as f:
            json.dump(serializable_progress, f, indent=2)
    except Exception as e:
        current_app.logger.error(f"保存进度失败: {str(e)}")
        current_app.logger.error(f"Progress data: {progress}")
        raise

@app.route('/progress')
def get_progress():
    """获取进度信息"""
    try:
        if os.path.exists('progress.json'):
            try:
                with open('progress.json', 'r') as f:
                    progress = json.load(f)
                    current_app.logger.info(f"Loaded progress data: {progress}")
            except json.JSONDecodeError as e:
                current_app.logger.error(f"JSON解析错误: {str(e)}")
                return jsonify({"error": "Invalid progress data format"}), 500
            except Exception as e:
                current_app.logger.error(f"读取进度文件失败: {str(e)}")
                return jsonify({"error": "Failed to read progress file"}), 500
            
            # 确保所有必要的字段都存在
            if not isinstance(progress, dict):
                current_app.logger.error("Progress data is not a dictionary")
                return jsonify({"error": "Invalid progress data format"}), 500
            
            # 添加默认值
            progress.setdefault('current_round', 0)
            progress.setdefault('total_rounds', 0)
            progress.setdefault('completion_percentage', 0)
            progress.setdefault('last_update', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            stats = progress.setdefault('stats', {})
            stats.setdefault('total_players', 0)
            stats.setdefault('total_bets', 0.0)
            stats.setdefault('total_payouts', 0.0)
            stats.setdefault('jackpot_hits', 0)
            stats.setdefault('prize_counts', {str(i): 0 for i in range(1, 5)})
            stats.setdefault('rtp', 0.0)
            stats.setdefault('elapsed_time', '0:00:00')
            
            # 重新计算完成百分比
            if progress['total_rounds'] > 0:
                progress['completion_percentage'] = \
                    (progress['current_round'] / progress['total_rounds']) * 100
            
            current_app.logger.info(f"Returning progress data: {progress}")
            return jsonify(progress)
        
        # 如果文件不存在，返回默认值
        default_response = {
            "current_round": 0,
            "total_rounds": 0,
            "completion_percentage": 0,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stats": {
                "total_players": 0,
                "total_bets": 0.0,
                "total_payouts": 0.0,
                "jackpot_hits": 0,
                "prize_counts": {'1': 0, '2': 0, '3': 0, '4': 0},  # 使用字符串键
                "rtp": 0.0,
                "elapsed_time": "0:00:00"
            }
        }
        current_app.logger.info("Progress file not found, returning default values")
        return jsonify(default_response)
    except Exception as e:
        current_app.logger.error(f"获取进度失败: {str(e)}")
        return jsonify({"error": str(e)}), 500
def simulate_lottery(
    num_rounds: int,
    players_range: tuple[int, int],
    cards_per_player_range: tuple[int, int],
    ticket_price: float = 20.0,
    initial_jackpot: float = 30_000_000.0,
    pool_insert = 0.43,
    return_pool = 0.9
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Memory-efficient simulation of a lottery game with funding pool mechanism.

    - Numbers 1..42, pick 6 per ticket
    - Prize tiers: 1st (jackpot), 2nd-5th fixed amounts
    - Funding pool initialized at -initial_jackpot (to reflect initial injection)
    - If funding pool < 0: 10% of ticket_price repays funding pool, 5% -> jackpot pool
      Else: 15% of ticket_price -> jackpot pool
    - Jackpot rollover: if 1st prize hit, payout full jackpot pool, then inject initial_jackpot (funding_pool -= initial_jackpot)

    Returns summary, detail, and jackpot DataFrames.  Summary includes funding_pool_shortfall.
    """
    summary_records = []
    detail_buffer = deque(maxlen=10_000)
    jackpot_list = []

    # Pools
    jackpot_pool = initial_jackpot
    funding_pool = -initial_jackpot

    # Prize map for non-jackpot tiers
    prize_map = {6: None, 5: 50_000, 4: 1_500, 3: 60, 2: 20}

    for round_no in range(1, num_rounds + 1):
        # Setup round
        num_players = random.randint(*players_range)
        total_cards = 0
        winning_nums = set(random.sample(range(1, 43), 6))
        winning_str = ",".join(map(str, sorted(winning_nums)))
        tier_counts = {tier: 0 for tier in prize_map}
        tier_totals = {tier: 0.0 for tier in prize_map}
        total_bet_amount = 0.0
        current_jackpots = []

        # Betting and contributions
        for player_id in range(1, num_players + 1):
            num_cards = random.randint(*cards_per_player_range)
            total_cards += num_cards
            for card_idx in range(1, num_cards + 1):
                total_bet_amount += ticket_price
                # Contribution split
                if funding_pool < 0:
                   total_insert = ticket_price * pool_insert      # 43% 的投入
                   max_repay    = -funding_pool                   # 最多还到 0 的债务量
                   repay_amount = min(total_insert * return_pool, max_repay)
                   # 剩余部分都进奖池
                   jackpot_contrib = total_insert - repay_amount
                
                   funding_pool  += repay_amount
                   jackpot_pool   += jackpot_contrib
                else:
                   # 债务清完后，43% 全部进奖池
                   jackpot_pool += ticket_price * pool_insert

                # Ticket evaluation
                ticket_nums = set(random.sample(range(1, 43), 6))
                ticket_str = ",".join(map(str, sorted(ticket_nums)))
                matches = len(ticket_nums & winning_nums)
                prize = 0.0
                prize_tier = None
                if 2 <= matches < 6:
                    prize = prize_map[matches]
                    prize_tier = matches
                    tier_counts[matches] += 1
                    tier_totals[matches] += prize

                # Record detail
                bet = {
                    "round": round_no,
                    "player_id": player_id,
                    "card_id": f"P{player_id:04d}_C{card_idx:04d}",
                    "ticket_numbers": ticket_str,
                    "winning_numbers": winning_str,
                    "bet_amount": ticket_price,
                    "matches": matches,
                    "prize_tier": prize_tier,
                    "prize_amount": prize,
                }
                detail_buffer.append(bet)
                if matches == 6:
                    current_jackpots.append(bet)

        # Snapshot pools before payout
        jackpot_after = jackpot_pool
        funding_shortfall = funding_pool

        # Jackpot payout
        if current_jackpots:
            share = jackpot_after / len(current_jackpots)
            for bet in current_jackpots:
                bet["prize_amount"] = share
                bet["prize_tier"] = 6
                jackpot_list.append(bet)
            tier_counts[6] = len(current_jackpots)
            tier_totals[6] = jackpot_after
            # Reset jackpot pool and inject funding
            jackpot_pool = initial_jackpot
            funding_pool -= initial_jackpot

        # Record summary
        total_payout = sum(tier_totals.values())
        rtp = total_payout / total_bet_amount if total_bet_amount else 0
        summary_records.append({
            "round": round_no,
            "game_result": winning_str,
            "num_players": num_players,
            "total_bet_amount": total_bet_amount,
            "total_cards": total_cards,
            "jackpot_after": jackpot_after,
            "funding_pool_shortfall": funding_shortfall,
            "total_payout": total_payout,
            "1st_count": tier_counts[6],
            "1st_amount": tier_totals[6],
            "2nd_count": tier_counts[5],
            "2nd_amount": tier_totals[5],
            "3rd_count": tier_counts[4],
            "3rd_amount": tier_totals[4],
            "4th_count": tier_counts[3],
            "4th_amount": tier_totals[3],
            "5th_count": tier_counts[2],
            "5th_amount": tier_totals[2],
            "RTP": rtp,
        })

    # Build DataFrames
    summary_df = pd.DataFrame(summary_records)
    detail_df = pd.DataFrame(list(detail_buffer))
    jackpot_df = pd.DataFrame(jackpot_list)
    return summary_df, detail_df, jackpot_df

@app.route('/simulate', methods=['POST'])
def start_simulation():
    return simulate()

def cleanup_progress():
    """清理进度文件"""
    try:
        if os.path.exists('progress.json'):
            os.remove('progress.json')
    except Exception as e:
        current_app.logger.error(f"清理进度文件失败: {str(e)}")

@app.errorhandler(Exception)
def handle_error(e):
    cleanup_progress()
    return jsonify({"status": "error", "message": str(e)}), 500

def cleanup_on_exit():
    cleanup_progress()

atexit.register(cleanup_on_exit)

if __name__ == '__main__':
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    app.run(debug=True, threaded=True, port=5000)

# 奖级设置
PRIZE_LEVELS = {
    1: {'match': 6, 'prize': 5000000},  # 一等奖
    2: {'match': 5, 'prize': 3000},     # 二等奖
    3: {'match': 4, 'prize': 200},      # 三等奖
    4: {'match': 3, 'prize': 10},       # 四等奖
}

def get_prize_level(matches):
    """根据匹配数确定奖级"""
    if matches == 6:
        return 1
    elif matches == 5:
        return 2
    elif matches == 4:
        return 3
    elif matches == 3:
        return 4
    return 0  # 未中奖

def count_matches(ticket_numbers, winning_numbers):
    """计算匹配数"""
    return len(set(ticket_numbers) & set(winning_numbers))

def generate_ticket_numbers():
    """生成一注彩票号码"""
    return sorted(random.sample(range(1, 43), 6))

def cleanup_memory():
    """强制进行垃圾回收并压缩内存"""
    gc.collect()
    if hasattr(gc, 'garbage'):
        del gc.garbage[:]

def run_simulation_batch(batch_rounds):
    try:
        results = {
            'total_players': 0,
            'total_bets': 0.0,
            'total_payouts': 0.0,
            'jackpot_hits': 0,
            'prize_counts': {'1': 0, '2': 0, '3': 0, '4': 0},
            'last_round_bets': [],
            'jackpot_records': []
        }
        
        for current_round in range(batch_rounds):
            # 生成玩家数量
            players = random.randint(1, 10)
            results['total_players'] += players
            
            # 计算投注金额
            round_bets = players * BET_AMOUNT
            results['total_bets'] += round_bets
            
            # 生成中奖号码
            winning_numbers = generate_winning_numbers()
            
            # 为每个玩家生成投注号码并检查中奖
            for _ in range(players):
                player_numbers = generate_player_numbers()
                matches = check_matches(winning_numbers, player_numbers)
                
                if matches > 0:
                    prize_level = get_prize_level(matches)
                    if prize_level > 0:
                        prize_amount = PRIZE_TABLE[prize_level]
                        results['total_payouts'] += prize_amount
                        results['prize_counts'][str(prize_level)] += 1  # 使用字符串键
                        
                        if prize_level == 1:
                            results['jackpot_hits'] += 1
                            results['jackpot_records'].append({
                                'round': current_round,
                                'numbers': winning_numbers,
                                'matches': matches
                            })
            
            # 记录最后一轮的投注情况
            if current_round == batch_rounds - 1:
                results['last_round_bets'].append({
                    'players': players,
                    'total_bet': round_bets,
                    'winning_numbers': winning_numbers
                })
        
        return results
        
    except Exception as e:
        current_app.logger.error(f"批次模拟失败: {str(e)}")
        raise
    
def simulate_batch(batch_size, total_rounds, current_round):
    """
    模拟一批次的彩票游戏
    
    Args:
        batch_size: 本批次要模拟的轮数
        total_rounds: 总轮数
        current_round: 当前轮数
    
    Returns:
        batch_results: 包含本批次模拟结果的字典
    """
    print(f"开始批次模拟: batch_size={batch_size}, current_round={current_round}")
    
    batch_results = {
        'total_players': 0,
        'total_bets': 0.0,
        'total_payouts': 0.0,
        'prize_counts': {'1': 0, '2': 0, '3': 0, '4': 0},
        'rounds_data': []
    }

    try:
        for i in range(batch_size):
            # 生成本轮中奖号码
            winning_numbers = generate_random_numbers(6, 42)
            print(f"第 {current_round + i + 1} 轮中奖号码: {winning_numbers}")
            
            # 生成随机玩家数量
            is_weekend = (current_round + i) % 7 >= 5
            base_players = random.randint(100000, 150000)
            weekend_multiplier = random.uniform(1.3, 1.5) if is_weekend else 1.0
            num_players = int(base_players * weekend_multiplier)
            batch_results['total_players'] += num_players
            
            # 初始化本轮数据
            round_bets = 0.0
            round_payouts = 0.0
            round_prizes = {'1': 0, '2': 0, '3': 0, '4': 0}
            
            # 模拟每个玩家的投注
            for _ in range(num_players):
                # 玩家投注策略
                if random.random() < 0.8:
                    num_tickets = random.randint(1, 2)
                else:
                    num_tickets = random.randint(3, 10)
                
                total_bet = num_tickets * BET_AMOUNT
                round_bets += total_bet
                
                for _ in range(num_tickets):
                    # 生成玩家选号
                    player_numbers = generate_biased_numbers() if random.random() < 0.3 else generate_random_numbers(6, 42)
                    
                    # 判断中奖情况
                    matches = len(set(player_numbers) & set(winning_numbers))
                    
                    # 确定中奖等级和奖金
                    if matches == 6:
                        round_prizes['1'] += 1
                        round_payouts += PRIZE_TABLE[1]
                    elif matches == 5:
                        round_prizes['2'] += 1
                        round_payouts += PRIZE_TABLE[2]
                    elif matches == 4:
                        round_prizes['3'] += 1
                        round_payouts += PRIZE_TABLE[3]
                    elif matches == 3:
                        round_prizes['4'] += 1
                        round_payouts += PRIZE_TABLE[4]
            
            # 更新批次总计
            batch_results['total_bets'] += round_bets
            batch_results['total_payouts'] += round_payouts
            for level in ['1', '2', '3', '4']:
                batch_results['prize_counts'][level] += round_prizes[level]
            
            # 记录本轮详细数据
            round_data = {
                'round': current_round + i + 1,
                'players': num_players,
                'bets': round_bets,
                'payouts': round_payouts,
                'prizes': round_prizes,
                'rtp': round_payouts / round_bets if round_bets > 0 else 0
            }
            
            # 验证轮次数据
            try:
                validate_round_data(round_data)
                batch_results['rounds_data'].append(round_data)
                if i % 10 == 0:
                    print(f"完成第 {current_round + i + 1} 轮模拟: 玩家数={num_players}, 投注={round_bets:.2f}, 派奖={round_payouts:.2f}")
            except ValueError as e:
                print(f"轮次数据验证失败: {str(e)}")
                raise
        
        # 验证批次结果
        try:
            validate_batch_results(batch_results)
            print(f"批次模拟完成: 处理了 {batch_size} 轮, 累计玩家 {batch_results['total_players']}")
            print(f"批次统计: 总投注={batch_results['total_bets']:.2f}, 总派奖={batch_results['total_payouts']:.2f}")
            return batch_results
        except ValueError as e:
            print(f"批次结果验证失败: {str(e)}")
            raise
            
    except Exception as e:
        print(f"批次模拟出错: {str(e)}")
        raise

def ensure_stats_dir():
    """确保统计文件目录存在"""
    stats_dir = os.path.join(os.path.dirname(__file__), 'stats')
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)
    return stats_dir

def cleanup_old_stats():
    """清理旧的统计文件"""
    stats_dir = ensure_stats_dir()
    current_time = datetime.now()
    for file in os.listdir(stats_dir):
        if file.startswith('stats_') and file.endswith('.json'):
            file_path = os.path.join(stats_dir, file)
            file_time = datetime.strptime(file[6:-5], "%Y%m%d_%H%M%S")
            # 删除超过24小时的统计文件
            if (current_time - file_time).total_seconds() > 86400:
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.error(f"删除旧统计文件失败: {str(e)}")

def save_interval_stats(stats, interval_time):
    """保存阶段性统计结果"""
    try:
        stats_dir = ensure_stats_dir()
        filename = f'stats_{interval_time.strftime("%Y%m%d_%H%M%S")}.json'
        file_path = os.path.join(stats_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(convert_to_serializable(stats), f)
        cleanup_old_stats()  # 清理旧文件
    except Exception as e:
        current_app.logger.error(f"保存阶段性统计失败: {str(e)}")

def simulate():
    try:
        cleanup_progress()
        cleanup_old_stats()
        initial_memory = get_memory_usage()
        start_time = datetime.now()
        last_interval_save = start_time
        last_progress_save = start_time
        
        data = request.get_json()
        total_rounds = int(data.get('rounds', 1000))
        batch_size = 1000
        
        # 初始化进度和统计信息
        progress = {
            'current_round': 0,
            'total_rounds': total_rounds,
            'jackpot_history': [0],
            'detailed_data': [],  # 添加这行，用于存储每轮详细数据
            'stats': {
                'total_players': 0,
                'total_bets': 0.0,
                'total_payouts': 0.0,
                'jackpot_hits': 0,
                'prize_counts': {'1': 0, '2': 0, '3': 0, '4': 0},  # 使用字符串键
                'rtp': 0.0,
                'memory_usage': initial_memory,
                'elapsed_time': '0:00:00',
                'start_time': start_time.strftime("%Y-%m-%d %H:%M:%S"),
                'last_update': start_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        save_progress(progress)
        
        # 创建线程池
        with ThreadPoolExecutor(max_workers=1) as executor:
            for start in range(0, total_rounds, batch_size):
                end = min(start + batch_size, total_rounds)
                batch_rounds = end - start
                
                # 在新线程中执行批次模拟
                future = executor.submit(run_simulation_batch, batch_rounds)
                batch_results = future.result()
                
                # 验证和更新进度
                if not update_progress(progress, batch_results, batch_size, start_time):
                    print("警告：进度更新失败")
                    continue

                # 添加概率分布数据
                total_bets = progress['stats']['total_bets']
                probability_dist = {
                    'data': [{
                        'x': ['一等奖', '二等奖', '三等奖', '四等奖'],
                        'y': [
                            progress['stats']['prize_counts']['1'] / total_bets,
                            progress['stats']['prize_counts']['2'] / total_bets,
                            progress['stats']['prize_counts']['3'] / total_bets,
                            progress['stats']['prize_counts']['4'] / total_bets
                        ],
                        'type': 'bar',
                        'name': '中奖概率'
                    }],
                    'layout': {
                        'title': '各奖级中奖概率分布',
                        'xaxis': {'title': '奖级'},
                        'yaxis': {'title': '概率', 'tickformat': '.2%'}
                    }
                }

                # 添加返奖率分布数据
                rtp_dist = {
                    'data': [{
                        'x': ['一等奖', '二等奖', '三等奖', '四等奖'],
                        'y': [
                            progress['stats']['prize_counts']['1'] * PRIZE_TABLE[1] / total_bets * 100,
                            progress['stats']['prize_counts']['2'] * PRIZE_TABLE[2] / total_bets * 100,
                            progress['stats']['prize_counts']['3'] * PRIZE_TABLE[3] / total_bets * 100,
                            progress['stats']['prize_counts']['4'] * PRIZE_TABLE[4] / total_bets * 100
                        ],
                        'type': 'bar',
                        'name': '返奖率'
                    }],
                    'layout': {
                        'title': '各奖级返奖率分布',
                        'xaxis': {'title': '奖级'},
                        'yaxis': {'title': '返奖率', 'tickformat': '.1%'}
                    }
                }

                progress['stats']['charts'] = {
                    'probability_dist': probability_dist,
                    'rtp_dist': rtp_dist
                }
                
                # 更新奖级统计
                prize_counts = progress['stats']['prize_counts']
                for level in range(1, 5):
                    level_str = str(level)
                    current_count = int(prize_counts.get(level_str, 0))
                    batch_count = int(batch_results['prize_counts'].get(level_str, 0))  # 使用字符串键
                    prize_counts[level_str] = current_count + batch_count
                
                # 计算RTP
                if progress['stats']['total_bets'] > 0:
                    progress['stats']['rtp'] = float(
                        progress['stats']['total_payouts'] / progress['stats']['total_bets'] * 100
                    )
                
                # 每秒保存一次进度
                current_time = datetime.now()
                if (current_time - last_progress_save).total_seconds() >= 1:
                    save_progress(progress)
                    last_progress_save = current_time
                
                # 每10秒保存一次统计数据
                if (current_time - last_interval_save).total_seconds() >= 10:
                    elapsed = current_time - start_time
                    interval_stats = {
                        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        'elapsed_time': str(elapsed).split('.')[0],
                        'completed_rounds': end,
                        'total_rounds': total_rounds,
                        'completion_percentage': (end / total_rounds) * 100,
                        'stats': {
                            'total_players': progress['stats']['total_players'],
                            'total_bets': float(progress['stats']['total_bets']),
                            'total_payouts': float(progress['stats']['total_payouts']),
                            'jackpot_hits': progress['stats']['jackpot_hits'],
                            'prize_counts': {str(k): int(v) for k, v in progress['stats']['prize_counts'].items()},
                            'rtp': float(progress['stats']['rtp']),
                            'memory_usage': progress['stats']['memory_usage'],
                            'elapsed_time': progress['stats']['elapsed_time']
                        }
                    }
                    save_interval_stats(interval_stats, current_time)
                    last_interval_save = current_time
                
                # 执行内存清理
                if end % (batch_size * 10) == 0:
                    cleanup_memory()
                
                # 短暂暂停，避免CPU过载
                time.sleep(0.1)
        
        # 保存最终统计结果
        final_time = datetime.now()
        final_stats = {
            'timestamp': final_time.strftime("%Y-%m-%d %H:%M:%S"),
            'elapsed_time': str(final_time - start_time).split('.')[0],
            'completed_rounds': total_rounds,
            'total_rounds': total_rounds,
            'completion_percentage': 100,
            'stats': progress['stats']
        }
        save_interval_stats(final_stats, final_time)
        
        # 计算总投注数
        total_bets = progress['stats']['total_bets'] / BET_AMOUNT  # 转换为注数

        # 构建图表数据
        charts_data = {
            "probability_dist": {
                "data": [{
                    "x": ["一等奖", "二等奖", "三等奖", "四等奖"],
                    "y": [
                        progress['stats']['prize_counts']['1'] / total_bets,
                        progress['stats']['prize_counts']['2'] / total_bets,
                        progress['stats']['prize_counts']['3'] / total_bets,
                        progress['stats']['prize_counts']['4'] / total_bets
                    ],
                    "type": "bar",
                    "name": "中奖概率"
                }],
                "layout": {
                    "title": "各奖级中奖概率分布",
                    "xaxis": {"title": "奖级"},
                    "yaxis": {"title": "概率", "tickformat": ".2%"}
                }
            },
            "rtp_dist": {
                "data": [{
                    "x": ["一等奖", "二等奖", "三等奖", "四等奖"],
                    "y": [
                        progress['stats']['prize_counts']['1'] * PRIZE_TABLE[1] / progress['stats']['total_bets'] * 100,
                        progress['stats']['prize_counts']['2'] * PRIZE_TABLE[2] / progress['stats']['total_bets'] * 100,
                        progress['stats']['prize_counts']['3'] * PRIZE_TABLE[3] / progress['stats']['total_bets'] * 100,
                        progress['stats']['prize_counts']['4'] * PRIZE_TABLE[4] / progress['stats']['total_bets'] * 100
                    ],
                    "type": "bar",
                    "name": "返奖率",
                    "text": [
                        f"{progress['stats']['prize_counts']['1'] * PRIZE_TABLE[1] / progress['stats']['total_bets'] * 100:.1f}%",
                        f"{progress['stats']['prize_counts']['2'] * PRIZE_TABLE[2] / progress['stats']['total_bets'] * 100:.1f}%",
                        f"{progress['stats']['prize_counts']['3'] * PRIZE_TABLE[3] / progress['stats']['total_bets'] * 100:.1f}%",
                        f"{progress['stats']['prize_counts']['4'] * PRIZE_TABLE[4] / progress['stats']['total_bets'] * 100:.1f}%"
                    ],
                    "textposition": 'auto'
                }],
                "layout": {
                    "title": "各奖级返奖率分布",
                    "xaxis": {
                        "title": "奖级",
                        "tickangle": 0
                    },
                    "yaxis": {
                        "title": "返奖率",
                        "tickformat": ".1%",
                        "range": [0, Math.max(...[
                            progress['stats']['prize_counts']['1'] * PRIZE_TABLE[1] / progress['stats']['total_bets'] * 100,
                            progress['stats']['prize_counts']['2'] * PRIZE_TABLE[2] / progress['stats']['total_bets'] * 100,
                            progress['stats']['prize_counts']['3'] * PRIZE_TABLE[3] / progress['stats']['total_bets'] * 100,
                            progress['stats']['prize_counts']['4'] * PRIZE_TABLE[4] / progress['stats']['total_bets'] * 100
                        ]) * 1.1]
                    },
                    "margin": {
                        "l": 80,
                        "r": 20,
                        "t": 50,
                        "b": 50
                    },
                    "autosize": true,
                    "showlegend": false,
                    "bargap": 0.3
                }
            },
            "jackpot_trend": {
                "data": [{
                    "x": list(range(total_rounds + 1)),  # 包含初始0点
                    "y": progress['jackpot_history'],    # 使用累计历史数据
                    "type": "line",
                    "name": "头奖中出累计次数"
                }],
                "layout": {
                    "title": "头奖中出累计趋势",
                    "xaxis": {"title": "轮次"},
                    "yaxis": {"title": "累计次数"}
                }
            },
            "money_comparison": {
                "data": [{
                    "x": ["投注金额", "派奖金额"],
                    "y": [progress['stats']['total_bets'], progress['stats']['total_payouts']],
                    "type": "bar",
                    "name": "金额对比",
                    "text": [
                        f"¥{progress['stats']['total_bets']:,.2f}",
                        f"¥{progress['stats']['total_payouts']:,.2f}"
                    ],
                    "textposition": 'auto',
                }],
                "layout": {
                    "title": "投注与派奖金额对比",
                    "xaxis": {
                        "title": "类型",
                        "tickangle": 0
                    },
                    "yaxis": {
                        "title": "金额（元）",
                        "tickformat": ",.0f"
                    },
                    "margin": {
                        "l": 80,
                        "r": 20,
                        "t": 50,
                        "b": 50
                    },
                    "autosize": true,
                    "showlegend": false,
                    "bargap": 0.3
                }
            }
        }

        # 返回最终结果
        return jsonify({
            "status": "success",
            "message": "模拟完成",
            "elapsed_time": str(final_time - start_time).split('.')[0],
            "summary_stats": {
                "total_rounds": total_rounds,
                "avg_players": progress['stats']['total_players'] / total_rounds,
                "avg_cards": total_bets / total_rounds,
                "total_bet_amount": progress['stats']['total_bets'],
                "total_payout": progress['stats']['total_payouts'],
                "jackpot_hits": progress['stats']['jackpot_hits'],
                "average_rtp": progress['stats']['rtp']
            },
            "charts": charts_data,
            "tables": {
                "prize_stats": [
                    {
                        "prize_level": level,
                        "total_winners": progress['stats']['prize_counts'][str(level)],
                        "total_amount": progress['stats']['prize_counts'][str(level)] * PRIZE_TABLE[level],
                        "avg_winners_per_round": progress['stats']['prize_counts'][str(level)] / total_rounds,
                        "probability": progress['stats']['prize_counts'][str(level)] / total_bets,
                        "rtp": progress['stats']['prize_counts'][str(level)] * PRIZE_TABLE[level] / progress['stats']['total_bets'] * 100
                    }
                    for level in range(1, 5)
                ]
            },
            "detailed_data": progress['detailed_data']  # 添加详细数据
        })
        
    except Exception as e:
        current_app.logger.error(f"模拟过程出错: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 備註：
# 參數1
#         num_rounds=100,
#         players_range=(190000, 210000),
#         cards_per_player_range=(9, 11),
#         ticket_price=20.0,
#
# 參數2
#         num_rounds=100,
#         players_range=(490000, 510000),
#         cards_per_player_range=(9, 11),
#         ticket_price=20.0,
#
# 參數3
#         num_rounds=100,
#         players_range=(990000, 1010000),
#         cards_per_player_range=(9, 11),
#         ticket_price=20.0,
#
# 參數4
#         num_rounds=100,
#         players_range=(1990000, 2010000),
#         cards_per_player_range=(9, 11),
#         ticket_price=20.0,