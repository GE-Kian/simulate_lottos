
import random
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict

def generate_random_numbers() -> List[int]:
    """生成一组6个不重复的随机数（1-42）"""
    return random.sample(range(1, 43), 6)

def calculate_matches(ticket: List[int], winning_numbers: List[int]) -> int:
    """计算匹配的数字数量"""
    return len(set(ticket) & set(winning_numbers))

def calculate_prize(matches: int, jackpot: float, total_cards: int) -> float:
    """根据匹配数计算奖金"""
    prize_structure = {
        6: ('jackpot', 0.75),  # 头奖，奖池的75%
        5: ('fixed', 3000),    # 二等奖，固定3000
        4: ('fixed', 200),     # 三等奖，固定200
        3: ('fixed', 50),      # 四等奖，固定50
        2: ('fixed', 5),       # 五等奖，固定5
    }
    
    if matches not in prize_structure:
        return 0
    
    prize_type, value = prize_structure[matches]
    if prize_type == 'jackpot':
        return jackpot * value
    else:
        return value

def simulate_lottery(num_rounds: int = 100,
                    players_range: Tuple[int, int] = (490000, 510000),
                    cards_per_player_range: Tuple[int, int] = (9, 11),
                    ticket_price: float = 20.0,
                    initial_jackpot: float = 10000000.0) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    模拟多轮彩票开奖
    
    Args:
        num_rounds: 模拟轮数
        players_range: 玩家数量范围
        cards_per_player_range: 每个玩家购买彩票数量范围
        ticket_price: 每张彩票价格
        initial_jackpot: 初始奖池金额
    
    Returns:
        Tuple[DataFrame, DataFrame, DataFrame]: 
            - 每轮概要数据
            - 最后一轮详细投注数据
            - 中头奖记录
    """
    summary_data = []
    jackpot_winners = []
    current_jackpot = initial_jackpot
    
    for round_num in range(1, num_rounds + 1):
        # 生成本轮玩家数和中奖号码
        num_players = random.randint(*players_range)
        winning_numbers = generate_random_numbers()
        
        # 初始化本轮统计数据
        round_stats = {
            'round': round_num,
            'num_players': num_players,
            'winning_numbers': winning_numbers,
            'jackpot_before': current_jackpot,
            'total_cards': 0,
            'total_bet_amount': 0,
            'total_payout': 0
        }
        
        # 初始化各奖级统计
        for i in range(1, 7):
            round_stats[f'{i}th_count'] = 0
            round_stats[f'{i}th_amount'] = 0
        
        # 存储最后一轮的详细投注数据
        last_round_bets = [] if round_num == num_rounds else None
        
        # 模拟每个玩家的投注
        for player_id in range(num_players):
            num_cards = random.randint(*cards_per_player_range)
            round_stats['total_cards'] += num_cards
            round_stats['total_bet_amount'] += num_cards * ticket_price
            
            # 处理每张彩票
            for card_id in range(num_cards):
                ticket = generate_random_numbers()
                matches = calculate_matches(ticket, winning_numbers)
                prize = calculate_prize(matches, current_jackpot, round_stats['total_cards'])
                
                # 更新奖级统计
                if matches >= 2:
                    tier = 7 - matches  # 6匹配=1等奖，5匹配=2等奖，以此类推
                    round_stats[f'{tier}th_count'] += 1
                    round_stats[f'{tier}th_amount'] += prize
                
                # 记录头奖信息
                if matches == 6:
                    jackpot_winners.append({
                        'round': round_num,
                        'player_id': player_id,
                        'card_id': card_id,
                        'ticket': ticket,
                        'prize': prize
                    })
                
                # 存储最后一轮的详细数据
                if last_round_bets is not None:
                    last_round_bets.append({
                        'player_id': player_id,
                        'card_id': card_id,
                        'ticket': ticket,
                        'matches': matches,
                        'prize': prize
                    })
        
        # 计算总派奖金额
        round_stats['total_payout'] = sum(round_stats[f'{i}th_amount'] for i in range(1, 7))
        
        # 更新奖池
        pool_contribution = round_stats['total_bet_amount'] * 0.5  # 50%投注额进入奖池
        current_jackpot = current_jackpot + pool_contribution - round_stats['1th_amount']
        round_stats['jackpot_after'] = current_jackpot
        
        summary_data.append(round_stats)
    
    # 转换为DataFrame
    summary_df = pd.DataFrame(summary_data)
    detail_df = pd.DataFrame(last_round_bets) if last_round_bets else pd.DataFrame()
    jackpot_df = pd.DataFrame(jackpot_winners)
    
    return summary_df, detail_df, jackpot_df