from flask import Flask, render_template, request, jsonify
import numpy as np
from lottery_simulator import LotterySimulator
from report_generator import generate_report
import pandas as pd
import json
# 存储当前运行的模拟器实例
current_simulator = None

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

app = Flask(__name__)
app.config['JSON_ENCODER'] = CustomJSONEncoder

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        # 获取JSON数据
        data = request.json
        
        # 设置默认值和参数映射
        rounds = int(data.get('total_rounds', 1000))
        players = {
            'min': int(data.get('min_players', 1000)),
            'max': int(data.get('max_players', 5000))
        }
        cards = {
            'min': int(data.get('cards_min', 1)),
            'max': int(data.get('cards_max', 5))
        }
        ticket_price = float(data.get('ticket_price', 2.0))

        # 创建模拟器实例
        simulator = LotterySimulator(
            num_rounds=rounds,
            players_range=(players['min'], players['max']),
            cards_range=(cards['min'], cards['max']),
            ticket_price=ticket_price
        )
        global current_simulator
        current_simulator = simulator

        # 运行模拟
        summary_df, detail_df, jackpot_df = simulator.run_simulation()

        # 生成报告数据
        report_data = generate_report(summary_df, detail_df, jackpot_df)

        return jsonify({
            'status': 'success',
            'summary_stats': report_data['summary_stats'],
            'charts': report_data['charts'],
            'tables': report_data['tables']
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/progress')
def get_progress():
    if current_simulator is None:
        return jsonify({
            'status': 'not_running',
            'message': '没有正在运行的模拟'
        })

    progress = current_simulator.get_progress()
    if progress is None:
        return jsonify({
            'status': 'running',
            'message': '模拟正在运行，但尚未有进度数据'
        })

    # 确保所有数值都转换为Python原生类型
    stats = {
        'status': 'running',
        'data': {
            'progress': float(progress.get('progress', 0)),
            'current_round': int(progress.get('current_round', 0)),
            'total_rounds': int(progress.get('total_rounds', 0)),
            'player_count': int(progress.get('player_count', 0)),
            'total_bets': float(progress.get('total_bets', 0)),
            'total_tickets': int(progress.get('total_tickets', 0)),
            'jackpot_amount': float(progress.get('jackpot_amount', 0)),
            'total_payouts': float(progress.get('total_payouts', 0)),
            'payout_ratio': float(progress.get('payout_ratio', 0))
        }
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)