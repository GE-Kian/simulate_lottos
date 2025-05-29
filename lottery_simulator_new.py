# -*- coding: utf-8 -*-
import random
import pandas as pd
from datetime import datetime
from collections import deque
from typing import Dict, List, Tuple, Any
import json

class LotterySimulator:
    def __init__(
        self,
        num_rounds: int = 100,
        players_range: tuple = (490000, 510000),
        cards_per_player_range: tuple = (9, 11),
        ticket_price: float = 20.0,
        initial_jackpot: float = 30_000_000.0,
        pool_insert: float = 0.43,
        return_pool: float = 0.9
    ):
        self.num_rounds = num_rounds
        self.players_range = players_range
        self.cards_per_player_range = cards_per_player_range
        self.ticket_price = ticket_price
        self.initial_jackpot = initial_jackpot
        self.pool_insert = pool_insert
        self.return_pool = return_pool
        
        # 奖池初始化
        self.jackpot_pool = initial_jackpot
        self.funding_pool = -initial_jackpot
        
        # 奖金设置
        self.prize_map = {6: None, 5: 50_000, 4: 1_500, 3: 60, 2: 20}
        
        # 数据存储
        self.summary_records = []
        self.detail_buffer = deque(maxlen=10_000)  # 限制详细记录数量
        self.jackpot_list = []

    def generate_winning_numbers(self) -> set:
        """生成中奖号码"""
        return set(random.sample(range(1, 43), 6))

    def generate_ticket_numbers(self) -> set:
        """生成投注号码"""
        return set(random.sample(range(1, 43), 6))

    def process_ticket(self, round_no: int, player_id: int, card_idx: int, 
                      winning_nums: set, winning_str: str) -> dict:
        """处理单张彩票"""
        ticket_nums = self.generate_ticket_numbers()
        ticket_str = ",".join(map(str, sorted(ticket_nums)))
        matches = len(ticket_nums & winning_nums)
        
        prize = 0.0
        prize_tier = None
        if 2 <= matches < 6:
            prize = self.prize_map[matches]
            prize_tier = matches
            
        return {
            "round": round_no,
            "player_id": player_id,
            "card_id": f"P{player_id:04d}_C{card_idx:04d}",
            "ticket_numbers": ticket_str,
            "winning_numbers": winning_str,
            "bet_amount": self.ticket_price,
            "matches": matches,
            "prize_tier": prize_tier,
            "prize_amount": prize,
        }

    def process_round(self, round_no: int) -> Dict[str, Any]:
        """处理单轮游戏"""
        num_players = random.randint(*self.players_range)
        total_cards = 0
        winning_nums = self.generate_winning_numbers()
        winning_str = ",".join(map(str, sorted(winning_nums)))
        
        tier_counts = {tier: 0 for tier in self.prize_map}
        tier_totals = {tier: 0.0 for tier in self.prize_map}
        total_bet_amount = 0.0
        current_jackpots = []

        # 处理每个玩家的投注
        for player_id in range(1, num_players + 1):
            num_cards = random.randint(*self.cards_per_player_range)
            total_cards += num_cards
            
            for card_idx in range(1, num_cards + 1):
                total_bet_amount += self.ticket_price
                
                # 资金分配
                if self.funding_pool < 0:
                    total_insert = self.ticket_price * self.pool_insert
                    max_repay = -self.funding_pool
                    repay_amount = min(total_insert * self.return_pool, max_repay)
                    jackpot_contrib = total_insert - repay_amount
                    
                    self.funding_pool += repay_amount
                    self.jackpot_pool += jackpot_contrib
                else:
                    self.jackpot_pool += self.ticket_price * self.pool_insert

                # 处理彩票
                bet = self.process_ticket(round_no, player_id, card_idx, winning_nums, winning_str)
                
                if bet["matches"] >= 2:
                    tier_counts[bet["matches"]] += 1
                    if bet["matches"] < 6:
                        tier_totals[bet["matches"]] += bet["prize_amount"]
                
                if bet["matches"] == 6:
                    current_jackpots.append(bet)
                
                self.detail_buffer.append(bet)

        # 处理头奖
        jackpot_after = self.jackpot_pool
        funding_shortfall = self.funding_pool
        
        if current_jackpots:
            share = jackpot_after / len(current_jackpots)
            for bet in current_jackpots:
                bet["prize_amount"] = share
                bet["prize_tier"] = 6
                self.jackpot_list.append(bet)
            
            tier_counts[6] = len(current_jackpots)
            tier_totals[6] = jackpot_after
            
            # 重置奖池
            self.jackpot_pool = self.initial_jackpot
            self.funding_pool -= self.initial_jackpot

        # 计算总派彩和返奖率
        total_payout = sum(tier_totals.values())
        rtp = total_payout / total_bet_amount if total_bet_amount else 0

        # 记录本轮摘要
        round_summary = {
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
        }
        
        self.summary_records.append(round_summary)
        return round_summary

    def run_simulation(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """运行完整模拟"""
        start_time = datetime.now()
        print(f"开始模拟: {start_time}")
        
        for round_no in range(1, self.num_rounds + 1):
            self.process_round(round_no)
            if round_no % 10 == 0:
                print(f"已完成 {round_no} 轮模拟")
        
        end_time = datetime.now()
        print(f"模拟结束: {end_time}")
        print(f"总耗时: {end_time - start_time}")
        
        # 转换为DataFrame
        summary_df = pd.DataFrame(self.summary_records)
        detail_df = pd.DataFrame(list(self.detail_buffer))
        jackpot_df = pd.DataFrame(self.jackpot_list)
        
        return summary_df, detail_df, jackpot_df

    def get_simulation_results(self) -> dict:
        """获取模拟结果的JSON格式"""
        if not self.summary_records:
            return {"status": "error", "message": "No simulation data available"}
        
        # 计算总体统计
        summary_df = pd.DataFrame(self.summary_records)
        total_bets = summary_df['total_bet_amount'].sum()
        total_payouts = summary_df['total_payout'].sum()
        overall_rtp = total_payouts / total_bets if total_bets else 0
        
        # 计算每个奖级的统计数据
        prize_stats = []
        for tier in range(2, 7):
            count_col = f"{tier}st_count" if tier == 1 else f"{tier}nd_count" if tier == 2 else f"{tier}rd_count" if tier == 3 else f"{tier}th_count"
            amount_col = f"{tier}st_amount" if tier == 1 else f"{tier}nd_amount" if tier == 2 else f"{tier}rd_amount" if tier == 3 else f"{tier}th_amount"
            
            total_winners = summary_df[count_col].sum()
            total_prize_amount = summary_df[amount_col].sum()
            avg_winners = total_winners / len(summary_df) if len(summary_df) > 0 else 0
            
            prize_stats.append({
                "prize_level": tier,
                "total_winners": int(total_winners),
                "total_prize_amount": float(total_prize_amount),
                "avg_winners_per_round": float(avg_winners)
            })
        
        # 准备图表数据
        charts = {
            "money_comparison": {
                "data": [
                    {
                        "name": "投注金额",
                        "x": summary_df['round'].tolist(),
                        "y": summary_df['total_bet_amount'].tolist()
                    },
                    {
                        "name": "派彩金额",
                        "x": summary_df['round'].tolist(),
                        "y": summary_df['total_payout'].tolist()
                    }
                ]
            },
            "jackpot_trend": {
                "data": [
                    {
                        "name": "奖池金额",
                        "x": summary_df['round'].tolist(),
                        "y": summary_df['jackpot_after'].tolist()
                    }
                ]
            },
            "players_trend": {
                "data": [
                    {
                        "name": "玩家数量",
                        "x": summary_df['round'].tolist(),
                        "y": summary_df['num_players'].tolist()
                    }
                ]
            }
        }
        
        return {
            "status": "success",
            "summary_stats": {
                "total_rounds": len(summary_df),
                "total_bet_amount": float(total_bets),
                "total_payout": float(total_payouts),
                "overall_rtp": float(overall_rtp),
                "avg_bet_amount": float(total_bets / len(summary_df)) if len(summary_df) > 0 else 0,
                "avg_players": float(summary_df['num_players'].mean())
            },
            "tables": {
                "prize_stats": prize_stats
            },
            "charts": charts
        }

if __name__ == "__main__":
    # 设置模拟参数
    simulator = LotterySimulator(
        num_rounds=100,
        players_range=(490000, 510000),
        cards_per_player_range=(9, 11),
        ticket_price=20.0
    )
    
    # 运行模拟
    summary_df, detail_df, jackpot_df = simulator.run_simulation()
    
    # 保存结果
    summary_df.to_csv("summary.csv", index=False)
    detail_df.to_csv("last_bets.csv", index=False)
    jackpot_df.to_csv("jackpot_bets.csv", index=False)
    
    # 获取JSON格式的结果
    results = simulator.get_simulation_results()
    with open("simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)
