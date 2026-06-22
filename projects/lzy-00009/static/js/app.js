const sampleTexts = {
    chinese_pos: `2024年6月22日，张三先生在北京清华大学参加了由教育部组织的人工智能学术研讨会。他表示："这次会议非常精彩，结识了很多优秀的同行，收获满满！清华大学的校园环境也非常美丽，让人流连忘返。感谢主办方的精心安排，这是一次完美的学术交流体验！"`,
    
    chinese_neg: `昨天在京东买的华为手机，今天就降价了500元，客服态度非常差，说不能补差价。屏幕还有明显的划痕，物流也慢得要死。真是太失望了，再也不在京东买东西了，垃圾服务！建议大家都别上当。`,
    
    english_pos: `On June 22, 2024, Dr. John Smith attended the International AI Conference at Stanford University organized by Google. He said: "This conference was absolutely amazing! I met so many brilliant researchers from Microsoft, Amazon, and Meta. The presentations on deep learning and natural language processing were incredibly insightful. I highly recommend this event to anyone in the tech industry!"`,
    
    english_neg: `I purchased a new iPhone from Amazon last week. The delivery was delayed by 5 days, and when it finally arrived, the screen was cracked! I contacted customer service but they were extremely rude and unhelpful. They refused to give me a refund or replacement. This is the worst shopping experience I've ever had. Never buying from Amazon again!`,
    
    default: `2024年6月22日，张三先生在北京清华大学参加了由教育部组织的人工智能学术研讨会，他表示："这次会议非常精彩，结识了很多优秀的同行，收获满满！"`
};

let currentAnalysisResult = null;

function updateCharCount() {
    const textarea = document.getElementById('inputText');
    const charCount = document.getElementById('charCount');
    charCount.textContent = textarea.value.length;
}

function handlePaste(event) {
    setTimeout(() => {
        updateCharCount();
        showToast('文本已粘贴', 'success');
    }, 100);
}

async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            document.getElementById('inputText').value = text;
            updateCharCount();
            showToast('已从剪贴板粘贴', 'success');
        } else {
            showToast('剪贴板为空', 'info');
        }
    } catch (err) {
        showToast('无法访问剪贴板，请手动粘贴', 'error');
    }
}

function loadSample(type = 'default') {
    const textarea = document.getElementById('inputText');
    const sample = sampleTexts[type] || sampleTexts.default;
    textarea.value = sample;
    updateCharCount();
    
    const typeNames = {
        chinese_pos: '中文好评示例',
        chinese_neg: '中文差评示例',
        english_pos: '英文好评示例',
        english_neg: '英文差评示例',
        default: '默认示例'
    };
    
    showToast(`已加载${typeNames[type]}`, 'success');
}

function clearInput() {
    document.getElementById('inputText').value = '';
    updateCharCount();
    document.getElementById('resultsSection').style.display = 'none';
    currentAnalysisResult = null;
    showToast('已清空', 'info');
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

function setLoading(isLoading) {
    const btn = document.getElementById('analyzeBtn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = document.getElementById('btnLoader');
    
    if (isLoading) {
        btn.disabled = true;
        btnText.textContent = '分析中...';
        btnLoader.style.display = 'inline-block';
    } else {
        btn.disabled = false;
        btnText.textContent = '一键分析';
        btnLoader.style.display = 'none';
    }
}

async function analyzeText() {
    const text = document.getElementById('inputText').value.trim();
    
    if (!text) {
        showToast('请输入要分析的文本内容', 'error');
        return;
    }
    
    setLoading(true);
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentAnalysisResult = data;
            displayResults(data);
            document.getElementById('resultsSection').style.display = 'block';
            document.getElementById('resultsSection').scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
            showToast('分析完成！', 'success');
        } else {
            showToast(data.error || '分析失败', 'error');
        }
    } catch (err) {
        console.error('Analysis error:', err);
        showToast('网络错误，请稍后重试', 'error');
    } finally {
        setLoading(false);
    }
}

function displayResults(data) {
    displayEntityResults(data.entity_recognition);
    displaySentimentResults(data.sentiment_analysis);
    displayHighlight(data.entity_recognition.highlight_html);
    displayDetails(data);
}

function displayEntityResults(entityData) {
    document.getElementById('entityCount').textContent = `共 ${entityData.total_count} 个实体`;
    
    const legendContainer = document.getElementById('entityLegend');
    legendContainer.innerHTML = '';
    
    Object.keys(entityTypes).forEach(type => {
        const count = entityData.statistics[type] || 0;
        const info = entityTypes[type];
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <span class="legend-color" style="background-color: ${info.color}"></span>
            <span>${info.name}</span>
            <span class="legend-count">${count}</span>
        `;
        legendContainer.appendChild(legendItem);
    });
    
    const statsGrid = document.getElementById('entityStatsGrid');
    statsGrid.innerHTML = '';
    
    Object.keys(entityTypes).forEach(type => {
        const count = entityData.statistics[type] || 0;
        const info = entityTypes[type];
        const statCard = document.createElement('div');
        statCard.className = 'entity-stat-card';
        statCard.innerHTML = `
            <div class="stat-number" style="color: ${info.color}">${count}</div>
            <div class="stat-label">${info.name}</div>
        `;
        statsGrid.appendChild(statCard);
    });
    
    const entityList = document.getElementById('entityList');
    
    if (entityData.entities.length === 0) {
        entityList.innerHTML = '<p class="empty-state">未识别到任何实体</p>';
        return;
    }
    
    entityList.innerHTML = '';
    
    entityData.entities.forEach(entity => {
        const entityItem = document.createElement('div');
        entityItem.className = 'entity-item';
        entityItem.style.borderLeftColor = entity.color;
        entityItem.innerHTML = `
            <span class="entity-tag" style="background-color: ${entity.color}">${entity.type_name}</span>
            <span class="entity-text">${escapeHtml(entity.text)}</span>
            <span class="entity-confidence">${(entity.confidence * 100).toFixed(0)}%</span>
        `;
        entityList.appendChild(entityItem);
    });
}

function displaySentimentResults(sentimentData) {
    const badge = document.getElementById('sentimentBadge');
    badge.className = `sentiment-badge ${sentimentData.sentiment}`;
    badge.textContent = sentimentData.sentiment_name;

    document.getElementById('sentimentValue').textContent = sentimentData.sentiment_name;
    document.getElementById('confidenceValue').textContent = `${(sentimentData.confidence * 100).toFixed(1)}%`;

    const scoreNumber = document.getElementById('sentimentScoreNumber');
    scoreNumber.textContent = sentimentData.positive_score.toFixed(2);
    scoreNumber.className = 'score-number ' + (sentimentData.positive_score >= 0.5 ? 'positive' : 'negative');

    const positivePercent = sentimentData.positive_score * 100;
    const negativePercent = sentimentData.negative_score * 100;

    document.getElementById('positiveProgress').style.width = `${positivePercent}%`;
    document.getElementById('positiveLabel').textContent = `${positivePercent.toFixed(1)}%`;

    document.getElementById('negativeProgress').style.width = `${negativePercent}%`;
    document.getElementById('negativeLabel').textContent = `${negativePercent.toFixed(1)}%`;

    updateGauge(sentimentData.positive_score, sentimentData.gauge_data);
    updateSentimentChart(sentimentData);
}

function updateGauge(positiveScore, gaugeData) {
    const circumference = 251.2;
    const offset = circumference * (1 - positiveScore);

    const progress = document.getElementById('gaugeProgress');
    progress.style.strokeDashoffset = offset;
    progress.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)';

    const angle = (positiveScore * 180) - 90;
    const needle = document.getElementById('gaugeNeedle');
    const dot = document.getElementById('gaugeDot');
    const centerX = 100;
    const centerY = 100;
    const length = 60;

    const endX = centerX + length * Math.cos(angle * Math.PI / 180);
    const endY = centerY + length * Math.sin(angle * Math.PI / 180);

    needle.style.transition = 'all 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
    needle.setAttribute('x2', endX);
    needle.setAttribute('y2', endY);

    const dotX = centerX + 70 * Math.cos(angle * Math.PI / 180);
    const dotY = centerY + 70 * Math.sin(angle * Math.PI / 180);
    dot.style.transition = 'all 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
    dot.setAttribute('cx', dotX);
    dot.setAttribute('cy', dotY);

    if (gaugeData && gaugeData.current_color) {
        dot.setAttribute('fill', gaugeData.current_color);
        needle.setAttribute('stroke', gaugeData.current_color);
    }

    const gaugeValueEl = document.getElementById('gaugeValue');
    animateNumber(gaugeValueEl, 0, positiveScore * 100, 1200, v => `${v.toFixed(0)}%`);
}

function animateNumber(element, from, to, duration, formatter) {
    const start = performance.now();
    function step(timestamp) {
        const elapsed = timestamp - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = from + (to - from) * eased;
        element.textContent = formatter(current);
        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }
    requestAnimationFrame(step);
}

function updateSentimentChart(sentimentData) {
    const chartContainer = document.getElementById('sentimentChart');
    if (!chartContainer) return;

    const posScore = sentimentData.positive_score;
    const negScore = sentimentData.negative_score;
    const posDeg = posScore * 360;
    const negDeg = negScore * 360;

    chartContainer.innerHTML = `
        <svg viewBox="0 0 120 120" class="donut-svg">
            <circle cx="60" cy="60" r="45" fill="none" stroke="#e0e0e0" stroke-width="16"/>
            <circle cx="60" cy="60" r="45" fill="none" 
                stroke="#2ecc71" stroke-width="16"
                stroke-dasharray="${2 * Math.PI * 45 * posScore} ${2 * Math.PI * 45 * negScore}"
                stroke-dashoffset="${2 * Math.PI * 45 * 0.25}"
                stroke-linecap="round"
                style="transition: stroke-dasharray 1.5s cubic-bezier(0.4, 0, 0.2, 1);"
                class="donut-positive"/>
            <circle cx="60" cy="60" r="45" fill="none" 
                stroke="#e74c3c" stroke-width="16"
                stroke-dasharray="${2 * Math.PI * 45 * negScore} ${2 * Math.PI * 45 * posScore}"
                stroke-dashoffset="${2 * Math.PI * 45 * (0.25 - posScore)}"
                stroke-linecap="round"
                style="transition: stroke-dasharray 1.5s cubic-bezier(0.4, 0, 0.2, 1);"
                class="donut-negative"/>
            <text x="60" y="55" text-anchor="middle" class="donut-center-value"
                fill="${posScore >= 0.5 ? '#2ecc71' : '#e74c3c'}">
                ${(posScore * 100).toFixed(0)}%
            </text>
            <text x="60" y="72" text-anchor="middle" class="donut-center-label">
                ${sentimentData.sentiment_name}
            </text>
        </svg>
        <div class="donut-legend">
            <div class="donut-legend-item">
                <span class="donut-legend-dot" style="background:#2ecc71"></span>
                <span>正面 ${(posScore * 100).toFixed(1)}%</span>
            </div>
            <div class="donut-legend-item">
                <span class="donut-legend-dot" style="background:#e74c3c"></span>
                <span>负面 ${(negScore * 100).toFixed(1)}%</span>
            </div>
        </div>
    `;
}

function displayHighlight(highlightHtml) {
    const highlightContent = document.getElementById('highlightContent');
    const highlightLegend = document.getElementById('highlightLegend');
    
    highlightLegend.innerHTML = '';
    Object.keys(entityTypes).forEach(type => {
        const info = entityTypes[type];
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <span class="legend-color" style="background-color: ${info.color}"></span>
            <span>${info.name}</span>
        `;
        highlightLegend.appendChild(legendItem);
    });
    
    if (highlightHtml) {
        highlightContent.innerHTML = highlightHtml;
    } else {
        highlightContent.innerHTML = '<p class="empty-state">分析完成后将在此显示高亮标注的文本</p>';
    }
}

function displayDetails(data) {
    document.getElementById('analysisTime').textContent = data.timestamp;
    document.getElementById('textLength').textContent = `${data.text.length} 字符`;
    document.getElementById('detectedLanguage').textContent = 
        data.entity_recognition.language === 'chinese' ? '中文' : 'English';
    document.getElementById('sentenceCount').textContent = 
        `${data.sentiment_analysis.details.sentence_count} 句`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function downloadReport() {
    if (!currentAnalysisResult) {
        showToast('请先进行分析', 'error');
        return;
    }
    
    const data = currentAnalysisResult;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `文本分析报告_${timestamp}.html`;
    
    const reportHtml = generateReportHtml(data);
    
    const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('报告已下载', 'success');
}

function generateReportHtml(data) {
    const sentiment = data.sentiment_analysis;
    const entity = data.entity_recognition;
    
    const entityTableRows = entity.entities.map(e => `
        <tr>
            <td>${escapeHtml(e.text)}</td>
            <td><span style="color: ${e.color}; font-weight: 600;">${e.type_name}</span></td>
            <td>${(e.confidence * 100).toFixed(1)}%</td>
        </tr>
    `).join('');
    
    const entityStatsHtml = Object.keys(entityTypes).map(type => {
        const count = entity.statistics[type] || 0;
        const info = entityTypes[type];
        return `
            <div style="display: inline-block; margin: 5px; padding: 10px 20px; 
                        background: ${info.color}20; border-radius: 8px; min-width: 100px; text-align: center;">
                <div style="font-size: 24px; font-weight: 700; color: ${info.color};">${count}</div>
                <div style="font-size: 12px; color: #666;">${info.name}</div>
            </div>
        `;
    }).join('');
    
    return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>文本分析报告</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px;
            background: #f7fafc;
            color: #2d3748;
            line-height: 1.8;
        }
        .report-header {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 16px;
            margin-bottom: 30px;
        }
        .report-header h1 {
            margin: 0 0 10px 0;
            font-size: 28px;
        }
        .report-header p {
            margin: 0;
            opacity: 0.9;
        }
        .section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .section h2 {
            color: #2d3748;
            margin-top: 0;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
        }
        .sentiment-result {
            text-align: center;
            padding: 30px;
            background: ${sentiment.sentiment === 'positive' ? '#d4edda' : 
                        sentiment.sentiment === 'negative' ? '#f8d7da' : '#fff3cd'};
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .sentiment-result .label {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        .sentiment-result .value {
            font-size: 36px;
            font-weight: 700;
            color: ${sentiment.sentiment === 'positive' ? '#27ae60' : 
                        sentiment.sentiment === 'negative' ? '#e74c3c' : '#f39c12'};
        }
        .score-bar {
            height: 20px;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .score-fill {
            height: 100%;
            transition: width 1s;
        }
        .score-fill.positive {
            background: linear-gradient(90deg, #27ae60, #2ecc71);
        }
        .score-fill.negative {
            background: linear-gradient(90deg, #e74c3c, #c0392b);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        th {
            background: #f7fafc;
            font-weight: 600;
            color: #4a5568;
        }
        tr:hover {
            background: #f7fafc;
        }
        .highlight-text {
            padding: 20px;
            background: #f7fafc;
            border-radius: 8px;
            font-size: 15px;
            line-height: 2;
        }
        .entity-highlight {
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 500;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .info-item {
            padding: 15px;
            background: #f7fafc;
            border-radius: 8px;
        }
        .info-item .label {
            font-size: 12px;
            color: #718096;
            margin-bottom: 5px;
        }
        .info-item .value {
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #718096;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="report-header">
        <h1>📊 智能文本分析报告</h1>
        <p>生成时间：${data.timestamp}</p>
    </div>
    
    <div class="section">
        <h2>📈 情感分析结果</h2>
        <div class="sentiment-result">
            <div class="label">情感倾向</div>
            <div class="value">${sentiment.sentiment_name}</div>
            <div style="margin-top: 15px; font-size: 14px; color: #666;">
                置信度：${(sentiment.confidence * 100).toFixed(1)}%
            </div>
        </div>
        <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>正面概率</span>
                <span>${(sentiment.positive_score * 100).toFixed(1)}%</span>
            </div>
            <div class="score-bar">
                <div class="score-fill positive" style="width: ${sentiment.positive_score * 100}%"></div>
            </div>
        </div>
        <div style="margin-top: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>负面概率</span>
                <span>${(sentiment.negative_score * 100).toFixed(1)}%</span>
            </div>
            <div class="score-bar">
                <div class="score-fill negative" style="width: ${sentiment.negative_score * 100}%"></div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>🏷️ 实体识别结果</h2>
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="font-size: 14px; color: #666; margin-bottom: 10px;">共识别到 ${entity.total_count} 个实体</div>
            ${entityStatsHtml}
        </div>
        ${entity.entities.length > 0 ? `
        <table>
            <thead>
                <tr>
                    <th>实体文本</th>
                    <th>实体类型</th>
                    <th>置信度</th>
                </tr>
            </thead>
            <tbody>
                ${entityTableRows}
            </tbody>
        </table>
        ` : '<p style="text-align: center; color: #999; padding: 30px;">未识别到任何实体</p>'}
    </div>
    
    <div class="section">
        <h2>✨ 高亮标注文本</h2>
        <div class="highlight-text">
            ${entity.highlight_html || escapeHtml(data.text)}
        </div>
    </div>
    
    <div class="section">
        <h2>📋 详细信息</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="label">分析时间</div>
                <div class="value">${data.timestamp}</div>
            </div>
            <div class="info-item">
                <div class="label">文本长度</div>
                <div class="value">${data.text.length} 字符</div>
            </div>
            <div class="info-item">
                <div class="label">检测语言</div>
                <div class="value">${entity.language === 'chinese' ? '中文' : 'English'}</div>
            </div>
            <div class="info-item">
                <div class="label">句子数量</div>
                <div class="value">${sentiment.details.sentence_count} 句</div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>© 2024 智能文本分析平台 | 实体识别准确率 ≥ 85% | 情感分析准确率 ≥ 80%</p>
    </div>
</body>
</html>
    `;
}

document.addEventListener('DOMContentLoaded', function() {
    updateCharCount();
    
    document.getElementById('inputText').addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            analyzeText();
        }
    });
});
