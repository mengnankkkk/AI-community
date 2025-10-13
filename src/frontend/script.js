// AI虚拟播客工作室 - 现代化JavaScript控制器
// 全局变量
let characterCount = 0;
let currentTaskId = null;
let statusCheckInterval = null;
let isGenerating = false;
let knowledgeState = {
    stats: null,
    lastSource: '--',
    isUploading: false
};
let knowledgeUploadElements = {};

// API基础URL
const API_BASE_URL = '/api/v1';

// 功能配置
const CONFIG = {
    maxCharacters: 6,
    minCharacters: 2,
    defaultCharacterCount: 2,
    statusCheckInterval: 2000,
    animationDuration: 300,
    toastDuration: 3000
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 应用初始化
 */
function initializeApp() {
    // 添加默认角色
    for (let i = 0; i < CONFIG.defaultCharacterCount; i++) {
        addCharacter();
    }

    // 绑定表单提交事件
    document.getElementById('podcastForm').addEventListener('submit', handleFormSubmit);

    // 初始化工具提示
    initializeTooltips();

    // 初始化知识库上传与状态
    initializeKnowledgeUpload();

    // 添加输入验证
    addInputValidation();

    // 初始化主题建议
    initializeTopicSuggestions();

    // 同步知识库并刷新指标
    checkKnowledgeBase();

    // 显示欢迎提示
    showWelcomeToast();
}

function scrollToForm() {
    const anchor = document.getElementById('formAnchor');
    if (anchor) {
        anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function initializeKnowledgeUpload() {
    const dropzone = document.getElementById('knowledgeDropzone');
    const fileInput = document.getElementById('knowledgeFileInput');
    const status = document.getElementById('knowledgeUploadStatus');

    if (!dropzone || !fileInput) {
        return;
    }

    knowledgeUploadElements = { dropzone, fileInput, status };

    dropzone.addEventListener('click', (event) => {
        if (!event.target.closest('button')) {
            fileInput.click();
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();
            dropzone.classList.add('drag-active');
        });
    });

    ['dragleave', 'dragend', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();
            dropzone.classList.remove('drag-active');
        });
    });

    dropzone.addEventListener('drop', (event) => {
        const files = event.dataTransfer?.files;
        if (files && files.length) {
            handleKnowledgeFiles(files);
        }
    });

    fileInput.addEventListener('change', (event) => {
        const files = event.target.files;
        if (files && files.length) {
            handleKnowledgeFiles(files);
            fileInput.value = '';
        }
    });
}

async function handleKnowledgeFiles(fileList) {
    if (knowledgeState.isUploading) {
        showToast('知识文件正在上传，请稍候...', 'warning');
        return;
    }

    const files = Array.from(fileList).slice(0, 10);
    if (!files.length) {
        return;
    }

    if (fileList.length > files.length) {
        showToast('一次最多上传10个文件，部分文件已暂存', 'warning');
    }

    const allowedExtensions = ['.txt', '.md', '.pdf', '.docx', '.json'];
    const filteredFiles = files.filter(file => {
        const fileName = file.name.toLowerCase();
        return allowedExtensions.some(ext => fileName.endsWith(ext));
    });

    if (!filteredFiles.length) {
        showToast('未检测到支持的文件格式，请选择 txt/md/pdf/docx/json', 'error');
        return;
    }

    if (filteredFiles.length !== files.length) {
        showToast('部分文件类型暂不支持，已自动忽略', 'warning');
    }

    let hasFailure = false;
    knowledgeState.isUploading = true;
    setKnowledgeUploadStatus('正在上传知识文件...', 'info');

    for (let index = 0; index < filteredFiles.length; index++) {
        const file = filteredFiles[index];
        const formData = new FormData();
        formData.append('file', file);

        setKnowledgeUploadStatus(`(${index + 1}/${filteredFiles.length}) 上传中：${file.name}`, 'info');

        try {
            const response = await fetch(`${API_BASE_URL}/knowledge/add-file`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const result = await response.json().catch(() => ({ detail: '上传失败' }));
                throw new Error(result.detail || '上传失败');
            }

            knowledgeState.lastSource = file.name;
            renderKnowledgeStatus(knowledgeState.stats);
            showToast(`知识库已添加：${file.name}`, 'success');
        } catch (error) {
            console.error(error);
            showToast(`上传失败：${error.message}`, 'error');
            setKnowledgeUploadStatus(`上传失败：${file.name}`, 'error');
            hasFailure = true;
        }
    }

    knowledgeState.isUploading = false;
    setKnowledgeUploadStatus(hasFailure ? '部分文件上传失败，请稍后重试' : '上传完成', hasFailure ? 'warning' : 'success');
    await checkKnowledgeBase();
    setTimeout(() => setKnowledgeUploadStatus('', 'info'), 2500);
}

function setKnowledgeUploadStatus(message, type = 'info') {
    const status = knowledgeUploadElements.status;
    if (!status) {
        return;
    }

    if (!message) {
        status.textContent = '';
        status.dataset.state = '';
        status.className = 'upload-progress';
        return;
    }

    status.textContent = message;
    status.dataset.state = type;
    status.className = `upload-progress ${type}`;
}

/**
 * 添加角色
 */
function addCharacter() {
    if (characterCount >= CONFIG.maxCharacters) {
        showToast('角色数量已达上限', 'warning');
        return;
    }

    characterCount++;
    const container = document.getElementById('charactersContainer');

    const characterDiv = document.createElement('div');
    characterDiv.className = 'character-card fade-in';
    characterDiv.id = `character-${characterCount}`;

    characterDiv.innerHTML = `
        <div class="card-header">
            <span><i class="fas fa-user me-2"></i>角色 ${characterCount}</span>
            ${characterCount > CONFIG.minCharacters ? `
                <button type="button" class="btn btn-sm btn-danger" onclick="removeCharacter(${characterCount})">
                    <i class="fas fa-trash"></i> 删除
                </button>
            ` : ''}
        </div>
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="name-${characterCount}" class="form-label required">角色姓名/代称</label>
                    <input type="text" class="form-control" id="name-${characterCount}"
                           placeholder="例如：李博士" required>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label for="voice-${characterCount}" class="form-label required">
                        音色选择
                        <button type="button" class="btn btn-sm btn-link p-0 ms-1" onclick="previewVoiceSample(${characterCount})" title="试听音色">
                            <i class="fas fa-play-circle"></i>
                        </button>
                    </label>
                    <select class="form-select" id="voice-${characterCount}" onchange="updateVoiceSampleDescription(${characterCount})" required>
                        <option value="">正在加载音色...</option>
                    </select>
                    <small class="form-text text-muted" id="voice-desc-${characterCount}">
                        <i class="fas fa-info-circle me-1"></i>请选择音色
                    </small>
                </div>
                <div class="mb-3">
                    <label class="form-label">
                        或上传自定义音色
                        <i class="fas fa-question-circle text-muted ms-1" title="支持WAV/MP3格式，建议3-10秒纯净人声"></i>
                    </label>
                    <input type="file" class="form-control" id="custom-voice-${characterCount}"
                           accept="audio/wav,audio/mp3,audio/mpeg"
                           onchange="uploadCustomVoice(${characterCount})">
                    <small class="form-text text-muted">
                        <i class="fas fa-upload me-1"></i>上传后将自动使用此音色
                    </small>
                </div>
            </div>
        </div>
        <div class="mb-3">
            <label for="tone-${characterCount}" class="form-label required">语气风格</label>
            <input type="text" class="form-control" id="tone-${characterCount}"
                   placeholder="例如：平和专业、热情开朗、幽默风趣" required>
            <small class="form-text text-muted">
                <i class="fas fa-lightbulb text-warning me-1"></i>
                描述角色的说话风格和态度，AI将根据此生成符合人设的对话
            </small>
        </div>
        <div class="mb-3">
            <label for="persona-${characterCount}" class="form-label required">人设/身份</label>
            <textarea class="form-control" id="persona-${characterCount}" rows="2"
                      placeholder="例如：资深AI专家，拥有15年行业经验" required></textarea>
        </div>
        <div class="mb-3">
            <label for="viewpoint-${characterCount}" class="form-label required">核心观点</label>
            <textarea class="form-control" id="viewpoint-${characterCount}" rows="2"
                      placeholder="例如：AI是工具而非威胁，关键在于如何引导其发展" required></textarea>
        </div>
    `;

    container.appendChild(characterDiv);
    updateCharacterCount();

    // 添加动画效果
    setTimeout(() => {
        characterDiv.classList.add('slide-in-up');
    }, 50);

    // 填充音色选择框（使用voice samples）
    const voiceSelect = document.getElementById(`voice-${characterCount}`);
    if (voiceSelect && typeof populateVoiceSampleSelector === 'function') {
        populateVoiceSampleSelector(voiceSelect, characterCount);
    }
}

/**
 * 删除角色
 */
function removeCharacter(characterId) {
    if (characterCount <= CONFIG.minCharacters) {
        showToast('至少需要保留2个角色', 'warning');
        return;
    }

    const characterElement = document.getElementById(`character-${characterId}`);
    if (characterElement) {
        // 添加删除动画
        characterElement.style.transform = 'translateX(-100%)';
        characterElement.style.opacity = '0';

        setTimeout(() => {
            characterElement.remove();
            characterCount--;
            updateCharacterCount();
        }, CONFIG.animationDuration);
    }
}

/**
 * 更新角色数量显示
 */
function updateCharacterCount() {
    const display = document.getElementById('characterCountDisplay');
    if (display) {
        display.textContent = characterCount;

        // 根据角色数量更新提示样式
        const hint = document.getElementById('characterCountHint');
        if (characterCount < CONFIG.minCharacters) {
            hint.className = 'alert alert-warning border-0 py-2 mb-3';
        } else if (characterCount > 4) {
            hint.className = 'alert alert-info border-0 py-2 mb-3';
        } else {
            hint.className = 'alert alert-light border-0 py-2 mb-3';
        }
    }
}

/**
 * 收集表单数据
 */
function collectFormData() {
    const formData = {
        topic: document.getElementById('topic').value,
        title: document.getElementById('title').value || null,
        atmosphere: document.getElementById('atmosphere').value,
        target_duration: document.getElementById('duration').value,
        language_style: document.getElementById('languageStyle').value,
        background_materials: document.getElementById('backgroundMaterials').value || null,
        characters: []
    };

    // 收集角色信息
    const characterElements = document.querySelectorAll('.character-card');
    characterElements.forEach((element) => {
        const characterId = element.id.split('-')[1];
        const name = document.getElementById(`name-${characterId}`)?.value;
        const voiceSelect = document.getElementById(`voice-${characterId}`);
        const tone = document.getElementById(`tone-${characterId}`)?.value;
        const persona = document.getElementById(`persona-${characterId}`)?.value;
        const viewpoint = document.getElementById(`viewpoint-${characterId}`)?.value;

        if (name && voiceSelect && voiceSelect.value && tone && persona && viewpoint) {
            // 获取选中的音色数据
            const selectedOption = voiceSelect.options[voiceSelect.selectedIndex];
            let voiceFile = null;
            let voiceDescription = voiceSelect.value;

            try {
                const sampleData = JSON.parse(selectedOption.dataset.sampleData || '{}');
                voiceFile = sampleData.file_path || null;
                voiceDescription = sampleData.name || voiceSelect.value;
            } catch (e) {
                console.error('解析音色数据失败:', e);
            }

            formData.characters.push({
                name: name,
                voice_description: voiceDescription,
                voice_file: voiceFile,  // 添加音色文件路径
                tone_description: tone,
                persona: persona,
                core_viewpoint: viewpoint
            });
        }
    });

    return formData;
}

/**
 * 验证表单数据
 */
function validateForm() {
    const requiredFields = [
        { id: 'topic', name: '播客主题' },
        { id: 'atmosphere', name: '讨论氛围' },
        { id: 'duration', name: '目标时长' },
        { id: 'languageStyle', name: '语言风格' }
    ];

    // 验证基础字段
    for (const field of requiredFields) {
        const element = document.getElementById(field.id);
        if (!element.value.trim()) {
            element.focus();
            element.classList.add('is-invalid');
            showToast(`请填写${field.name}`, 'error');
            return false;
        } else {
            element.classList.remove('is-invalid');
        }
    }

    // 验证角色信息
    const formData = collectFormData();
    if (formData.characters.length < CONFIG.minCharacters) {
        showToast(`至少需要${CONFIG.minCharacters}个完整的角色信息`, 'error');
        return false;
    }

    return true;
}

/**
 * 处理表单提交
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    if (isGenerating) {
        showToast('正在生成中，请稍候...', 'info');
        return;
    }

    if (!validateForm()) {
        return;
    }

    const formData = collectFormData();
    const generateBtn = document.getElementById('generateBtn');

    try {
        isGenerating = true;
        updateGenerateButton(true);

        // 发送请求
        const response = await fetch(`${API_BASE_URL}/podcast/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                custom_form: formData
            })
        });

        const result = await response.json();

        if (response.ok) {
            currentTaskId = result.task_id;
            showToast('任务创建成功，开始生成播客...', 'success');
            startStatusCheck();
        } else {
            throw new Error(result.detail || '请求失败');
        }

    } catch (error) {
        console.error('Error:', error);
        showToast(`生成失败: ${error.message}`, 'error');
        isGenerating = false;
        updateGenerateButton(false);
    }
}

/**
 * 更新生成按钮状态
 */
function updateGenerateButton(generating) {
    const generateBtn = document.getElementById('generateBtn');

    if (generating) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>生成中...';
        generateBtn.classList.remove('pulse');
    } else {
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic me-2"></i>生成播客';
        generateBtn.classList.add('pulse');
    }
}

/**
 * 开始状态检查
 */
function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }

    // 显示进度详情
    const progressDetails = document.getElementById('progressDetails');
    progressDetails.style.display = 'block';

    updateStatus('pending', '任务已提交，正在处理中...');

    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/podcast/status/${currentTaskId}`);
            const result = await response.json();

            if (response.ok) {
                updateStatus(result.status, result.message, result);
                updateProgressSteps(result.status);

                if (result.status === 'completed' || result.status === 'failed') {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                    isGenerating = false;
                    updateGenerateButton(false);
                }
            } else {
                throw new Error('状态查询失败');
            }
        } catch (error) {
            console.error('Status check error:', error);
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
            isGenerating = false;
            updateGenerateButton(false);
            showToast('状态查询失败', 'error');
        }
    }, CONFIG.statusCheckInterval);
}

/**
 * 更新状态显示
 */
function updateStatus(status, message, result = null) {
    const statusContainer = document.getElementById('statusContainer');
    const resultContainer = document.getElementById('resultContainer');

    let statusClass = '';
    let icon = '';
    let progressHtml = '';

    switch (status) {
        case 'queued':
        case 'pending':
            statusClass = 'status-pending';
            icon = 'fas fa-clock';
            progressHtml = '<div class="progress mt-2"><div class="progress-bar" style="width: 10%"></div></div>';
            break;
        case 'generating_script':
            statusClass = 'status-generating';
            icon = 'fas fa-file-alt';
            progressHtml = '<div class="progress mt-2"><div class="progress-bar" style="width: 30%"></div></div>';
            break;
        case 'generating_audio':
            statusClass = 'status-generating';
            icon = 'fas fa-volume-up';
            progressHtml = '<div class="progress mt-2"><div class="progress-bar" style="width: 70%"></div></div>';
            break;
        case 'completed':
            statusClass = 'status-completed';
            icon = 'fas fa-check-circle';
            progressHtml = '<div class="progress mt-2"><div class="progress-bar" style="width: 100%"></div></div>';
            break;
        case 'failed':
            statusClass = 'status-failed';
            icon = 'fas fa-exclamation-circle';
            break;
    }

    statusContainer.innerHTML = `
        <div class="status-indicator ${statusClass}">
            <i class="${icon} me-2"></i>
            <div>
                <div>${message}</div>
                ${progressHtml}
            </div>
        </div>
    `;

    // 如果生成完成，显示结果
    if (status === 'completed' && result) {
        displayResult(result);
        resultContainer.style.display = 'block';
        showToast('播客生成完成！', 'success');
    }
}

/**
 * 更新进度步骤
 */
function updateProgressSteps(status) {
    const steps = document.querySelectorAll('.step');

    // 重置所有步骤
    steps.forEach(step => {
        step.classList.remove('active', 'completed');
    });

    // 根据状态更新步骤
    let activeStep = 0;
    switch (status) {
        case 'queued':
        case 'pending':
            activeStep = 1;
            break;
        case 'generating_script':
            activeStep = 1;
            break;
        case 'generating_audio':
            activeStep = 2;
            break;
        case 'processing_audio':
            activeStep = 3;
            break;
        case 'completed':
            activeStep = 4;
            break;
    }

    // 更新步骤状态
    steps.forEach((step, index) => {
        if (index < activeStep - 1) {
            step.classList.add('completed');
        } else if (index === activeStep - 1) {
            step.classList.add('active');
        }
    });
}

/**
 * 显示生成结果
 */
function displayResult(result) {
    // 显示剧本
    if (result.script) {
        displayScript(result.script);
    }

    // 显示音频播放器
    if (result.audio_url) {
        displayAudioPlayer(result.audio_url, result.script);
    }

    // 显示详细信息
    displayPodcastInfo(result.metadata || {});
}

/**
 * 显示剧本
 */
function displayScript(script) {
    const scriptPreview = document.getElementById('scriptPreview');

    let scriptHtml = `<h6 class="mb-3">${script.title}</h6>`;

    script.dialogues.forEach(dialogue => {
        scriptHtml += `
            <div class="dialogue-item">
                <div class="character-name">【${dialogue.character_name}】</div>
                <div class="dialogue-content">
                    ${dialogue.content}
                    ${dialogue.emotion ? `<span class="emotion-tag">${dialogue.emotion}</span>` : ''}
                </div>
            </div>
        `;
    });

    scriptPreview.innerHTML = scriptHtml;
}

/**
 * 显示音频播放器
 */
function displayAudioPlayer(audioUrl, script) {
    const audioPlayer = document.getElementById('audioPlayer');

    const duration = script && script.estimated_duration ?
        formatDuration(script.estimated_duration) : '未知';

    audioPlayer.innerHTML = `
        <div class="audio-player">
            <audio controls class="w-100 mb-3">
                <source src="${audioUrl}" type="audio/mpeg">
                您的浏览器不支持音频播放。
            </audio>
            <div class="audio-info">
                <span><i class="fas fa-clock me-1"></i>时长: ${duration}</span>
                <a href="${audioUrl}" download="podcast.mp3" class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-download me-1"></i>下载
                </a>
            </div>
        </div>
    `;
}

/**
 * 显示播客信息
 */
function displayPodcastInfo(metadata) {
    const podcastInfo = document.getElementById('podcastInfo');

    const ragDocs = knowledgeState.stats
        ? Number(knowledgeState.stats.document_count ?? knowledgeState.stats.total_documents ?? 0)
        : 0;
    const ragDocsLabel = Number.isFinite(ragDocs) ? ragDocs.toLocaleString('zh-CN') : '--';

    const ragStatus = ragDocs > 0
        ? `已启用（${ragDocsLabel} 篇文档）`
        : '未启用';

    podcastInfo.innerHTML = `
        <div class="podcast-metadata">
            <h6><i class="fas fa-info-circle me-2"></i>播客详情</h6>
            <ul class="list-unstyled">
                <li><strong>生成时间:</strong> ${new Date().toLocaleString()}</li>
                <li><strong>角色数量:</strong> ${metadata.character_count || '未知'}个</li>
                <li><strong>对话轮次:</strong> ${metadata.dialogue_count || '未知'}轮</li>
                <li><strong>使用模型:</strong> ${metadata.model_used || '默认模型'}</li>
                <li><strong>音效类型:</strong> ${metadata.audio_effects || '智能适配'}</li>
                <li><strong>RAG 知识库:</strong> ${ragStatus}</li>
            </ul>
        </div>
    `;
}

/**
 * 格式化时长
 */
function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * 显示主题建议
 */
function showTopicSuggestions() {
    const suggestions = document.getElementById('topicSuggestions');
    suggestions.style.display = 'block';
    setTimeout(() => {
        suggestions.classList.add('fade-in');
    }, 50);
}

/**
 * 隐藏主题建议
 */
function hideTopicSuggestions() {
    setTimeout(() => {
        const suggestions = document.getElementById('topicSuggestions');
        suggestions.style.display = 'none';
    }, 200);
}

/**
 * 选择主题
 */
function selectTopic(topic) {
    document.getElementById('topic').value = topic;
    hideTopicSuggestions();
    showToast(`已选择主题: ${topic}`, 'success');
}

/**
 * 生成主题建议
 */
async function generateTopicSuggestion() {
    try {
        showToast('正在生成主题建议...', 'info');

        // 这里可以调用AI API生成主题建议
        const suggestions = [
            '元宇宙技术的现实应用前景',
            '零工经济对传统就业的冲击',
            '个人隐私在数字时代的保护',
            '新能源汽车的普及挑战',
            '在线教育的优势与局限'
        ];

        const randomSuggestion = suggestions[Math.floor(Math.random() * suggestions.length)];
        document.getElementById('topic').value = randomSuggestion;
        showToast('已为您生成主题建议', 'success');

    } catch (error) {
        showToast('生成建议失败，请手动输入', 'error');
    }
}

/**
 * 生成角色建议
 */
async function generateCharacterSuggestion() {
    try {
        showToast('正在生成角色建议...', 'info');

        // 这里可以调用AI API根据主题生成角色建议
        const topic = document.getElementById('topic').value;
        if (!topic) {
            showToast('请先填写播客主题', 'warning');
            return;
        }

        showToast('角色建议功能正在开发中', 'info');

    } catch (error) {
        showToast('生成角色建议失败', 'error');
    }
}

/**
 * 检查知识库状态
 */
async function checkKnowledgeBase() {
    try {
        const response = await fetch(`${API_BASE_URL}/knowledge/stats`);
        const stats = await response.json();

        knowledgeState.stats = stats;
        renderKnowledgeStatus(stats);
    } catch (error) {
        console.error('Knowledge base check failed:', error);
        setKnowledgeUploadStatus('知识库状态获取失败', 'error');
        showToast('知识库状态获取失败，请稍后重试', 'error');
        renderKnowledgeStatus({ status: 'error' });
    }
}

function renderKnowledgeStatus(stats = {}) {
    const statusElement = document.getElementById('knowledgeStatus');
    const summaryElement = document.getElementById('knowledgeSummary');
    const heroDocElement = document.getElementById('heroKnowledgeCount');

    if (!statusElement) {
        return;
    }

    const documentCountRaw = stats.document_count ?? stats.total_documents ?? 0;
    const documentCount = Number(documentCountRaw) || 0;
    const documentLabel = Number.isFinite(documentCount) ? documentCount.toLocaleString('zh-CN') : documentCountRaw;
    const sizeMb = Number(stats.database_size_mb ?? 0);
    const status = stats.status ?? (documentCount > 0 ? 'ready' : 'not_initialized');

    const statusMap = {
        ready: {
            icon: 'fas fa-check-circle',
            label: '知识库已就绪',
            tone: 'ready',
            description: `已索引 ${documentLabel} 个文档`
        },
        not_initialized: {
            icon: 'fas fa-inbox',
            label: '知识库未初始化',
            tone: 'empty',
            description: '上传资料后即可启用知识增强'
        },
        error: {
            icon: 'fas fa-exclamation-triangle',
            label: '知识库异常',
            tone: 'error',
            description: '请检查配置或稍后重试'
        }
    };

    const config = statusMap[status] || statusMap.not_initialized;

    statusElement.innerHTML = `
        <div class="status-row ${config.tone}">
            <div class="status-icon"><i class="${config.icon}"></i></div>
            <div class="status-info">
                <span class="status-label">${config.label}</span>
                <p class="status-text mb-0">${config.description}</p>
            </div>
            <button class="btn btn-sm btn-outline-primary" onclick="checkKnowledgeBase()" title="刷新知识库">
                <i class="fas fa-sync"></i>
            </button>
        </div>
    `;

    if (summaryElement) {
        const docField = summaryElement.querySelector('[data-field="documents"]');
        const sizeField = summaryElement.querySelector('[data-field="size"]');
        const latestField = summaryElement.querySelector('[data-field="latest"]');

        if (docField) {
            docField.textContent = documentLabel;
        }
        if (sizeField) {
            sizeField.textContent = Number.isFinite(sizeMb) ? `${sizeMb.toFixed(2)} MB` : '--';
        }
        if (latestField) {
            latestField.textContent = knowledgeState.lastSource || '--';
        }
    }

    if (heroDocElement) {
        heroDocElement.textContent = documentLabel;
    }
}

function toggleKnowledgeBase() {
    const panel = document.querySelector('.knowledge-panel');
    if (!panel) {
        return;
    }

    panel.classList.add('panel-highlight');
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => panel.classList.remove('panel-highlight'), 1500);
    showToast('已定位至知识库区域', 'info');
}

function uploadFile() {
    const fileInput = document.getElementById('knowledgeFileInput');
    if (fileInput) {
        fileInput.click();
    }
}

/**
 * 加载模板
 */
function loadTemplate() {
    const templates = [
        {
            name: '科技讨论模板',
            topic: '人工智能对未来工作的影响',
            atmosphere: 'serious_deep',
            characters: [
                { name: '李博士', voice: '理性、严谨', persona: 'AI研究专家', viewpoint: 'AI将创造新的就业机会' },
                { name: '王经理', voice: '务实、直接', persona: '企业管理者', viewpoint: 'AI会替代大量传统工作' }
            ]
        }
    ];

    const template = templates[0];

    // 填充表单
    document.getElementById('topic').value = template.topic;
    document.getElementById('atmosphere').value = template.atmosphere;

    // 清空现有角色
    document.getElementById('charactersContainer').innerHTML = '';
    characterCount = 0;

    // 添加模板角色
    template.characters.forEach(char => {
        addCharacter();
        const currentId = characterCount;
        document.getElementById(`name-${currentId}`).value = char.name;
        document.getElementById(`voice-${currentId}`).value = char.voice;
        document.getElementById(`persona-${currentId}`).value = char.persona;
        document.getElementById(`viewpoint-${currentId}`).value = char.viewpoint;
    });

    showToast('已加载科技讨论模板', 'success');
}

/**
 * 重置表单
 */
function resetForm() {
    if (confirm('确定要重置所有内容吗？')) {
        document.getElementById('podcastForm').reset();
        document.getElementById('charactersContainer').innerHTML = '';
        characterCount = 0;

        // 重新添加默认角色
        for (let i = 0; i < CONFIG.defaultCharacterCount; i++) {
            addCharacter();
        }

        showToast('表单已重置', 'info');
    }
}

/**
 * 滚动到顶部
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * 显示帮助
 */
function showHelp() {
    const modal = new bootstrap.Modal(document.getElementById('helpModal'));
    modal.show();
}

/**
 * 显示功能特色
 */
function showFeatures() {
    const modal = new bootstrap.Modal(document.getElementById('featuresModal'));
    modal.show();
}

/**
 * 切换深色模式
 */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
    showToast(isDark ? '已切换到深色模式' : '已切换到浅色模式', 'info');
}

/**
 * 显示Toast提示
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast-' + Date.now();

    const typeClasses = {
        success: 'text-bg-success',
        error: 'text-bg-danger',
        warning: 'text-bg-warning',
        info: 'text-bg-info'
    };

    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };

    const toastHtml = `
        <div class="toast ${typeClasses[type] || typeClasses.info}" role="alert" id="${toastId}">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="${icons[type] || icons.info} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: CONFIG.toastDuration
    });

    toast.show();

    // 自动清理
    setTimeout(() => {
        if (toastElement) {
            toastElement.remove();
        }
    }, CONFIG.toastDuration + 500);
}

/**
 * 显示欢迎提示
 */
function showWelcomeToast() {
    setTimeout(() => {
        showToast('欢迎使用AI虚拟播客工作室！开始创建您的专属播客吧', 'success');
    }, 1000);
}

/**
 * 初始化工具提示
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(element => {
        new bootstrap.Tooltip(element);
    });
}

/**
 * 添加输入验证
 */
function addInputValidation() {
    // 实时验证主题输入
    const topicInput = document.getElementById('topic');
    topicInput.addEventListener('input', function() {
        if (this.value.length < 5) {
            this.classList.add('is-invalid');
        } else {
            this.classList.remove('is-invalid');
        }
    });

    // 验证角色名称重复
    document.addEventListener('input', function(e) {
        if (e.target.id && e.target.id.startsWith('name-')) {
            validateCharacterNames();
        }
    });
}

/**
 * 验证角色名称重复
 */
function validateCharacterNames() {
    const nameInputs = document.querySelectorAll('[id^="name-"]');
    const names = Array.from(nameInputs).map(input => input.value.trim()).filter(name => name);
    const uniqueNames = new Set(names);

    if (names.length !== uniqueNames.size) {
        nameInputs.forEach(input => {
            const value = input.value.trim();
            if (value && names.filter(name => name === value).length > 1) {
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });
    } else {
        nameInputs.forEach(input => input.classList.remove('is-invalid'));
    }
}

/**
 * 初始化主题建议
 */
function initializeTopicSuggestions() {
    // 预设一些热门主题
    const popularTopics = [
        '远程工作的未来趋势',
        '人工智能对教育的影响',
        '可持续发展与环保',
        '数字化转型的挑战',
        '新能源汽车的普及',
        '元宇宙技术的应用前景'
    ];

    // 可以根据需要动态更新建议
}

// 加载深色模式设置
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// 错误处理
window.addEventListener('error', function(e) {
    console.error('全局错误:', e.error);
    showToast('系统出现错误，请刷新页面重试', 'error');
});

// 网络状态监听
window.addEventListener('online', function() {
    showToast('网络连接已恢复', 'success');
    document.getElementById('systemStatus').innerHTML = '<i class="fas fa-circle"></i> 在线';
    document.getElementById('systemStatus').className = 'badge bg-success';
});

window.addEventListener('offline', function() {
    showToast('网络连接已断开', 'warning');
    document.getElementById('systemStatus').innerHTML = '<i class="fas fa-circle"></i> 离线';
    document.getElementById('systemStatus').className = 'badge bg-danger';
});

// ==================== 图片上传分析功能 ====================

// 图片上传相关变量
let currentTargetField = null;
let imageUploadModal = null;

/**
 * 开始图片上传
 * @param {string} targetField - 目标字段ID
 */
async function startImageUpload(targetField) {
    currentTargetField = targetField;

    // 显示图片上传模态框
    imageUploadModal = new bootstrap.Modal(document.getElementById('imageUploadModal'));

    // 重置界面状态
    resetImageUploadInterface();

    // 设置目标字段信息
    const fieldName = getFieldDisplayName(targetField);
    document.getElementById('uploadTitle').textContent = `为"${fieldName}"上传图片`;
    document.getElementById('targetFieldName').textContent = fieldName;

    imageUploadModal.show();
}

/**
 * 重置图片上传界面状态
 */
function resetImageUploadInterface() {
    // 隐藏所有结果区域
    document.getElementById('analysisResult').classList.add('d-none');
    document.getElementById('imagePreview').classList.add('d-none');

    // 重置按钮状态
    document.getElementById('selectImageBtn').classList.remove('d-none');
    document.getElementById('analyzeImageBtn').classList.add('d-none');
    document.getElementById('retryUploadBtn').classList.add('d-none');
    document.getElementById('confirmAnalysisBtn').classList.add('d-none');

    // 重置上传区域状态
    document.getElementById('uploadArea').classList.remove('d-none');
    document.getElementById('processingState').classList.add('d-none');

    // 清空文件选择
    const fileInput = document.getElementById('imageFileInput');
    if (fileInput) {
        fileInput.value = '';
    }
}

/**
 * 获取字段显示名称
 * @param {string} fieldId - 字段ID
 * @returns {string} 显示名称
 */
function getFieldDisplayName(fieldId) {
    const fieldNames = {
        'topic': '播客主题',
        'title': '播客标题',
        'backgroundMaterials': '背景资料'
    };

    // 处理角色字段
    if (fieldId.startsWith('name-')) return '角色姓名';
    if (fieldId.startsWith('voice-')) return '音色描述';
    if (fieldId.startsWith('persona-')) return '人设身份';
    if (fieldId.startsWith('viewpoint-')) return '核心观点';

    return fieldNames[fieldId] || fieldId;
}

/**
 * 选择图片文件
 */
function selectImageFile() {
    const fileInput = document.getElementById('imageFileInput');
    if (!fileInput) {
        // 创建文件输入元素
        const input = document.createElement('input');
        input.type = 'file';
        input.id = 'imageFileInput';
        input.accept = 'image/*';
        input.style.display = 'none';
        input.onchange = handleImageFileSelect;
        document.body.appendChild(input);
        input.click();
    } else {
        fileInput.click();
    }
}

/**
 * 处理图片文件选择
 */
function handleImageFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 验证文件类型
    if (!file.type.startsWith('image/')) {
        showToast('请选择图片文件', 'error');
        return;
    }

    // 验证文件大小（最大10MB）
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('图片文件过大，请选择小于10MB的图片', 'error');
        return;
    }

    // 预览图片
    previewImage(file);

    // 显示分析按钮
    document.getElementById('analyzeImageBtn').classList.remove('d-none');
    document.getElementById('selectImageBtn').textContent = '重新选择图片';
}

/**
 * 预览图片
 */
function previewImage(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('imagePreview');
        preview.innerHTML = `
            <img src="${e.target.result}" class="img-fluid rounded"
                 style="max-height: 200px; object-fit: contain;" alt="图片预览">
            <div class="mt-2 text-muted">
                <small>文件名: ${file.name} | 大小: ${formatFileSize(file.size)}</small>
            </div>
        `;
        preview.classList.remove('d-none');
    };
    reader.readAsDataURL(file);
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 分析图片
 */
async function analyzeImage() {
    const fileInput = document.getElementById('imageFileInput');
    const file = fileInput.files[0];

    if (!file) {
        showToast('请先选择图片文件', 'error');
        return;
    }

    try {
        // 更新界面状态
        updateAnalysisInterface(true);

        // 创建表单数据
        const formData = new FormData();
        formData.append('image_file', file);
        formData.append('analysis_type', 'material'); // 播客素材分析
        formData.append('target_field', currentTargetField);

        // 发送到Vision API
        const response = await fetch(`${API_BASE_URL}/vision/analyze`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            displayAnalysisResult(result);
        } else {
            throw new Error(result.error || '图片分析失败');
        }

    } catch (error) {
        console.error('图片分析失败:', error);
        showToast(`图片分析失败: ${error.message}`, 'error');

        // 显示重试按钮
        document.getElementById('retryUploadBtn').classList.remove('d-none');
        updateAnalysisInterface(false);
    }
}

/**
 * 更新分析界面状态
 * @param {boolean} isAnalyzing - 是否正在分析
 */
function updateAnalysisInterface(isAnalyzing) {
    const analyzeBtn = document.getElementById('analyzeImageBtn');
    const processingState = document.getElementById('processingState');
    const uploadArea = document.getElementById('uploadArea');

    if (isAnalyzing) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>分析中...';
        processingState.classList.remove('d-none');
        uploadArea.classList.add('d-none');

        document.getElementById('uploadTitle').textContent = '正在分析图片...';
        document.getElementById('uploadDescription').textContent = '请稍候，AI正在理解图片内容';
    } else {
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="fas fa-magic me-2"></i>开始分析';
        processingState.classList.add('d-none');
        uploadArea.classList.remove('d-none');
    }
}

/**
 * 显示分析结果
 * @param {Object} result - 分析结果
 */
function displayAnalysisResult(result) {
    // 显示分析文本
    document.getElementById('analyzedText').textContent = result.description;
    document.getElementById('analysisConfidence').textContent = Math.round(result.confidence * 100);

    // 显示结果区域
    document.getElementById('analysisResult').classList.remove('d-none');

    // 显示确认按钮
    document.getElementById('confirmAnalysisBtn').classList.remove('d-none');

    // 更新界面文本
    document.getElementById('uploadTitle').textContent = '分析完成';
    document.getElementById('uploadDescription').textContent = '请确认分析结果是否满意';

    updateAnalysisInterface(false);
}

/**
 * 确认并填入分析结果
 */
function confirmAnalysis() {
    const analyzedText = document.getElementById('analyzedText').textContent;

    if (analyzedText && currentTargetField) {
        // 获取目标输入元素
        const targetElement = document.getElementById(currentTargetField);

        if (targetElement) {
            // 根据元素类型设置值
            if (targetElement.tagName.toLowerCase() === 'textarea') {
                // 对于文本域，追加内容
                const currentValue = targetElement.value;
                targetElement.value = currentValue ? `${currentValue}\n${analyzedText}` : analyzedText;
            } else {
                // 对于输入框，替换内容
                targetElement.value = analyzedText;
            }

            // 触发输入事件以便表单验证
            targetElement.dispatchEvent(new Event('input', { bubbles: true }));

            showToast('图片分析内容已成功填入', 'success');
        }
    }

    // 关闭模态框
    imageUploadModal.hide();
}

/**
 * 重新上传图片
 */
function retryImageUpload() {
    resetImageUploadInterface();
    setTimeout(() => {
        selectImageFile();
    }, 100);
}

/**
 * 显示图片分析帮助
 */
function showImageAnalysisHelp() {
    const helpModal = new bootstrap.Modal(document.getElementById('imageAnalysisModal'));
    helpModal.show();
}

// 绑定图片上传相关事件
document.addEventListener('DOMContentLoaded', function() {
    // 绑定图片分析按钮事件
    document.getElementById('selectImageBtn').addEventListener('click', selectImageFile);
    document.getElementById('analyzeImageBtn').addEventListener('click', analyzeImage);
    document.getElementById('retryUploadBtn').addEventListener('click', retryImageUpload);
    document.getElementById('confirmAnalysisBtn').addEventListener('click', confirmAnalysis);

    // 在导航栏添加图片分析帮助按钮
    const navbar = document.querySelector('.navbar-nav');
    if (navbar) {
        const imageHelpBtn = document.createElement('a');
        imageHelpBtn.className = 'nav-link text-white me-2';
        imageHelpBtn.href = '#';
        imageHelpBtn.innerHTML = '<i class="fas fa-image me-1"></i>图片分析';
        imageHelpBtn.onclick = showImageAnalysisHelp;

        navbar.insertBefore(imageHelpBtn, navbar.firstChild);
    }

    // 加载音色库数据
    loadVoiceLibrary();
});

// ==================== 音色库功能 ====================

// 全局音色库数据
let voiceLibrary = {
    voices: [],
    categories: {},
    loaded: false
};

/**
 * 加载音色库数据
 */
async function loadVoiceLibrary() {
    try {
        const response = await fetch(`${API_BASE_URL}/voices/categories`);
        const result = await response.json();

        if (result.success) {
            voiceLibrary.categories = result.categories;
            voiceLibrary.voices = [];

            // 提取所有音色到平铺列表
            Object.values(result.categories).forEach(category => {
                voiceLibrary.voices.push(...category.voices);
            });

            voiceLibrary.loaded = true;

            // 更新所有已存在的音色选择框
            updateAllVoiceSelectors();

            console.log('音色库加载成功:', voiceLibrary.voices.length, '个音色');
        }
    } catch (error) {
        console.error('加载音色库失败:', error);
        showToast('音色库加载失败，将使用默认选项', 'warning');
    }
}

/**
 * 更新所有音色选择框
 */
function updateAllVoiceSelectors() {
    const voiceSelectors = document.querySelectorAll('select[id^="voice-"]');
    voiceSelectors.forEach(selector => {
        populateVoiceSelector(selector);
    });
}

/**
 * 填充音色选择框
 */
function populateVoiceSelector(selectElement) {
    if (!voiceLibrary.loaded || !selectElement) return;

    // 清空现有选项
    selectElement.innerHTML = '<option value="">请选择音色</option>';

    // 按分类添加选项
    Object.entries(voiceLibrary.categories).forEach(([categoryId, categoryData]) => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = categoryData.name;

        categoryData.voices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.id;
            option.textContent = `${voice.name} (${voice.name_en}) - ${voice.style}`;
            option.dataset.voiceData = JSON.stringify(voice);
            optgroup.appendChild(option);
        });

        selectElement.appendChild(optgroup);
    });
}

/**
 * 更新音色描述
 */
function updateVoiceDescription(characterId) {
    const selectElement = document.getElementById(`voice-${characterId}`);
    const descElement = document.getElementById(`voice-desc-${characterId}`);

    if (!selectElement || !descElement) return;

    const selectedOption = selectElement.options[selectElement.selectedIndex];

    if (selectedOption && selectedOption.value) {
        try {
            const voiceData = JSON.parse(selectedOption.dataset.voiceData);

            // 更新描述文本
            descElement.innerHTML = `
                <i class="fas fa-microphone me-1 text-primary"></i>
                <strong>${voiceData.name}</strong> - ${voiceData.description}
                <span class="badge bg-secondary ms-1">${voiceData.gender === 'male' ? '男声' : voiceData.gender === 'female' ? '女声' : '特色'}</span>
            `;

            // 根据音色特点，智能推荐语气风格
            const toneInput = document.getElementById(`tone-${characterId}`);
            if (toneInput && !toneInput.value) {
                suggestToneFromVoice(voiceData, toneInput);
            }
        } catch (e) {
            descElement.innerHTML = '<i class="fas fa-info-circle me-1"></i>音色信息加载失败';
        }
    } else {
        descElement.innerHTML = '<i class="fas fa-info-circle me-1"></i>请选择音色';
    }
}

/**
 * 根据音色智能推荐语气风格
 */
function suggestToneFromVoice(voiceData, toneInput) {
    let suggestedTone = '';

    // 根据音色风格推荐语气
    if (voiceData.tags.includes('专业') || voiceData.tags.includes('权威')) {
        suggestedTone = '平和专业、善于引导';
    } else if (voiceData.tags.includes('活力') || voiceData.tags.includes('热情')) {
        suggestedTone = '热情开朗、充满活力';
    } else if (voiceData.tags.includes('温暖') || voiceData.tags.includes('亲切')) {
        suggestedTone = '温暖亲切、平易近人';
    } else if (voiceData.tags.includes('磁性') || voiceData.tags.includes('浑厚')) {
        suggestedTone = '沉稳专业、富有感染力';
    } else if (voiceData.tags.includes('优雅') || voiceData.tags.includes('抒情')) {
        suggestedTone = '优雅从容、娓娓道来';
    } else {
        suggestedTone = '自然流畅、亲和友好';
    }

    toneInput.placeholder = `建议：${suggestedTone}`;
}

/**
 * 显示音色预览（未来功能）
 */
function showVoicePreview(voiceSelectId) {
    const selectElement = document.getElementById(voiceSelectId);
    if (!selectElement || !selectElement.value) {
        showToast('请先选择音色', 'warning');
        return;
    }

    // TODO: 实现音色预览功能
    showToast('音色预览功能正在开发中', 'info');
}