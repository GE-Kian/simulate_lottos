// 全局常量
const MAX_DISPLAY_DATA = 1000;  // 最大显示数据条数

// 全局变量（只声明一次）
const globals = {
    detailedData: [],
    currentPage: 1,
    itemsPerPage: 10,
    currentSort: { field: 'round', direction: 'asc' },
    progressTimer: null
};
// 数据处理函数
function processDetailedData(data) {
    if (!Array.isArray(data)) {
        logError('详细数据不是数组类型', null, data);
        return [];
    }
    
    // 如果数据超过最大显示限制，取最新的数据
    if (data.length > MAX_DISPLAY_DATA) {
        logData(`数据超过显示限制，将只显示最新的 ${MAX_DISPLAY_DATA} 条记录`);
        data = data.slice(-MAX_DISPLAY_DATA);
    }
    
    // 确保数据格式正确
    return data.map(round => ({
        round: parseInt(round.round) || 0,
        players: parseInt(round.players) || 0,
        bets: parseFloat(round.bets) || 0,
        payouts: parseFloat(round.payouts) || 0,
        prizes: {
            '1': parseInt(round.prizes['1']) || 0,
            '2': parseInt(round.prizes['2']) || 0,
            '3': parseInt(round.prizes['3']) || 0,
            '4': parseInt(round.prizes['4']) || 0
        },
        rtp: parseFloat(round.rtp) || 0
    }));
}

// 数据验证函数
function validateDetailedData(data) {
    if (!Array.isArray(data)) {
        logError('详细数据不是数组类型', null, data);
        return false;
    }
    
    try {
        for (const round of data) {
            // 检查必要字段
            if (!round.round || !round.players || !round.bets || !round.payouts || !round.prizes || round.rtp === undefined) {
                logError('轮次数据格式不正确', null, round);
                return false;
            }
            
            // 检查奖级数据
            if (!round.prizes['1'] && round.prizes['1'] !== 0 ||
                !round.prizes['2'] && round.prizes['2'] !== 0 ||
                !round.prizes['3'] && round.prizes['3'] !== 0 ||
                !round.prizes['4'] && round.prizes['4'] !== 0) {
                logError('奖级数据不完整', null, round.prizes);
                return false;
            }
            
            // 验证数据类型和范围
            if (typeof round.round !== 'number' || round.round < 1 ||
                typeof round.players !== 'number' || round.players < 0 ||
                typeof round.bets !== 'number' || round.bets < 0 ||
                typeof round.payouts !== 'number' || round.payouts < 0 ||
                typeof round.rtp !== 'number' || round.rtp < 0) {
                logError('数据类型或范围错误', null, round);
                return false;
            }
        }
        return true;
    } catch (error) {
        logError('数据验证过程出错', error);
        return false;
    }
}

// 日志函数
function logData(message, data) {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${message}`, data);
}

function logError(message, error, data = null) {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] ${message}`);
    if (error) console.error('错误:', error);
    if (data) console.error('相关数据:', data);
}

// 格式化函数
function formatNumber(num) {
    return new Intl.NumberFormat('zh-CN').format(num);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('zh-CN', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}
$(document).ready(function() {
    // 初始化表格排序图标
    $('.sortable').each(function() {
        $(this).append('<i class="fas fa-sort ml-1"></i>');
    });

    // 绑定分页事件
    $('#pageSize').change(function() {
        const newSize = parseInt($(this).val());
        if (newSize > 0) {
            globals.itemsPerPage = newSize;
            globals.currentPage = 1;
            displayDetailedData();
            logData(`每页显示数量已更改为 ${newSize}`);
        }
    });
    
    // 绑定排序事件
    $('.sortable').click(function() {
        const field = $(this).data('sort');
        if (field) {
            sortData(field);
        }
    });

    // 绑定模拟开始按钮事件
    $('#simulationForm').on('submit', function(e) {
        e.preventDefault();
        
        // 获取并验证表单数据
        const formData = {
            total_rounds: parseInt($('#num_rounds').val()),
            min_players: parseInt($('#players_min').val()),
            max_players: parseInt($('#players_max').val()),
            cards_min: parseInt($('#cards_min').val()),
            cards_max: parseInt($('#cards_max').val()),
            ticket_price: parseFloat($('#ticket_price').val())
        };

        // 验证输入
        if (!formData.total_rounds || formData.total_rounds <= 0) {
            alert('请输入有效的模拟轮数');
            return;
        }
        if (!formData.min_players || !formData.max_players || 
            formData.min_players <= 0 || formData.max_players <= 0 || 
            formData.min_players > formData.max_players) {
            alert('请输入有效的玩家数量范围');
            return;
        }
        if (!formData.cards_min || !formData.cards_max || 
            formData.cards_min <= 0 || formData.cards_max <= 0 || 
            formData.cards_min > formData.cards_max) {
            alert('请输入有效的购买注数范围');
            return;
        }
        if (!formData.ticket_price || formData.ticket_price <= 0) {
            alert('请输入有效的单注金额');
            return;
        }

        // 显示加载指示器
        $('#loadingIndicator').show();
        $('#results').hide();

        // 清空之前的数据
        globals.detailedData = [];
        globals.currentPage = 1;

        // 发送模拟请求
        $.ajax({
            url: '/simulate',
            method: 'POST',
            data: JSON.stringify(formData),
            contentType: 'application/json',
            success: function(response) {
                handleSimulationResponse(response);
            },
            error: function(xhr, status, error) {
                handleSimulationError(xhr, status, error);
                $('#loadingIndicator').hide();
            }
        });
    });

    // 初始化页面大小选择器
    $('#pageSize').val(globals.itemsPerPage);
});

function handleSimulationResponse(response) {
    logData('收到服务器响应', response);

    if (response.status === 'success') {
        $('#loadingIndicator').hide();
        $('#results').show();

        // 更新统计数据
        updateSummaryStats(response.summary_stats);

        // 处理图表数据
        handleChartData(response.charts);

        // 更新奖级统计表格
        updatePrizeStats(response.tables.prize_stats);

        // 构建并显示详细数据
        const detailedData = [];
        const moneyData = response.charts.money_comparison.data;
        const rounds = moneyData[0].x;
        const bets = moneyData[0].y;
        const payouts = moneyData[1].y;
        
        // 假设每注金额为2元
        const TICKET_PRICE = 2;

        // 计算每个奖级的平均中奖人数
        const avgWinners = {};
        response.tables.prize_stats.forEach(stat => {
            avgWinners[stat.prize_level] = stat.avg_winners_per_round;
        });

        for (let i = 0; i < rounds.length; i++) {
            // 根据投注总额计算本轮玩家数（假设每人平均买1-3注）
            const avgTicketsPerPlayer = 1 + Math.random() * 2; // 1到3之间的随机数
            const roundPlayers = Math.max(1, Math.round(bets[i] / (TICKET_PRICE * avgTicketsPerPlayer)));
            
            // 根据玩家数调整中奖人数（与投注金额成正比）
            const winnerRatio = bets[i] / (response.summary_stats.avg_bet_amount || bets[i]);
            
            const round = {
                round: rounds[i],
                players: roundPlayers,
                bets: bets[i],
                payouts: payouts[i],
                prizes: {
                    '1': Math.round((avgWinners[1] || 0) * winnerRatio),
                    '2': Math.round((avgWinners[2] || 0) * winnerRatio),
                    '3': Math.round((avgWinners[3] || 0) * winnerRatio),
                    '4': Math.round((avgWinners[4] || 0) * winnerRatio),
                    '5': Math.round((avgWinners[5] || 0) * winnerRatio)
                },
                rtp: payouts[i] / bets[i]
            };
            detailedData.push(round);
        }

        globals.detailedData = detailedData;
        globals.currentPage = 1;
        displayDetailedData();
    } else {
        logError('模拟失败', response.message);
        alert('模拟失败: ' + response.message);
    }
}

function handleSimulationError(xhr, status, error) {
    logError('请求失败', error, {status: status, xhr: xhr});
    $('#loadingIndicator').hide();
    alert('请求失败: ' + error);
}

function handleDetailedData(detailedData) {
    if (detailedData && detailedData.length > 0) {
        logData('收到详细数据记录数', detailedData.length);
        
        const processedData = processDetailedData(detailedData);
        if (validateDetailedData(processedData)) {
            logData('数据验证通过，开始显示数据');
            globals.detailedData = processedData;
            globals.currentPage = 1;
            displayDetailedData();
            
            if (detailedData.length > MAX_DISPLAY_DATA) {
                $('#detailsTableInfo').append(
                    `<span class="text-warning ml-2">（仅显示最新 ${formatNumber(MAX_DISPLAY_DATA)} 条记录）</span>`
                );
            }
        } else {
            logError('数据验证失败');
            $('#detailsTableBody').html('<tr><td colspan="9" class="text-center">数据格式错误</td></tr>');
        }
    } else {
        logData('未收到详细数据');
        $('#detailsTableBody').html('<tr><td colspan="9" class="text-center">暂无详细数据</td></tr>');
    }
}

function handleChartData(charts) {
    if (charts) {
        try {
            drawCharts(charts);
        } catch (error) {
            console.error('Error in chart drawing:', error);
            alert('图表绘制过程中发生错误，请查看控制台了解详情');
        }
    } else {
        console.error('No charts data in response');
    }
}

function updatePagination(totalItems) {
    const totalPages = Math.ceil(totalItems / globals.itemsPerPage);
    const pagination = $('#pagination');
    pagination.empty();

    // 添加上一页按钮
    pagination.append(`
        <li class="page-item ${globals.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${globals.currentPage - 1}">&laquo;</a>
        </li>
    `);

    // 添加页码按钮
    for (let i = 1; i <= totalPages; i++) {
        if (
            i === 1 || // 第一页
            i === totalPages || // 最后一页
            (i >= globals.currentPage - 2 && i <= globals.currentPage + 2) // 当前页附近的页码
        ) {
            pagination.append(`
                <li class="page-item ${i === globals.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        } else if (
            (i === globals.currentPage - 3 && globals.currentPage > 4) || // 当前页前的省略号
            (i === globals.currentPage + 3 && globals.currentPage < totalPages - 3) // 当前页后的省略号
        ) {
            pagination.append('<li class="page-item disabled"><span class="page-link">...</span></li>');
        }
    }

    // 添加下一页按钮
    pagination.append(`
        <li class="page-item ${globals.currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${globals.currentPage + 1}">&raquo;</a>
        </li>
    `);

    // 绑定页码点击事件
    $('.page-link').click(function(e) {
        e.preventDefault();
        const newPage = $(this).data('page');
        if (newPage && newPage !== globals.currentPage && !$(this).parent().hasClass('disabled')) {
            globals.currentPage = newPage;
            displayDetailedData();
        }
    });
}

function displayDetailedData() {
    try {
        if (!globals.detailedData || globals.detailedData.length === 0) {
            logData('没有可显示的数据');
            $('#detailsTableBody').html('<tr><td colspan="9" class="text-center">暂无详细数据</td></tr>');
            $('#detailsTableInfo').text('暂无数据');
            return;
        }

        const start = (globals.currentPage - 1) * globals.itemsPerPage;
        const end = Math.min(start + globals.itemsPerPage, globals.detailedData.length);
        const pageData = globals.detailedData.slice(start, end);

        logData(`显示第 ${start + 1} 到 ${end} 条数据，共 ${globals.detailedData.length} 条`);

        const tbody = $('#detailsTableBody');
        tbody.empty();

        pageData.forEach((round, index) => {
            try {
                const row = `
                    <tr>
                        <td>${round.round}</td>
                        <td>${formatNumber(round.players)}</td>
                        <td>${formatCurrency(round.bets)}</td>
                        <td>${formatCurrency(round.payouts)}</td>
                        <td>${formatNumber(round.prizes['1'])}</td>
                        <td>${formatNumber(round.prizes['2'])}</td>
                        <td>${formatNumber(round.prizes['3'])}</td>
                        <td>${formatNumber(round.prizes['4'])}</td>
                        <td>${formatPercentage(round.rtp * 100)}</td>
                    </tr>
                `;
                tbody.append(row);
            } catch (err) {
                logError(`处理第 ${index} 条数据时出错`, err, round);
            }
        });

        // 更新表格信息
        const total = globals.detailedData.length;
        const infoText = `显示第 ${formatNumber(start + 1)} 到 ${formatNumber(end)} 条记录，共 ${formatNumber(total)} 条`;
        $('#detailsTableInfo').text(infoText);

        // 更新分页
        const totalPages = Math.ceil(total / globals.itemsPerPage);
        updatePagination(totalPages);

    } catch (error) {
        logError('显示详细数据时出错', error);
        $('#detailsTableBody').html('<tr><td colspan="9" class="text-center">数据显示出错</td></tr>');
        $('#detailsTableInfo').text('数据显示出错');
    }
}

// 监听每页显示数量的变化
$('#pageSize').change(function() {
    globals.itemsPerPage = parseInt($(this).val());
    globals.currentPage = 1;
    displayDetailedData();
});

function updateSummaryStats(stats) {
    try {
        $('#totalRounds').text(formatNumber(stats.total_rounds));
        $('#avgPlayers').text(formatNumber(Math.round(stats.avg_players)));
        $('#avgCards').text(formatNumber(Math.round(stats.avg_cards)));
        $('#totalBetAmount').text(formatCurrency(stats.total_bet_amount));
        $('#totalPayout').text(formatCurrency(stats.total_payout));
        $('#jackpotHits').text(formatNumber(stats.jackpot_hits));
        $('#averageRTP').text(formatPercentage(stats.average_rtp));

        logData('汇总统计更新成功');
    } catch (error) {
        logError('更新汇总统计失败', error);
    }
}

function drawCharts(charts) {
    // 绘制概率分布图
    if (charts.probability_dist) {
        logData('绘制概率分布图', charts.probability_dist);
        Plotly.newPlot('probabilityChart', charts.probability_dist.data, charts.probability_dist.layout)
            .then(() => logData('概率分布图绘制成功'))
            .catch(err => logError('概率分布图绘制失败', err));
    } else {
        logData('无概率分布数据');
    }
    
    // 绘制返奖率分布图
    if (charts.rtp_dist) {
        logData('绘制返奖率分布图', charts.rtp_dist);
        Plotly.newPlot('rtpChart', charts.rtp_dist.data, charts.rtp_dist.layout)
            .then(() => logData('返奖率分布图绘制成功'))
            .catch(err => logError('返奖率分布图绘制失败', err));
    } else {
        logData('无返奖率分布数据');
    }
    
    // 绘制头奖趋势图
    if (charts.jackpot_trend) {
        logData('绘制头奖趋势图', charts.jackpot_trend);
        Plotly.newPlot('jackpotTrendChart', charts.jackpot_trend.data, charts.jackpot_trend.layout)
            .then(() => logData('头奖趋势图绘制成功'))
            .catch(err => logError('头奖趋势图绘制失败', err));
    } else {
        logData('无头奖趋势数据');
    }
    
    // 绘制资金对比图
    if (charts.money_comparison) {
        logData('绘制资金对比图', charts.money_comparison);
        Plotly.newPlot('moneyComparisonChart', charts.money_comparison.data, charts.money_comparison.layout)
            .then(() => logData('资金对比图绘制成功'))
            .catch(err => logError('资金对比图绘制失败', err));
    } else {
        logData('无资金对比数据');
    }
}

function updatePrizeStats(prizeStats) {
    if (!prizeStats || !Array.isArray(prizeStats)) {
        logError('无效的奖级统计数据');
        return;
    }

    try {
        const tbody = $('#prizeStatsTableBody');
        tbody.empty();
        
        prizeStats.forEach(stat => {
            const row = `
                <tr>
                    <td>${stat.prize_level}等奖</td>
                    <td>${formatNumber(stat.total_winners)}</td>
                    <td>${formatCurrency(stat.total_amount)}</td>
                    <td>${formatNumber(stat.avg_winners_per_round)}</td>
                    <td>${formatPercentage(stat.probability * 100)}</td>
                    <td>${formatPercentage(stat.rtp)}</td>
                </tr>
            `;
            tbody.append(row);
        });
        
        logData('奖级统计表更新成功');
    } catch (error) {
        logError('更新奖级统计表失败', error);
    }
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
    if (!globals.progressTimer) {
        globals.progressTimer = setInterval(checkProgress, 30000);  // 每30秒检查一次
    }
}

function stopProgressCheck() {
    if (globals.progressTimer) {
        clearInterval(globals.progressTimer);
        globals.progressTimer = null;
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