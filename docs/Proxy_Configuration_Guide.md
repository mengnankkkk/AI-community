# IndexTTS-2 Gradio 代理配置指南

## 问题背景

HuggingFace官方空间 `IndexTeam/IndexTTS-2-Demo` 在国内需要代理访问。本指南说明如何配置代理以使用Gradio API。

## 配置步骤

### 1. 环境变量配置 (.env)

```env
# IndexTTS2 Gradio配置
INDEXTTS2_GRADIO_SPACE=IndexTeam/IndexTTS-2-Demo

# 代理配置
PROXY_ENABLED=true
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```

### 2. 代码实现

已在 `indextts2_gradio_service.py` 中实现：
- SSL验证禁用
- httpx代理补丁
- 环境变量代理配置

## 验证结果

### ✅ 代理服务正常
```bash
python test_basic_proxy.py
# [+] HTTP 请求成功!
# [+] HTTPS 请求成功! (状态码: 200)
# [+] 代理工作正常!
```

### ⚠️ Gradio WebSocket连接问题

**症状：**
```
Loaded as API: https://indexteam-indextts-2-demo.hf.space ✔
[-] 连接失败: _ssl.c:989: The handshake operation timed out
```

**原因：**
- Gradio Client内部使用WebSocket进行通信
- WebSocket连接可能不支持标准HTTP代理
- SSL握手在代理环境下超时

## 解决方案

### 方案1：使用魔搭社区（推荐）

**优点：** 国内访问快，无需代理

```env
TTS_ENGINE=indextts2_gradio
INDEXTTS2_GRADIO_SPACE=https://indexteam-indextts-2-demo.ms.show
PROXY_ENABLED=false
```

**注意：** 需将API参数改回中文
```python
# indextts2_gradio_service.py:249
emo_control_method="与音色参考音频相同",  # 魔搭使用中文
```

### 方案2：SOCKS5代理（待测试）

某些SOCKS5代理可能支持WebSocket：

```env
# 如果您的代理支持SOCKS5
HTTP_PROXY=socks5://127.0.0.1:7897
HTTPS_PROXY=socks5://127.0.0.1:7897
```

需要安装：
```bash
pip install httpx[socks]
```

### 方案3：本地部署Gradio Space

克隆并本地运行IndexTTS-2-Demo：

```bash
git clone https://huggingface.co/spaces/IndexTeam/IndexTTS-2-Demo
cd IndexTTS-2-Demo
pip install -r requirements.txt
python app.py
```

然后修改配置：
```env
INDEXTTS2_GRADIO_SPACE=http://127.0.0.1:7860
PROXY_ENABLED=false
```

### 方案4：使用本地模型（最稳定）

如果已下载IndexTTS-2模型：

```env
TTS_ENGINE=indextts2  # 使用本地模型
INDEXTTS_MODEL_DIR=E:/path/to/IndexTTS-2
PROXY_ENABLED=false
```

## 代理调试命令

### 检查代理服务
```bash
# Windows
netstat -an | findstr 7897

# Linux/Mac
netstat -an | grep 7897
```

### 测试代理连接
```bash
# 基础代理测试
python test_basic_proxy.py

# Gradio连接测试
python test_proxy_connection.py
```

### 手动测试代理
```bash
# 使用curl测试
curl -x http://127.0.0.1:7897 https://huggingface.co

# 使用Python测试
python -c "import httpx; print(httpx.get('https://huggingface.co', proxies={'https://': 'http://127.0.0.1:7897'}, verify=False).status_code)"
```

## 当前状态

- ✅ 环境变量代理配置：已完成
- ✅ httpx代理支持：已实现
- ✅ SSL验证禁用：已配置
- ✅ 基础代理功能：验证通过
- ⚠️ Gradio WebSocket：已知限制

## 推荐配置

**国内用户推荐使用魔搭社区：**

```env
# .env
TTS_ENGINE=indextts2_gradio
INDEXTTS2_GRADIO_SPACE=https://indexteam-indextts-2-demo.ms.show
PROXY_ENABLED=false
```

```python
# indextts2_gradio_service.py:249
emo_control_method="与音色参考音频相同",
```

**国际用户或企业网络：**

```env
# .env
TTS_ENGINE=indextts2_gradio
INDEXTTS2_GRADIO_SPACE=IndexTeam/IndexTTS-2-Demo
PROXY_ENABLED=false  # 直连或企业代理自动配置
```

## 参考资料

- [Gradio Client文档](https://www.gradio.app/docs/python-client)
- [httpx代理配置](https://www.python-httpx.org/advanced/#http-proxying)
- [魔搭社区](https://modelscope.cn/)

## 清理测试文件

完成配置后可删除测试文件：
```bash
rm test_proxy_connection.py
rm test_basic_proxy.py
```
