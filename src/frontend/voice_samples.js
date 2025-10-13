/**
 * Voice Samples 管理
 * 处理音色样本的加载、预览和上传
 */

// 全局音色样本数据
let voiceSamplesData = {
    presets: [],
    custom: [],
    loaded: false
};

// 当前播放的音频
let currentAudio = null;

/**
 * 初始化音色样本
 */
async function initializeVoiceSamples() {
    try {
        console.log('[Voice Samples] 开始加载音色样本...');

        // 加载预设音色
        console.log('[Voice Samples] 正在请求预设音色接口...');
        const presetsResponse = await fetch('/api/v1/voice-samples/presets');
        console.log('[Voice Samples] 预设音色接口响应状态:', presetsResponse.status);

        if (presetsResponse.ok) {
            const data = await presetsResponse.json();
            voiceSamplesData.presets = data.samples || [];
            console.log(`[Voice Samples] 已加载 ${voiceSamplesData.presets.length} 个预设音色`);
            console.log('[Voice Samples] 预设音色列表:', voiceSamplesData.presets);
        } else {
            console.error(`[Voice Samples] 预设音色加载失败: HTTP ${presetsResponse.status}`);
        }

        // 加载自定义音色
        console.log('[Voice Samples] 正在请求自定义音色接口...');
        const customResponse = await fetch('/api/v1/voice-samples/custom');
        console.log('[Voice Samples] 自定义音色接口响应状态:', customResponse.status);

        if (customResponse.ok) {
            const data = await customResponse.json();
            voiceSamplesData.custom = data.samples || [];
            console.log(`[Voice Samples] 已加载 ${voiceSamplesData.custom.length} 个自定义音色`);
            if (voiceSamplesData.custom.length > 0) {
                console.log('[Voice Samples] 自定义音色列表:', voiceSamplesData.custom);
            }
        } else {
            console.error(`[Voice Samples] 自定义音色加载失败: HTTP ${customResponse.status}`);
        }

        voiceSamplesData.loaded = true;
        console.log('[Voice Samples] 音色样本加载完成，总计:',
                    voiceSamplesData.presets.length + voiceSamplesData.custom.length, '个音色');

    } catch (error) {
        console.error('[Voice Samples] 加载音色样本失败:', error);
        showToast('加载音色列表失败: ' + error.message, 'error');
        // 即使失败也标记为已加载，避免无限重试
        voiceSamplesData.loaded = true;
    }
}

/**
 * 填充音色选择器
 */
function populateVoiceSampleSelector(selectElement, characterId) {
    if (!selectElement) {
        console.warn('[Voice Samples] 选择器不存在');
        return;
    }

    if (!voiceSamplesData.loaded) {
        console.warn('[Voice Samples] 数据未加载，稍后重试');
        // 如果数据还没加载完，200ms后重试
        setTimeout(() => {
            if (voiceSamplesData.loaded) {
                populateVoiceSampleSelector(selectElement, characterId);
            }
        }, 200);
        return;
    }

    // 清空现有选项
    selectElement.innerHTML = '<option value="">请选择音色</option>';

    // 添加预设音色
    if (voiceSamplesData.presets.length > 0) {
        const presetGroup = document.createElement('optgroup');
        presetGroup.label = '预设音色';

        voiceSamplesData.presets.forEach(sample => {
            const option = document.createElement('option');
            option.value = sample.id;
            option.textContent = sample.name;
            option.dataset.sampleData = JSON.stringify(sample);
            option.dataset.isCustom = 'false';
            presetGroup.appendChild(option);
        });

        selectElement.appendChild(presetGroup);
    }

    // 添加自定义音色
    if (voiceSamplesData.custom.length > 0) {
        const customGroup = document.createElement('optgroup');
        customGroup.label = '自定义音色';

        voiceSamplesData.custom.forEach(sample => {
            const option = document.createElement('option');
            option.value = sample.id;
            option.textContent = sample.name;
            option.dataset.sampleData = JSON.stringify(sample);
            option.dataset.isCustom = 'true';
            customGroup.appendChild(option);
        });

        selectElement.appendChild(customGroup);
    }

    console.log(`[Voice Samples] 已填充音色选择器 #voice-${characterId} (共${voiceSamplesData.presets.length}个预设音色)`);
}

/**
 * 更新音色样本描述
 */
function updateVoiceSampleDescription(characterId) {
    const selectElement = document.getElementById(`voice-${characterId}`);
    const descElement = document.getElementById(`voice-desc-${characterId}`);

    if (!selectElement || !descElement) return;

    const selectedOption = selectElement.options[selectElement.selectedIndex];

    if (selectedOption && selectedOption.value) {
        try {
            const sampleData = JSON.parse(selectedOption.dataset.sampleData);
            const isCustom = selectedOption.dataset.isCustom === 'true';

            // 更新描述文本
            descElement.innerHTML = `
                <i class="fas fa-microphone me-1 text-primary"></i>
                <strong>${sampleData.name}</strong> - ${sampleData.description || '音色样本'}
                ${isCustom ? '<span class="badge bg-info ms-1">自定义</span>' : '<span class="badge bg-secondary ms-1">预设</span>'}
            `;

        } catch (e) {
            console.error('[Voice Samples] 解析音色数据失败:', e);
            descElement.innerHTML = '<i class="fas fa-info-circle me-1"></i>音色信息加载失败';
        }
    } else {
        descElement.innerHTML = '<i class="fas fa-info-circle me-1"></i>请选择音色';
    }
}

/**
 * 预览音色样本
 */
async function previewVoiceSample(characterId) {
    const selectElement = document.getElementById(`voice-${characterId}`);

    if (!selectElement || !selectElement.value) {
        showToast('请先选择音色', 'warning');
        return;
    }

    const sampleId = selectElement.value;
    const playButton = selectElement.parentElement.querySelector('button[onclick*="previewVoiceSample"]');

    try {
        // 停止之前的播放
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
            // 恢复所有播放按钮
            document.querySelectorAll('button[onclick*="previewVoiceSample"]').forEach(btn => {
                btn.innerHTML = '<i class="fas fa-play-circle"></i>';
                btn.title = '试听音色';
            });
        }

        // 更新按钮状态
        if (playButton) {
            playButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            playButton.title = '加载中...';
        }

        // 获取音频URL
        const audioUrl = `/api/v1/voice-samples/preview/${sampleId}`;

        // 创建并播放音频
        currentAudio = new Audio(audioUrl);

        currentAudio.onloadeddata = () => {
            if (playButton) {
                playButton.innerHTML = '<i class="fas fa-pause-circle"></i>';
                playButton.title = '停止试听';
            }
            currentAudio.play();
            console.log(`[Voice Samples] 开始播放音色样本: ${sampleId}`);
        };

        currentAudio.onended = () => {
            if (playButton) {
                playButton.innerHTML = '<i class="fas fa-play-circle"></i>';
                playButton.title = '试听音色';
            }
            currentAudio = null;
            console.log(`[Voice Samples] 音色样本播放完成: ${sampleId}`);
        };

        currentAudio.onerror = (e) => {
            console.error('[Voice Samples] 音频加载失败:', e);
            showToast('音色预览失败', 'error');
            if (playButton) {
                playButton.innerHTML = '<i class="fas fa-play-circle"></i>';
                playButton.title = '试听音色';
            }
            currentAudio = null;
        };

    } catch (error) {
        console.error('[Voice Samples] 预览音色失败:', error);
        showToast('预览失败', 'error');
        if (playButton) {
            playButton.innerHTML = '<i class="fas fa-play-circle"></i>';
            playButton.title = '试听音色';
        }
    }
}

/**
 * 上传自定义音色
 */
async function uploadCustomVoice(characterId) {
    const fileInput = document.getElementById(`custom-voice-${characterId}`);
    const voiceSelect = document.getElementById(`voice-${characterId}`);

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        return;
    }

    const file = fileInput.files[0];

    // 验证文件大小 (最大10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('文件过大，最大支持10MB', 'error');
        fileInput.value = '';
        return;
    }

    // 验证文件类型
    const allowedTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3'];
    if (!allowedTypes.includes(file.type)) {
        showToast('仅支持WAV和MP3格式', 'error');
        fileInput.value = '';
        return;
    }

    try {
        showToast('正在上传音色...', 'info');

        // 创建FormData
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', `角色${characterId}自定义音色`);
        formData.append('description', `角色${characterId}的自定义音色`);

        // 上传文件
        const response = await fetch('/api/v1/voice-samples/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '上传失败');
        }

        const data = await response.json();
        console.log('[Voice Samples] 上传成功:', data);

        // 重新加载自定义音色列表
        await loadCustomVoices();

        // 更新选择器
        populateVoiceSampleSelector(voiceSelect, characterId);

        // 自动选择刚上传的音色
        if (data.sample && data.sample.id) {
            voiceSelect.value = data.sample.id;
            updateVoiceSampleDescription(characterId);
        }

        showToast('音色上传成功！', 'success');

    } catch (error) {
        console.error('[Voice Samples] 上传失败:', error);
        showToast(`上传失败: ${error.message}`, 'error');
    } finally {
        // 清空文件输入
        fileInput.value = '';
    }
}

/**
 * 重新加载自定义音色列表
 */
async function loadCustomVoices() {
    try {
        const response = await fetch('/api/v1/voice-samples/custom');
        if (response.ok) {
            const data = await response.json();
            voiceSamplesData.custom = data.samples || [];
            console.log(`[Voice Samples] 已重新加载 ${voiceSamplesData.custom.length} 个自定义音色`);
        }
    } catch (error) {
        console.error('[Voice Samples] 重新加载自定义音色失败:', error);
    }
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', async () => {
    await initializeVoiceSamples();
});
