$(document).ready(function() {
    let progressTimer = null;
    $('#simulationForm').on('submit', function(e) {
        e.preventDefault();
        
        $('#loadingIndicator').show();
        $('#results').hide();
        
        const formData = {
            rounds: $('#num_rounds').val(),
            players_min: $('#players_min').val(),
            players_max: $('#players_max').val(),
            cards_min: $('#cards_min').val(),
            cards_max: $('#cards_max').val(),
            ticket_price: $('#ticket_price').val()
        };
        
        $('#progressInfo').empty();
        startProgressCheck();
        
        $.ajax({
            url: '/simulate',
            method: 'POST',
            data: formData,
            success: function(response) {
                if (response.status === 'success') {
                    $('#loadingIndicator').hide();
                    $('#results').show();

                    // 更新统计数据
                    updateSummaryStats(response.summary_stats);

                    // 添加数据验证和错误处理
                    console.log('Response charts data:', response.charts);

                    // 绘制所有图表
                    if (response.charts) {
                        try {
                            // 绘制概率分布图
                            if (response.charts.probability_dist) {
                                console.log('Drawing probability chart:', response.charts.probability_dist);
                                Plotly.newPlot('probabilityChart', response.charts.probability_dist.data, response.charts.probability_dist.layout)
                                    .then(() => console.log('Probability chart drawn successfully'))
                                    .catch(err => console.error('Error drawing probability chart:', err));
                            } else {
                                console.warn('No probability distribution data available');
                            }
                            
                            // 绘制返奖率分布图
                            if (response.charts.rtp_dist) {
                                console.log('Drawing RTP chart:', response.charts.rtp_dist);
                                Plotly.newPlot('rtpChart', response.charts.rtp_dist.data, response.charts.rtp_dist.layout)
                                    .then(() => console.log('RTP chart drawn successfully'))
                                    .catch(err => console.error('Error drawing RTP chart:', err));
                            } else {
                                console.warn('No RTP distribution data available');
                            }
                            
                            // 绘制其他图表
                            if (response.charts.jackpot_trend) {
                                console.log('Drawing jackpot trend chart:', response.charts.jackpot_trend);
                                Plotly.newPlot('jackpotTrendChart', response.charts.jackpot_trend.data, response.charts.jackpot_trend.layout)
                                    .then(() => console.log('Jackpot trend chart drawn successfully'))
                                    .catch(err => console.error('Error drawing jackpot trend chart:', err));
                            } else {
                                console.warn('No jackpot trend data available');
                            }
                            
                            if (response.charts.money_comparison) {
                                console.log('Drawing money comparison chart:', response.charts.money_comparison);
                                Plotly.newPlot('moneyComparisonChart', response.charts.money_comparison.data, response.charts.money_comparison.layout)
                                    .then(() => console.log('Money comparison chart drawn successfully'))
                                    .catch(err => console.error('Error drawing money comparison chart:', err));
                            } else {
                                console.warn('No money comparison data available');
                            }
                        } catch (error) {
                            console.error('Error in chart drawing:', error);
                            alert('图表绘制过程中发生错误，请查看控制台了解详情');
                        }
                    } else {
                        console.error('No charts data in response');
                    }

                    // 更新奖级统计表格
                    updatePrizeStats(response.tables.prize_stats);
                } else {
                    console.error('Response status is not success:', response);
                    alert('模拟结果获取失败，请查看控制台了解详情');
                }
            },
            error: function(xhr, status, error) {
                console.error('AJAX request failed:', {xhr, status, error});
                $('#loadingIndicator').hide();
                alert('请求失败：' + error);
            }
        });
    });
});
    
// 更新统计数据
function updateSummaryStats(stats) {
    $('#totalRounds').text(stats.total_rounds.toLocaleString());
    $('#avgPlayers').text(stats.avg_players.toFixed(2));
    $('#avgCards').text(stats.avg_cards.toFixed(2));
    $('#totalBetAmount').text(stats.total_bet_amount.toLocaleString('zh-CN', {
        style: 'currency',
        currency: 'CNY'
    }));
    $('#totalPayout').text(stats.total_payout.toLocaleString('zh-CN', {
        style: 'currency',
        currency: 'CNY'
    }));
    $('#jackpotHits').text(stats.jackpot_hits);
    $('#averageRTP').text(stats.average_rtp.toFixed(2) + '%');
}

// 绘制图表
function drawCharts(chartData) {
    // 绘制奖池变化趋势图
    Plotly.newPlot('jackpotTrendChart', chartData.jackpot_trend.data, chartData.jackpot_trend.layout);
    
    // 绘制投注和派奖金额对比图
    Plotly.newPlot('moneyComparisonChart', chartData.money_comparison.data, chartData.money_comparison.layout);
    
    // 如果有最后一轮中奖分布数据，则绘制
    if (chartData.last_round_dist) {
        Plotly.newPlot('lastRoundDistChart', chartData.last_round_dist.data, chartData.last_round_dist.layout);
    }

    // 绘制概率分布图
    if (chartData.probability_dist) {
        Plotly.newPlot('probabilityChart', chartData.probability_dist.data, chartData.probability_dist.layout);
    }

    // 绘制返奖率分布图
    if (chartData.rtp_dist) {
        Plotly.newPlot('rtpChart', chartData.rtp_dist.data, chartData.rtp_dist.layout);
    }
}

// 更新奖级统计表格
function updatePrizeStats(prizeStats) {
    const tbody = $('#prizeStatsTable tbody');
    tbody.empty();
    
    prizeStats.forEach(function(stat) {
        const row = $('<tr>');
        row.append($('<td>').text(stat.prize_level + '等奖'));
        row.append($('<td>').text(stat.total_winners.toLocaleString()));
        row.append($('<td>').text(stat.total_amount.toLocaleString('zh-CN', {
            style: 'currency',
            currency: 'CNY'
        })));
        row.append($('<td>').text(stat.avg_winners_per_round.toFixed(2)));
        row.append($('<td>').text((stat.probability * 100).toFixed(6) + '%'));
        row.append($('<td>').text(stat.rtp.toFixed(2) + '%'));
        tbody.append(row);
    });
}
    
// 创建概率分布图
function createProbabilityChart(data) {
    const trace = {
        x: data.tiers,
        y: data.probabilities,
        type: 'bar',
        name: '中奖概率',
        marker: {
            color: 'rgb(55, 83, 109)'
        }
    };
    
    const layout = {
        title: '各奖级中奖概率分布',
        height: 400,
        margin: { t: 30, b: 30, l: 50, r: 20 },
        xaxis: { title: '奖级' },
        yaxis: { 
            title: '概率',
            tickformat: '.2%'
        },
        showlegend: true,
        legend: { y: 1.0 },
        bargap: 0.1
    };
    
    Plotly.newPlot('probabilityChart', [trace], layout);
}

// 创建RTP分布图
function createRTPChart(data) {
    const trace = {
        x: data.tiers,
        y: data.rtp_values,
        type: 'bar',
        name: '返奖率',
        marker: {
            color: 'rgb(26, 118, 255)'
        }
    };
    
    const layout = {
        title: '各奖级返奖率分布',
        height: 400,
        margin: { t: 30, b: 30, l: 50, r: 20 },
        xaxis: { title: '奖级' },
        yaxis: { 
            title: '返奖率',
            tickformat: '.1%'
        },
        showlegend: true,
        legend: { y: 1.0 },
        bargap: 0.1
    };
    
    Plotly.newPlot('rtpChart', [trace], layout);
}

// 创建奖池变化图
function createJackpotChart(data) {
    const trace = {
        x: data.rounds,
        y: data.amounts,
        type: 'line',
        name: '奖池金额',
        line: {
            color: 'rgb(219, 64, 82)',
            width: 2
        }
    };
    
    const layout = {
        title: '奖池金额变化趋势',
        height: 400,
        margin: { t: 30, b: 30, l: 50, r: 20 },
        xaxis: { 
            title: '轮次',
            showgrid: true
        },
        yaxis: { 
            title: '金额',
            tickformat: ',.0f'
        },
        showlegend: true,
        legend: { y: 1.0 }
    };
    
    Plotly.newPlot('jackpotChart', [trace], layout);
}

function startProgressCheck() {
    progressTimer = setInterval(checkProgress, 30000);  // 每30秒检查一次
}

function stopProgressCheck() {
    if (progressTimer) {
        clearInterval(progressTimer);
        progressTimer = null;
    }
}

function checkProgress() {
    $.ajax({
        url: '/progress',
        method: 'GET',
        success: function(response) {
            if (response.status === 'running' && response.data) {
                updateProgressDisplay(response.data);
            } else if (response.status === 'not_running') {
                stopProgressCheck();
            }
        },
        error: function(xhr, status, error) {
            console.error('进度查询失败：', error);
        }
    });
}

function updateProgressDisplay(progress) {
    const stats = progress.current_stats;
    const completionRate = (progress.completed_rounds / progress.total_rounds * 100).toFixed(1);
    
    // 更新进度信息
    $('#progressInfo').html(`
        <div class="alert alert-info">
            <h4>模拟进度：${completionRate}%</h4>
            <p>已完成轮次：${progress.completed_rounds} / ${progress.total_rounds}</p>
            <p>当前统计：</p>
            <ul>
                <li>平均玩家数：${stats.avg_players.toFixed(2)}</li>
                <li>总投注金额：￥${stats.total_bet_amount.toLocaleString()}</li>
                <li>总派奖金额：￥${stats.total_payout.toLocaleString()}</li>
                <li>一等奖中奖次数：${stats.jackpot_hits}</li>
                <li>当前返奖率：${stats.current_rtp.toFixed(2)}%</li>
            </ul>
        </div>
    `);
}