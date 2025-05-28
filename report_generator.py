import pandas as pd
import numpy as np

def generate_report(summary_df: pd.DataFrame, detail_df: pd.DataFrame, jackpot_df: pd.DataFrame) -> dict:
    """
    生成模拟报告数据
    
    Args:
        summary_df: 每轮概要数据
        detail_df: 最后一轮详细数据
        jackpot_df: 一等奖记录
        
    Returns:
        包含统计数据、图表数据和表格数据的字典
    """
    # 计算基础统计数据
    summary_stats = {
        'total_rounds': len(summary_df),
        'avg_players': summary_df['num_players'].mean(),
        'avg_cards': summary_df['total_cards'].mean() / summary_df['num_players'].mean(),
        'total_bet_amount': summary_df['total_bet_amount'].sum(),
        'total_payout': summary_df['total_payout'].sum(),
        'jackpot_hits': summary_df['1st_count'].sum(),
        'average_rtp': (summary_df['total_payout'].sum() / summary_df['total_bet_amount'].sum()) * 100
    }
    
    # 生成奖池变化趋势图数据
    jackpot_trend = {
        'data': [{
            'x': summary_df['round'].tolist(),
            'y': summary_df['jackpot_after'].tolist(),
            'type': 'scatter',
            'mode': 'lines',
            'name': '奖池金额',
            'line': {'color': 'rgb(55, 83, 109)'}
        }],
        'layout': {
            'title': '奖池金额变化趋势',
            'xaxis': {'title': '轮次'},
            'yaxis': {'title': '金额（元）'},
            'showlegend': True
        }
    }
    
    # 生成投注和派奖金额对比图数据
    money_comparison = {
        'data': [
            {
                'x': summary_df['round'].tolist(),
                'y': summary_df['total_bet_amount'].tolist(),
                'type': 'scatter',
                'mode': 'lines',
                'name': '总投注金额',
                'line': {'color': 'rgb(26, 118, 255)'}
            },
            {
                'x': summary_df['round'].tolist(),
                'y': summary_df['total_payout'].tolist(),
                'type': 'scatter',
                'mode': 'lines',
                'name': '总派奖金额',
                'line': {'color': 'rgb(219, 64, 82)'}
            }
        ],
        'layout': {
            'title': '投注和派奖金额对比',
            'xaxis': {'title': '轮次'},
            'yaxis': {'title': '金额（元）'},
            'showlegend': True
        }
    }
    
    # 计算各奖级统计数据
    prize_stats = []
    for i, prize_level in enumerate(['1st', '2nd', '3rd', '4th', '5th'], 1):
        count_col = f'{prize_level}_count'
        amount_col = f'{prize_level}_amount'
        total_winners = summary_df[count_col].sum()
        total_amount = summary_df[amount_col].sum()
        
        prize_stats.append({
            'prize_level': i,
            'total_winners': int(total_winners),
            'total_amount': float(total_amount),
            'avg_winners_per_round': float(total_winners / len(summary_df)),
            'probability': float(total_winners / summary_df['total_cards'].sum()),
            'rtp': float(total_amount / summary_df['total_bet_amount'].sum() * 100)
        })
    
    # 整合所有数据
    report_data = {
        'summary_stats': summary_stats,
        'charts': {
            'jackpot_trend': jackpot_trend,
            'money_comparison': money_comparison
        },
        'tables': {
            'prize_stats': prize_stats
        }
    }
    
    # 确保所有数值都是Python原生类型
    def convert_to_native_types(obj):
        if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        if isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, dict):
            return {key: convert_to_native_types(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [convert_to_native_types(item) for item in obj]
        return obj

    # 转换所有数据为Python原生类型
    report_data = convert_to_native_types(report_data)
    
    return report_data