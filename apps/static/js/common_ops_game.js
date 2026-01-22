const eventSources = { stop: null, update: null, start: null, reload: null, initial: null, battle:null };

window.onbeforeunload = () => {
    Object.values(eventSources).forEach(source => {
        if (source) source.close();
    });
};

/**
 * 游戏操作核心函数,支持传递额外参数
 * @param {string} type - python代码要操作的类型标识（如 'rsync'、'start'、'stop' 等）
 * @param {string} script - 要执行脚本的参数传递（如 'rsync_game'、'start_game' 等）
 * @param {Object} [extraParams={}] - 额外传递的URL参数（如 { rsync_mode: 'update' }）
 */
function operateGame(type, script, extraParams = {}) {
    clearOutput(type);
    const operationText = getOperationText(type);
    showStatus(type, `正在${operationText}游戏服，请等待...`, 'connecting');

    if (eventSources[type]) {
        eventSources[type].close();
    }

    // 1. 拼接基础URL
    let url = `/ops_game/operate?script=${encodeURIComponent(script)}`;

    // 2. 拼接额外参数（如 rsync_mode，空值不拼接）
    Object.keys(extraParams).forEach(key => {
        // 仅当参数值存在时拼接，避免空参数干扰后端
        if (extraParams[key] !== undefined && extraParams[key] !== null && extraParams[key] !== '') {
            url += `&${encodeURIComponent(key)}=${encodeURIComponent(extraParams[key])}`;
        }
    });

    try {
        eventSources[type] = new EventSource(url);

        eventSources[type].onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                if (data.status === 'statistics') {
                    appendStatistics(type, data.data);
                    return;
                }
                if (data.status === 'completed') {
                    appendCompletedMessage(type, data.message);
                    eventSources[type].close();
                    return;
                }
                appendOutput(type, data);
                hideStatus(type);
            } catch (e) {
                appendErrorOutput(type, `数据解析错误: ${e.message}\n原始数据: ${event.data}`);
            }
        };

        eventSources[type].onerror = function () {
            handleEventSourceError(type, eventSources[type]);
        };
    } catch (err) {
        showStatus(type, `${operationText}初始化连接失败: ${err.message}`, 'error');
        setTimeout(() => hideStatus(type), 3000);
    }
}

function appendStatistics(type, stats) {
    // 为可能缺失的字段设置默认值（避免未定义错误）
    stats.total_executions = stats.total_executions ?? 0; // 若不存在则默认为0
    stats.total_failures = stats.total_failures ?? 0;     // 若不存在则默认为0
    const outputContainer = document.getElementById(`${type}_game`);
    const statsContainer = document.createElement('div');
    statsContainer.className = 'statistics-container';

    const statsHeader = document.createElement('div');
    statsHeader.className = 'statistics-header';
    statsHeader.textContent = '执行统计结果';
    statsContainer.appendChild(statsHeader);

    const totalStats = document.createElement('div');
    totalStats.className = 'statistics-section';
    const failureRate = stats.total_executions > 0
        ? ((stats.total_failures / stats.total_executions) * 100).toFixed(2)
        : '0.00';
    totalStats.innerHTML = `
        <p><strong>总体情况：</strong></p>
        <p>总执行次数：${stats.total_executions}</p>
        <p><span class="failure-count">总失败次数：${stats.total_failures}（失败率：${failureRate}%）</p>
    `;
    statsContainer.appendChild(totalStats);

    outputContainer.appendChild(statsContainer);
    outputContainer.scrollTop = outputContainer.scrollHeight;
}

function getOperationText(type) {
    const texts = { stop: '关闭', rsync: '同步', update: '更新', start: '启动', reload: '热更', initial: '部署', battle: '更新录像' };
    return texts[type] || type;
}

function handleEventSourceError(type, eventSource) {
    eventSource.close();
    showStatus(type, '操作已中断或发生错误', 'error');
    setTimeout(() => hideStatus(type), 3000);
}

function appendOutput(type, data) {
    const outputContainer = document.getElementById(`${type}_game`);
    const { task_id, status, message } = data;

    let taskGroup = outputContainer.querySelector(`[data-task-id="${task_id}"]`);
    if (!taskGroup) {
        taskGroup = document.createElement('div');
        taskGroup.className = `task-group ${status}`;
        taskGroup.setAttribute('data-task-id', task_id);

        const taskHeader = document.createElement('div');
        taskHeader.className = 'task-header';
        taskHeader.textContent = `任务: ${task_id}`;
        taskGroup.appendChild(taskHeader);

        const taskOutput = document.createElement('div');
        taskOutput.className = 'task-output';
        taskGroup.appendChild(taskOutput);

        outputContainer.appendChild(taskGroup);
    } else {
        taskGroup.className = `task-group ${status}`;
    }

    const taskOutput = taskGroup.querySelector('.task-output');
    const messageElement = document.createElement('div');
    messageElement.className = `message-${status}`;
    messageElement.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    taskOutput.appendChild(messageElement);

    outputContainer.scrollTop = outputContainer.scrollHeight;
}

function appendCompletedMessage(type, message) {
    const outputContainer = document.getElementById(`${type}_game`);
    const completedDiv = document.createElement('div');
    completedDiv.className = 'all-completed';
    completedDiv.textContent = message;
    outputContainer.appendChild(completedDiv);
    outputContainer.scrollTop = outputContainer.scrollHeight;
}

function appendErrorOutput(type, message) {
    const outputContainer = document.getElementById(`${type}_game`);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'task-group error';
    const errorOutput = document.createElement('div');
    errorOutput.className = 'task-output message-error';
    errorOutput.textContent = message;
    errorDiv.appendChild(errorOutput);
    outputContainer.appendChild(errorDiv);
    outputContainer.scrollTop = outputContainer.scrollHeight;
}

function clearOutput(type) {
    const outputContainer = document.getElementById(`${type}_game`);
    outputContainer.innerHTML = '';
}

function showStatus(type, message, className) {
    const statusDiv = document.getElementById(`${type}_status`);
    statusDiv.textContent = message;
    statusDiv.className = `status ${className}`;
    statusDiv.style.display = 'block';
}

function hideStatus(type) {
    const statusDiv = document.getElementById(`${type}_status`);
    statusDiv.style.display = 'none';
}

// 加载渠道
async function loadChannels() {
    try {
        const res = await fetch('/ops_game/api/channel_name_list');
        if (!res.ok) throw new Error(`HTTP错误: ${res.status}`);

        const channels = await res.json();
        const sel = document.getElementById('channel_name');

        // 清空现有选项（保留全部）
        sel.innerHTML = '<option value="" data-all="true">&lt;全部&gt;</option>';

        channels.forEach(channel => {
            const opt = document.createElement('option');
            opt.value = channel;
            opt.textContent = channel;
            sel.appendChild(opt);
        });

        // 监听多选逻辑：选全部则取消其他，选其他则取消全部
        sel.addEventListener('change', function(e) {
            const allOption = this.querySelector('[data-all="true"]');
            const selectedOptions = Array.from(this.selectedOptions);

            // 选中了"全部" → 取消其他选项
            if (selectedOptions.includes(allOption)) {
                Array.from(this.options).forEach(opt => {
                    if (opt !== allOption) opt.selected = false;
                });
                allOption.selected = true;
            } else {
                // 选中了其他 → 取消"全部"
                allOption.selected = false;
            }
        });
    } catch (err) {
        console.error('加载渠道列表失败:', err);
        alert(`加载渠道列表失败: ${err.message}`);
    }
}

// 加载游戏服类型(修改为支持多选，渠道选择后放开限制)
async function loadServerTypes() {
    const channelSel = document.getElementById('channel_name');
    const serverTypeSel = document.getElementById('server_type');
    const gameNuInput = document.getElementById('game_nu');
    const gameRangeSpan = document.getElementById('game_range');

    // 重置状态
    serverTypeSel.innerHTML = '<option value="" data-all="true">&lt;全部&gt;</option>';
    gameNuInput.value = '';
    gameRangeSpan.textContent = '';
    gameNuInput.disabled = true;

    // 获取选中的渠道（排除全部选项）
    const selectedChannels = Array.from(channelSel.selectedOptions)
        .filter(opt => !opt.dataset.all)
        .map(opt => opt.value);
    // 判断是否选中"全部"
    const isAllSelected = Array.from(channelSel.selectedOptions).some(opt => opt.dataset.all);

    // 渠道有选择（全部/单选/多选）→ 放开区服类型选择
    if (isAllSelected || selectedChannels.length > 0) {
        serverTypeSel.disabled = false;

        // 加载区服类型数据（若为单选渠道则加载对应类型，否则加载所有类型）
        if (selectedChannels.length === 1) {
            const channelName = selectedChannels[0];
            try {
                const res = await fetch(`/ops_game/api/game_type?channel_name=${encodeURIComponent(channelName)}`);
                if (!res.ok) throw new Error(`HTTP错误: ${res.status}`);

                const serverTypes = await res.json();
                serverTypes.forEach(type => {
                    const opt = document.createElement('option');
                    opt.value = type;
                    opt.textContent = type;
                    serverTypeSel.appendChild(opt);
                });
            } catch (err) {
                console.error('加载游戏服类型失败:', err);
                alert(`加载游戏服类型失败: ${err.message}`);
            }
        } else {
            // 全部/多选渠道 → 加载所有区服类型
            try {
                const res = await fetch(`/ops_game/add/api/game_type_list`);
                if (!res.ok) throw new Error(`HTTP错误: ${res.status}`);
                const serverTypes = await res.json();
                serverTypes.forEach(type => {
                    const opt = document.createElement('option');
                    opt.value = type;
                    opt.textContent = type;
                    serverTypeSel.appendChild(opt);
                });
            } catch (err) {
                console.error('加载所有游戏服类型失败:', err);
                alert(`加载所有游戏服类型失败: ${err.message}`);
            }
        }

        // 为区服类型添加多选逻辑
        serverTypeSel.addEventListener('change', function(e) {
            const allOption = this.querySelector('[data-all="true"]');
            const selectedOptions = Array.from(this.selectedOptions);

            // 选中了"全部" → 取消其他选项
            if (selectedOptions.includes(allOption)) {
                Array.from(this.options).forEach(opt => {
                    if (opt !== allOption) opt.selected = false;
                });
                allOption.selected = true;
            } else {
                // 选中了其他 → 取消"全部"
                allOption.selected = false;
            }
            // 触发区服加载逻辑
            loadGameNumbers();
        });
    } else {
        // 渠道未选择 → 禁用区服类型
        serverTypeSel.disabled = true;
    }
}

// 区服数据（修改：区服类型多选/全部时禁用输入）
async function loadGameNumbers() {
    const channelSel = document.getElementById('channel_name');
    const serverTypeSel = document.getElementById('server_type');
    const gameNuInput = document.getElementById('game_nu');
    const gameRangeSpan = document.getElementById('game_range');

    gameNuInput.value = '';
    gameRangeSpan.textContent = '';
    gameNuInput.disabled = true;

    // 获取选中的渠道（排除全部）
    const selectedChannels = Array.from(channelSel.selectedOptions)
        .filter(opt => !opt.dataset.all)
        .map(opt => opt.value);
    // 获取选中的区服类型（排除全部）
    const selectedServerTypes = Array.from(serverTypeSel.selectedOptions)
        .filter(opt => !opt.dataset.all)
        .map(opt => opt.value);
    // 判断区服类型是否选中"全部"
    const isServerTypeAll = Array.from(serverTypeSel.selectedOptions).some(opt => opt.dataset.all);

    // 区服类型多选/全部 → 禁用输入
    if (isServerTypeAll || selectedServerTypes.length > 1) {
        gameRangeSpan.textContent = '已选择全部/多个区服类型，无需输入区服范围';
        return;
    }

    // 单选渠道 + 单选区服类型 → 加载区服并启用输入
    if (selectedChannels.length === 1 && selectedServerTypes.length === 1) {
        const channelName = selectedChannels[0];
        const serverType = selectedServerTypes[0];
        try {
            const res = await fetch(`/ops_game/api/game_nu?channel_name=${encodeURIComponent(channelName)}&server_type=${encodeURIComponent(serverType)}`);
            if (!res.ok) throw new Error(`HTTP错误: ${res.status}`);

            const gameNumbers = await res.json();
            gameNuInput.disabled = false;

            if (gameNumbers.length === 0) {
                gameRangeSpan.textContent = '无可用区服';
            } else if (gameNumbers.length === 1) {
                gameRangeSpan.textContent = `区服范围：${gameNumbers[0]}服`;
            } else {
                const numList = gameNumbers.map(num => parseInt(num, 10)).filter(num => !isNaN(num));
                if (numList.length > 0) {
                    const min = Math.min(...numList);
                    const max = Math.max(...numList);
                    gameRangeSpan.textContent = `区服范围：[最小 ${min}服 - 最大 ${max}服]`;
                } else {
                    gameRangeSpan.textContent = '区服数据格式异常';
                }
            }
        } catch (err) {
            console.error('加载区服范围失败:', err);
            alert(`加载区服范围失败: ${err.message}`);
            gameRangeSpan.textContent = '加载失败';
        }
    }
}

// 提交选择（新增更新方式校验，传递更新方式参数）
async function submitSelection() {
    // 1. 校验更新方式
    const updateMode = document.getElementById('update_mode').value;
    const updateModeTip = document.getElementById('update_mode_tip');
    if (!updateMode) {
        updateModeTip.style.display = 'inline';
        setTimeout(() => updateModeTip.style.display = 'none', 3000);
        return;
    }

    const channelSel = document.getElementById('channel_name');
    const serverTypeSel = document.getElementById('server_type');
    const gameNu = document.getElementById('game_nu').value;

    // 2. 提取渠道值
    const allSelectedChannelOptions = Array.from(channelSel.selectedOptions);
    const isChannelAllSelected = allSelectedChannelOptions.some(opt =>
        opt.innerText.includes('<全部>') || opt.innerText.includes('&lt;全部&gt;')
    );
    let channelName = null;
    if (!isChannelAllSelected && allSelectedChannelOptions.length > 0) {
        const selectedChannels = allSelectedChannelOptions
            .map(opt => opt.innerText.trim())
            .filter(name => name !== '' && !name.includes('全部'));
        if (selectedChannels.length >= 1) {
            channelName = selectedChannels.length === 1 ? selectedChannels[0] : selectedChannels;
        }
    }

    // 3. 提取区服类型值
    const allSelectedServerTypeOptions = Array.from(serverTypeSel.selectedOptions);
    const isServerTypeAllSelected = allSelectedServerTypeOptions.some(opt =>
        opt.innerText.includes('<全部>') || opt.innerText.includes('&lt;全部&gt;')
    );
    let serverType = null;
    if (!isServerTypeAllSelected && allSelectedServerTypeOptions.length > 0) {
        const selectedServerTypes = allSelectedServerTypeOptions
            .map(opt => opt.innerText.trim())
            .filter(name => name !== '' && !name.includes('全部'));
        if (selectedServerTypes.length >= 1) {
            serverType = selectedServerTypes.length === 1 ? selectedServerTypes[0] : selectedServerTypes;
        }
    }

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

        const response = await fetch('/ops_game/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                update_mode: updateMode, // 新增更新方式参数
                channel_name: channelName,
                server_type: serverType,
                game_nu: gameNu
            })
        });

        if (!response.ok) throw new Error(`HTTP错误: ${response.status}`);
        document.getElementById('result').textContent = await response.text();
    } catch (err) {
        console.error('提交选择失败:', err);
        document.getElementById('result').textContent = `提交失败: ${err.message}`;
    }
}

// 查询列表
async function queryGameList() {
    try {
        const response = await fetch('/ops_game/query_list');
        if (!response.ok) throw new Error(`HTTP错误: ${response.status}`);

        const textData = await response.text();
        let formattedData;

        try {
            const jsonData = JSON.parse(textData);
            formattedData = JSON.stringify(jsonData);
        } catch (e) {
            formattedData = textData;
        }

        document.getElementById('query_game_list').textContent = formattedData;
    } catch (err) {
        console.error('查询游戏服列表失败:', err);
        document.getElementById('query_game_list').textContent = `查询失败: ${err.message}`;
    }
}

// 处理同步代码操作
function handleRsync() {
    const rsyncMode = document.getElementById('rsync_mode').value;
    if (!rsyncMode) {
        alert('请先选择同步类型（更新或热更）');
        return;
    }
    // 关键：script 传纯值，rsync_mode 作为额外参数传递
    operateGame('rsync', 'rsync_game', { rsync_mode: rsyncMode });
}