// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const updateBtn = document.getElementById('updateBtn');
    const channelSelect = document.getElementById('channelSelect');
    const updateStatus = document.getElementById('updateStatus');
    const logContainer = document.getElementById('logContainer');

    // 清空日志容器
    const clearLogs = () => {
        logContainer.innerHTML = '';
    };

    // 添加日志行到容器
    const addLogLine = (message, type = 'output') => {
        const logLine = document.createElement('div');
        logLine.className = `log-line log-line-${type}`;
        logLine.textContent = message;
        logContainer.appendChild(logLine);
        // 自动滚动到底部
        logContainer.scrollTop = logContainer.scrollHeight;
    };

    // 更新状态显示
    const updateStatusText = (text, type = '') => {
        updateStatus.textContent = text;
        updateStatus.className = `update-card__status ${type ? `status-${type}` : ''}`;
    };

    // 点击更新按钮逻辑
    updateBtn.addEventListener('click', function() {
        // 获取选中的渠道
        const channel = channelSelect.value.trim();
        if (!channel) {
            updateStatusText('请选择更新渠道', 'error');
            return;
        }

        // 初始化状态和日志
        clearLogs();
        updateBtn.disabled = true;
        updateStatusText(`开始更新【${channel}】渠道前端代码...`, 'loading');
        addLogLine(`[开始] 执行${channel}渠道更新操作`, 'success');

        // 建立SSE连接，传递渠道参数
        const source = new EventSource(`/ops_game/operate_client?channel=${encodeURIComponent(channel)}`);

        // 接收SSE消息
        source.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                switch (data.status) {
                    case 'loading':
                        updateStatusText(data.message, 'loading');
                        addLogLine(`[进度] ${data.message}`, 'output');
                        break;
                    case 'completed':
                        updateStatusText(data.message, 'completed');
                        addLogLine(`[完成] ${data.message}`, 'success');
                        source.close();
                        updateBtn.disabled = false;
                        break;
                    case 'error':
                        updateStatusText(data.message, 'error');
                        addLogLine(`[错误] ${data.message}`, 'error');
                        source.close();
                        updateBtn.disabled = false;
                        break;
                    case 'heartbeat':
                        addLogLine(`[等待] ${data.message}`, 'heartbeat');
                        break;
                    default:
                        // 普通日志输出
                        addLogLine(data.message || JSON.stringify(data), 'output');
                }
            } catch (e) {
                addLogLine(`[解析异常] ${event.data}`, 'error');
            }
        };

        // SSE连接错误
        source.onerror = function(error) {
            updateStatusText('更新连接异常', 'error');
            addLogLine(`[连接错误] ${JSON.stringify(error)}`, 'error');
            source.close();
            updateBtn.disabled = false;
        };
    });
});