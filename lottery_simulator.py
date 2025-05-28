import numpy as np
import pandas as pd
from typing import Tuple, List
import random
import time
class LotterySimulator:
    def __init__(self, num_rounds: int, players_range: Tuple[int, int], 
                 cards_range: Tuple[int, int], ticket_price: float):
        """
        初始化彩票模拟器
        
        Args:
            num_rounds: 模拟轮次
            players_range: 玩家数量范围(最小值, 最大值)
            cards_range: 每人购买注数范围(最小值, 最大值)
            ticket_price: 单注金额
        """
        self.num_rounds = num_rounds
        self.players_range = players_range
        self.cards_range = cards_range
        self.ticket_price = ticket_price
        self.last_update_time = time.time()
        self.interim_results = []
        
        # 奖金设置
        self.prize_pool = 0
        self.base_prizes = {
            6: lambda x: max(x * 0.7, 5_000_000),  # 一等奖
            5: 3000,        # 二等奖
            4: 200,         # 三等奖
            3: 10,          # 四等奖
            2: 5,           # 五等奖
        }
        
        # 初始化奖池
        self.jackpot = 10_000_000  # 初始奖池1000万
        
    def generate_winning_numbers(self) -> List[int]:
        """生成中奖号码"""
        return random.sample(range(1, 43), 6)
    
    def generate_player_numbers(self) -> List[int]:
        """生成玩家选号"""
        return random.sample(range(1, 43), 6)
    
    def check_matches(self, player_numbers: List[int], winning_numbers: List[int]) -> int:
        """检查匹配数量"""
        return len(set(player_numbers) & set(winning_numbers))
    
    def calculate_prize(self, matches: int, total_winners: dict) -> float:
        """计算奖金"""
        if matches < 2:
            return 0
            
        if matches == 6:  # 一等奖
            prize = self.base_prizes[matches](self.jackpot)
            if total_winners[matches] > 0:
                prize = prize / total_winners[matches]
            return prize
            
        return self.base_prizes[matches]
    
    def run_simulation(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        运行模拟
        
        Returns:
            summary_df: 每轮概要数据
            detail_df: 最后一轮详细数据
            jackpot_df: 一等奖记录
        """
        summary_data = []
        jackpot_data = []
        last_round_detail = []
        
        for i, round_num in enumerate(range(1, self.num_rounds + 1)):
            # 生成本轮参数
            num_players = random.randint(*self.players_range)
            
            # 生成中奖号码
            winning_numbers = self.generate_winning_numbers()
            
            # 初始化统计数据
            total_cards = 0
            winners_count = {i: 0 for i in range(7)}
            winners_amount = {i: 0.0 for i in range(7)}
            
            # 模拟每个玩家
            for player_id in range(num_players):
                num_cards = random.randint(*self.cards_range)
                total_cards += num_cards
                
                # 生成该玩家所有投注
                for _ in range(num_cards):
                    player_numbers = self.generate_player_numbers()
                    matches = self.check_matches(player_numbers, winning_numbers)
                    winners_count[matches] += 1
                    
                    # 记录最后一轮的详细数据
                    if round_num == self.num_rounds:
                        last_round_detail.append({
                            'player_id': player_id,
                            'numbers': player_numbers,
                            'matches': matches
                        })
            
            # 计算奖金
            total_payout = 0
            for matches in range(2, 7):
                prize = self.calculate_prize(matches, winners_count)
                amount = prize * winners_count[matches]
                winners_amount[matches] = amount
                total_payout += amount
            
            # 更新奖池
            total_bet_amount = total_cards * self.ticket_price
            jackpot_contribution = total_bet_amount * 0.15
            self.jackpot = self.jackpot + jackpot_contribution - winners_amount[6]
            
            # 记录一等奖信息
            if winners_count[6] > 0:
                jackpot_data.append({
                    'round': round_num,
                    'winners': winners_count[6],
                    'prize_per_winner': winners_amount[6] / winners_count[6],
                    'total_prize': winners_amount[6],
                    'jackpot_before': self.jackpot + winners_amount[6],
                    'jackpot_after': self.jackpot
                })
            
            # 记录本轮概要数据
            summary_data.append({
                'round': round_num,
                'num_players': num_players,
                'total_cards': total_cards,
                'total_bet_amount': total_bet_amount,
                'total_payout': total_payout,
                'jackpot_before': self.jackpot + winners_amount[6],
                'jackpot_after': self.jackpot,
                '1st_count': winners_count[6],
                '2nd_count': winners_count[5],
                '3rd_count': winners_count[4],
                '4th_count': winners_count[3],
                '5th_count': winners_count[2],
                '1st_amount': winners_amount[6],
                '2nd_amount': winners_amount[5],
                '3rd_amount': winners_amount[4],
                '4th_amount': winners_amount[3],
                '5th_amount': winners_amount[2]
            })
            
            # 检查是否需要更新进度（每5分钟）
            current_time = time.time()
            if current_time - self.last_update_time >= 60:  # 60秒 = 1分钟
                interim_summary = self.generate_interim_summary(summary_data)
                self.interim_results.append(interim_summary)
                self.last_update_time = current_time
        
        # 转换为DataFrame
        summary_df = pd.DataFrame(summary_data)
        detail_df = pd.DataFrame(last_round_detail)
        jackpot_df = pd.DataFrame(jackpot_data)
        
        return summary_df, detail_df, jackpot_df
        
    def generate_interim_summary(self, results):
        """生成中间结果摘要"""
        df = pd.DataFrame(results)
        total_bet_amount = df['total_bet_amount'].sum()
        total_payout = df['total_payout'].sum()
        
        summary = {
            'progress': (len(df) / self.num_rounds) * 100,
            'current_round': len(df),
            'total_rounds': self.num_rounds,
            'player_count': int(df['num_players'].mean()),
            'total_bets': float(total_bet_amount),
            'total_tickets': int(df['total_cards'].sum()),
            'jackpot_amount': float(self.jackpot),
            'total_payouts': float(total_payout),
            'payout_ratio': float((total_payout / total_bet_amount) * 100) if total_bet_amount > 0 else 0
        }
        return summary

    def get_progress(self):
        """获取当前进度"""
        if not self.interim_results:
            return None
        return self.interim_results[-1]