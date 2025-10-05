# 前端音色选择集成指南

## 📋 概述

本指南说明如何在前端实现**双模式音色选择**功能，适配 `indextts2_gradio` TTS引擎的音色克隆机制。

---

## 🎯 两种音色选择策略

### 策略1：预设音色库选择
用户从系统预设的音色样本中选择（`voice_samples/` 目录）

### 策略2：自定义音频上传
用户上传自己的音频文件进行音色克隆

---

## 📡 后端API接口

### 1. 获取预设音色列表

```http
GET /api/v1/voice-samples/presets
```

**响应示例：**
```json
{
  "success": true,
  "total": 11,
  "samples": [
    {
      "id": "voice_standard",
      "name": "标准音色",
      "file_path": "voice_samples/voice_standard.wav",
      "file_size": 245678,
      "description": "中性标准音色，适合通用场景",
      "tags": ["通用", "标准", "中性"],
      "is_custom": false
    },
    {
      "id": "voice_male",
      "name": "男声",
      "file_path": "voice_samples/voice_male.wav",
      "file_size": 198432,
      "description": "标准男声，清晰自然",
      "tags": ["男声", "标准"],
      "is_custom": false
    }
    // ... 更多预设音色
  ]
}
```

---

### 2. 上传自定义音色

```http
POST /api/v1/voice-samples/upload
Content-Type: multipart/form-data
```

**请求参数：**
- `file` (File, 必须): 音频文件（WAV/MP3/M4A/OGG，最大10MB）
- `name` (String, 可选): 音色名称
- `description` (String, 可选): 音色描述

**响应示例：**
```json
{
  "success": true,
  "sample": {
    "id": "custom_20251002_143025_a1b2c3d4",
    "name": "我的自定义音色",
    "file_path": "uploads/custom_voices/custom_20251002_143025_a1b2c3d4.wav",
    "file_size": 312456,
    "description": "用户上传的自定义音色",
    "is_custom": true,
    "created_at": "2025-10-02T14:30:25.123456"
  }
}
```

---

### 3. 获取用户上传的音色列表

```http
GET /api/v1/voice-samples/custom
```

**响应格式同预设音色列表**

---

### 4. 删除自定义音色

```http
DELETE /api/v1/voice-samples/{sample_id}
```

**响应：**
```json
{
  "success": true,
  "message": "删除成功"
}
```

---

## 🎨 前端实现示例

### HTML结构

```html
<!-- 音色选择模式切换 -->
<div class="voice-mode-selector">
  <button id="preset-mode-btn" class="mode-btn active">预设音色</button>
  <button id="custom-mode-btn" class="mode-btn">自定义上传</button>
</div>

<!-- 预设音色库 -->
<div id="preset-voices" class="voice-section">
  <h3>选择预设音色</h3>
  <div id="preset-voice-list" class="voice-grid">
    <!-- 动态加载音色卡片 -->
  </div>
</div>

<!-- 自定义上传 -->
<div id="custom-upload" class="voice-section" style="display:none;">
  <h3>上传音色样本</h3>
  <div class="upload-area">
    <input type="file" id="voice-file-input" accept=".wav,.mp3,.m4a,.ogg" />
    <button id="upload-btn">上传音频</button>
  </div>

  <div id="custom-voice-list" class="voice-grid">
    <!-- 显示已上传的音色 -->
  </div>
</div>
```

---

### JavaScript实现

```javascript
// ========== 1. 加载预设音色 ==========
async function loadPresetVoices() {
  try {
    const response = await fetch('/api/v1/voice-samples/presets');
    const data = await response.json();

    if (data.success) {
      renderVoiceList(data.samples, 'preset-voice-list');
    }
  } catch (error) {
    console.error('加载预设音色失败:', error);
  }
}

// ========== 2. 加载用户上传的音色 ==========
async function loadCustomVoices() {
  try {
    const response = await fetch('/api/v1/voice-samples/custom');
    const data = await response.json();

    if (data.success) {
      renderVoiceList(data.samples, 'custom-voice-list', true);
    }
  } catch (error) {
    console.error('加载自定义音色失败:', error);
  }
}

// ========== 3. 渲染音色列表 ==========
function renderVoiceList(samples, containerId, allowDelete = false) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  samples.forEach(sample => {
    const card = document.createElement('div');
    card.className = 'voice-card';
    card.innerHTML = `
      <div class="voice-info">
        <h4>${sample.name}</h4>
        <p class="voice-desc">${sample.description}</p>
        <div class="voice-tags">
          ${sample.tags?.map(tag => `<span class="tag">${tag}</span>`).join('') || ''}
        </div>
      </div>
      <div class="voice-actions">
        <button class="select-btn" data-voice-path="${sample.file_path}">
          选择
        </button>
        ${allowDelete ? `
          <button class="delete-btn" data-voice-id="${sample.id}">
            删除
          </button>
        ` : ''}
      </div>
    `;

    // 选择按钮事件
    card.querySelector('.select-btn').addEventListener('click', () => {
      selectVoice(sample);
    });

    // 删除按钮事件
    if (allowDelete) {
      card.querySelector('.delete-btn').addEventListener('click', () => {
        deleteVoice(sample.id);
      });
    }

    container.appendChild(card);
  });
}

// ========== 4. 选择音色 ==========
function selectVoice(sample) {
  // 存储选中的音色信息到角色配置
  const currentCharacter = getCurrentCharacter(); // 获取当前编辑的角色

  // 设置voice_file字段（关键！）
  currentCharacter.voice_file = sample.file_path;
  currentCharacter.voice_description = sample.name; // 保留描述作为显示名称

  // 更新UI显示
  document.getElementById('selected-voice-name').textContent = sample.name;
  document.getElementById('selected-voice-path').textContent = sample.file_path;

  // 高亮选中状态
  document.querySelectorAll('.voice-card').forEach(card => {
    card.classList.remove('selected');
  });
  event.currentTarget.closest('.voice-card').classList.add('selected');
}

// ========== 5. 上传自定义音色 ==========
async function uploadCustomVoice() {
  const fileInput = document.getElementById('voice-file-input');
  const file = fileInput.files[0];

  if (!file) {
    alert('请选择音频文件');
    return;
  }

  // 验证文件类型
  const allowedTypes = ['.wav', '.mp3', '.m4a', '.ogg'];
  const fileExt = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowedTypes.includes(fileExt)) {
    alert('仅支持 WAV, MP3, M4A, OGG 格式');
    return;
  }

  // 验证文件大小（10MB限制）
  if (file.size > 10 * 1024 * 1024) {
    alert('文件过大，最大支持10MB');
    return;
  }

  // 创建FormData
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', prompt('请输入音色名称:') || file.name);
  formData.append('description', '用户上传的自定义音色');

  try {
    const response = await fetch('/api/v1/voice-samples/upload', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.success) {
      alert('上传成功！');
      // 重新加载自定义音色列表
      loadCustomVoices();
      // 自动选择刚上传的音色
      selectVoice(data.sample);
    } else {
      alert('上传失败: ' + data.detail);
    }
  } catch (error) {
    console.error('上传失败:', error);
    alert('上传失败，请重试');
  }
}

// ========== 6. 删除自定义音色 ==========
async function deleteVoice(voiceId) {
  if (!confirm('确定要删除这个音色吗？')) {
    return;
  }

  try {
    const response = await fetch(`/api/v1/voice-samples/${voiceId}`, {
      method: 'DELETE'
    });

    const data = await response.json();

    if (data.success) {
      alert('删除成功');
      loadCustomVoices();
    }
  } catch (error) {
    console.error('删除失败:', error);
    alert('删除失败，请重试');
  }
}

// ========== 7. 模式切换 ==========
document.getElementById('preset-mode-btn').addEventListener('click', () => {
  document.getElementById('preset-voices').style.display = 'block';
  document.getElementById('custom-upload').style.display = 'none';
  document.getElementById('preset-mode-btn').classList.add('active');
  document.getElementById('custom-mode-btn').classList.remove('active');
});

document.getElementById('custom-mode-btn').addEventListener('click', () => {
  document.getElementById('preset-voices').style.display = 'none';
  document.getElementById('custom-upload').style.display = 'block';
  document.getElementById('custom-mode-btn').classList.add('active');
  document.getElementById('preset-mode-btn').classList.remove('active');

  // 加载自定义音色列表
  loadCustomVoices();
});

// ========== 8. 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
  loadPresetVoices();

  // 上传按钮事件
  document.getElementById('upload-btn').addEventListener('click', uploadCustomVoice);
});
```

---

## 📤 提交播客生成请求

### 角色配置数据结构

```javascript
// 创建角色配置
const character = {
  name: "李博士",
  voice_description: "男中音",  // 描述性文字（向后兼容）
  voice_file: "voice_samples/voice_baritone.wav",  // 音色文件路径（优先使用）
  tone_description: "平和专业",
  persona: "资深AI专家",
  core_viewpoint: "AI应该辅助而非替代人类"
};

// 完整的播客生成请求
const request = {
  custom_form: {
    topic: "AI对未来工作的影响",
    title: "AI时代的工作变革",
    atmosphere: "serious_deep",
    target_duration: "5分钟",
    language_style: "formal",
    characters: [
      character,
      // ... 更多角色
    ]
  }
};

// 发送请求
const response = await fetch('/api/v1/podcast/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(request)
});
```

---

## 🎯 关键要点

### 1. 优先级规则
- **有 `voice_file`**：使用指定的音色文件（用户选择或上传）
- **无 `voice_file`**：使用 `voice_description` 映射到预设音色

### 2. 向后兼容
- 保留 `voice_description` 字段，确保与旧版前端兼容
- NihalGazi TTS 等其他引擎仍使用 `voice_description`

### 3. 文件要求
- **格式**：WAV（推荐）, MP3, M4A, OGG
- **时长**：3-10秒纯净人声
- **大小**：最大10MB
- **质量**：清晰、无背景噪音

### 4. 错误处理
```javascript
// 检查音色文件是否存在
if (character.voice_file && !await checkFileExists(character.voice_file)) {
  console.warn('音色文件不存在，回退到描述映射');
  character.voice_file = null;
}
```

---

## 🎨 CSS样式参考

```css
.voice-mode-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.mode-btn {
  padding: 10px 20px;
  border: 2px solid #ccc;
  background: white;
  cursor: pointer;
  border-radius: 5px;
  transition: all 0.3s;
}

.mode-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.voice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
}

.voice-card {
  border: 1px solid #ddd;
  padding: 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.voice-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.voice-card.selected {
  border-color: #007bff;
  background: #f0f8ff;
}

.voice-tags {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.tag {
  background: #e9ecef;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}
```

---

## 🧪 测试建议

1. **预设音色测试**：选择不同预设音色，验证生成效果
2. **自定义上传测试**：上传3-5秒人声样本，测试克隆效果
3. **混合使用**：部分角色用预设，部分角色用自定义
4. **边界情况**：大文件、错误格式、网络异常

---

## 📞 技术支持

如有问题，请查看：
- API文档：http://localhost:8000/docs
- 后端日志：查看服务器控制台输出
- 示例代码：`test_voice_samples.html`（可创建）

---

**更新时间：** 2025-10-02
**适用版本：** v1.0.0+
