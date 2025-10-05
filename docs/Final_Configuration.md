# IndexTTS-2 最终配置方案

## 问题总结

1. **HuggingFace官方空间问题**
   - SSL握手超时（即使配置代理）
   - Gradio Client的WebSocket连接在代理环境下不稳定
   - 需要复杂的代理配置且成功率低

2. **魔搭社区空间**
   - ✅ 访问测试成功
   - ✅ 国内直连速度快
   - ✅ 无需代理配置
   - ⚠️ 使用中文API参数（与HF版本不同）

## ✅ 最终解决方案：使用魔搭社区

### 配置文件 (.env)

```env
# TTS引擎配置
TTS_ENGINE=indextts2_gradio

# IndexTTS2 Gradio配置 - 使用魔搭社区
INDEXTTS2_GRADIO_SPACE=https://indexteam-indextts-2-demo.ms.show

# 代理配置 - 魔搭社区无需代理
PROXY_ENABLED=false
```

### 代码配置

**API参数 (indextts2_gradio_service.py:295)**
```python
emo_control_method="与音色参考音频相同",  # 魔搭社区使用中文参数
```

### 音色ID映射

已支持以下格式的音色ID：
- 中文描述：`沉稳`、`浑厚`、`清脆`等
- NihalGazi ID：`alloy`、`echo`、`nova`等
- 数字ID：`voice_01` ~ `voice_13`

## 配置对比

### 魔搭社区配置（推荐）

**优点：**
- ✅ 国内访问速度快
- ✅ 无需代理，配置简单
- ✅ 稳定性高
- ✅ 已验证可用

**缺点：**
- ⚠️ 使用中文API参数（需要特定配置）

**配置：**
```env
INDEXTTS2_GRADIO_SPACE=https://indexteam-indextts-2-demo.ms.show
PROXY_ENABLED=false
```

```python
# indextts2_gradio_service.py
emo_control_method="与音色参考音频相同",
```

### HuggingFace官方配置（备选）

**优点：**
- ✅ 官方标准接口
- ✅ 使用英文参数

**缺点：**
- ❌ 需要代理访问
- ❌ WebSocket连接不稳定
- ❌ 配置复杂

**配置：**
```env
INDEXTTS2_GRADIO_SPACE=IndexTeam/IndexTTS-2-Demo
PROXY_ENABLED=true
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```

```python
# indextts2_gradio_service.py
emo_control_method="Same as the voice reference",
```

## 代理实现（已完成）

### 1. 启动时配置 (main.py:4-26)

```python
# 在所有导入之前设置代理环境变量
from dotenv import load_dotenv
load_dotenv()

if os.getenv('PROXY_ENABLED', 'false').lower() == 'true':
    http_proxy = os.getenv('HTTP_PROXY', '')
    https_proxy = os.getenv('HTTPS_PROXY', '')

    if http_proxy:
        os.environ['HTTP_PROXY'] = http_proxy
    if https_proxy:
        os.environ['HTTPS_PROXY'] = https_proxy

    # 禁用SSL验证
    os.environ['GRADIO_SSL_VERIFY'] = 'false'
```

### 2. httpx代理补丁 (indextts2_gradio_service.py:30-74)

```python
class PatchedClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        kwargs['verify'] = False
        if 'HTTP_PROXY' in os.environ:
            proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
            kwargs['proxies'] = {
                'http://': proxy,
                'https://': proxy,
            }
        super().__init__(*args, **kwargs)
```

### 3. 运行时代理设置 (indextts2_gradio_service.py:153-163)

```python
async def initialize_client(self, max_retries: int = 3):
    # 配置代理（如果启用）
    if getattr(settings, 'proxy_enabled', False):
        http_proxy = getattr(settings, 'http_proxy', '')
        https_proxy = getattr(settings, 'https_proxy', '')

        if http_proxy:
            os.environ['HTTP_PROXY'] = http_proxy
        if https_proxy:
            os.environ['HTTPS_PROXY'] = https_proxy
```

## 测试验证

### 魔搭社区访问测试
```bash
python test_modelscope.py
# ✅ 连接成功！
```

### 基础代理测试
```bash
python test_basic_proxy.py
# ✅ HTTP/HTTPS代理工作正常
# ❌ Gradio WebSocket连接超时
```

## 快速切换指南

### 切换到魔搭社区（当前配置）
```env
INDEXTTS2_GRADIO_SPACE=https://indexteam-indextts-2-demo.ms.show
PROXY_ENABLED=false
```
```python
emo_control_method="与音色参考音频相同",
```

### 切换到HuggingFace（需要代理）
```env
INDEXTTS2_GRADIO_SPACE=IndexTeam/IndexTTS-2-Demo
PROXY_ENABLED=true
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```
```python
emo_control_method="Same as the voice reference",
```

## 故障排查

### 问题1：连接超时
- 检查网络连接
- 验证INDEXTTS2_GRADIO_SPACE配置
- 尝试切换到魔搭社区

### 问题2：API参数错误
- 魔搭社区：使用中文参数 `"与音色参考音频相同"`
- HuggingFace：使用英文参数 `"Same as the voice reference"`

### 问题3：音色ID无法识别
- 支持的格式：中文描述、NihalGazi ID、voice_XX数字ID
- 查看完整映射表：`docs/IndexTTS2_API_Migration.md`

### 问题4：代理不工作
- 确认代理服务运行：`netstat -an | findstr 7897`
- 验证PROXY_ENABLED=true
- 检查HTTP_PROXY和HTTPS_PROXY配置

## 重启服务

配置修改后需要重启服务：
```bash
# Windows
# 停止当前服务 (Ctrl+C)
python run_server.py

# 或使用start.bat
start.bat
```

服务启动时会显示：
```
[启动] 代理配置已应用  # 如果PROXY_ENABLED=true
```

## 参考文档

- 完整迁移文档：`docs/IndexTTS2_API_Migration.md`
- 代理配置指南：`docs/Proxy_Configuration_Guide.md`
- 当前配置：魔搭社区（推荐）

## 当前状态

✅ **已完成：**
- 环境变量代理配置
- httpx代理补丁
- 启动时代理设置
- 魔搭社区访问验证
- voice_XX音色ID映射
- API参数适配

✅ **当前配置：**
- TTS引擎：`indextts2_gradio`
- API空间：魔搭社区 `https://indexteam-indextts-2-demo.ms.show`
- 代理：禁用（魔搭社区无需代理）
- API参数：中文 `"与音色参考音频相同"`

🎯 **推荐使用魔搭社区配置，无需代理，访问稳定快速！**
