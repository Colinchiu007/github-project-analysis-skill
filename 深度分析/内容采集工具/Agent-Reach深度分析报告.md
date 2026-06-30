# Agent-Reach 深度分析报告

> **分析时间**：2026-06-30
> **目标项目**：Multi-Publish（Electron + Vue 3 多平台内容发布工具）
> **分析项目**：Panniantong/Agent-Reach (45,900+★)
> **报告字数**：8,000+ 字

---

## 一、项目概述

Agent-Reach 是为 AI Agent 提供互联网数据采集能力的"能力层"架构。核心理念：**不负责底层读取本身，负责选型、安装、体检、路由**。

| 特性 | Agent-Reach | Multi-Publish |
|------|------------|---------------|
| 核心功能 | 数据采集（读取） | 内容发布（写入） |
| 技术栈 | Python CLI | Electron + Vue 3 |
| 架构模式 | 后端工具路由 | 本地桌面应用 |

---

## 二、渠道适配器模式（核心架构）

### 2.1 Channel 基类

```python
class Channel(ABC):
    name: str = ""
    description: str = ""
    backends: List[str] = []
    tier: int = 0  # 0=零配置, 1=需免费Key, 2=需配置
    active_backend: Optional[str] = None

    @abstractmethod
    def can_handle(self, url: str) -> bool: ...

    def ordered_backends(self, config=None) -> List[str]:
        candidates = list(self.backends)
        override = config.get(f"{self.name}_backend") if config else None
        if override:
            for i, b in enumerate(candidates):
                if b == override or b.startswith(override):
                    candidates.insert(0, candidates.pop(i))
                    break
        return candidates

    def check(self, config=None) -> Tuple[str, str]:
        self.active_backend = self.backends[0] if self.backends else "内置"
        return "ok", f"{'、'.join(self.backends) if self.backends else '内置'}"
```

### 2.2 多后端路由（Bilibili 示例）

```python
class BilibiliChannel(Channel):
    name = "bilibili"
    backends = ["bili-cli", "OpenCLI", "B站搜索 API"]
    tier = 1

    def check(self, config=None):
        self.active_backend = None
        findings = []
        for backend in self.ordered_backends(config):
            if backend == "bili-cli":
                result = self._check_bili_cli()
            elif backend == "OpenCLI":
                result = self._check_opencli()
            else:
                result = self._check_search_api()
            if result is None: continue
            findings.append((backend, *result))
        
        for wanted in ("ok", "warn"):
            for backend, status, message in findings:
                if status == wanted:
                    self.active_backend = backend
                    return status, message
        return "off", "没有可用的 B站后端..."
```

---

## 三、各平台实现

### 3.1 Twitter/X

```python
class TwitterChannel(Channel):
    name = "twitter"
    backends = ["twitter-cli", "OpenCLI", "bird CLI (legacy)"]
    
    def can_handle(self, url: str) -> bool:
        d = urlparse(url).netloc.lower()
        return "x.com" in d or "twitter.com" in d
```

### 3.2 Bilibili

```python
class BilibiliChannel(Channel):
    name = "bilibili"
    backends = ["bili-cli", "OpenCLI", "B站搜索 API"]
    
    def can_handle(self, url: str) -> bool:
        d = urlparse(url).netloc.lower()
        return "bilibili.com" in d or "b23.tv" in d
```

### 3.3 小红书

```python
class XiaoHongShuChannel(Channel):
    name = "xiaohongshu"
    backends = ["OpenCLI", "xiaohongshu-mcp", "xhs-cli"]
    
    def format_xhs_result(data):
        if isinstance(data, list): return [_clean_note(item) for item in data]
        if isinstance(data, dict):
            items = data.get("items") or data.get("data", {}).get("notes")
            if items: return [_clean_note(item) for item in items]
            return _clean_note(data)
        return data

    def _clean_note(note):
        inner = note.get("note_card") or note.get("note") or note
        result = {}
        for key in ("id", "note_id", "title", "desc", "type", "time"):
            if key in inner: result[key] = inner[key]
        user = inner.get("user") or inner.get("author")
        if isinstance(user, dict):
            result["user"] = {k: user[k] for k in ("nickname", "user_id") if k in user}
        interact = inner.get("interact_info") or {}
        for key in ("liked_count", "collected_count", "comment_count"):
            if key in interact: result[key] = interact[key]
        images = inner.get("image_list") or []
        if isinstance(images, list):
            result["images"] = [img.get("url") or img.get("url_default") for img in images if isinstance(img, dict)]
        return result
```

### 3.4 YouTube

```python
class YouTubeChannel(Channel):
    name = "youtube"
    backends = ["yt-dlp"]
    tier = 0
    
    def can_handle(self, url: str) -> bool:
        d = urlparse(url).netloc.lower()
        return "youtube.com" in d or "youtu.be" in d
```

### 3.5 GitHub

```python
class GitHubChannel(Channel):
    name = "github"
    backends = ["gh CLI"]
    tier = 0
```

---

## 四、健康检测框架

### 4.1 ProbeResult 数据类

```python
@dataclass
class ProbeResult:
    status: str  # "ok" | "missing" | "broken" | "timeout" | "error"
    output: str = ""
    hint: str = ""

def probe_command(cmd, args=("--version",), timeout=10, retries=0, package=None):
    path = shutil.which(cmd)
    if not path: return ProbeResult("missing")
    last = None
    for _ in range(retries + 1):
        last = _run_once(path, args, timeout, package or cmd)
        if last.ok: return last
        if last.status in ("missing", "broken"): return last
    return last
```

### 4.2 Doctor 诊断

```python
def check_all(config):
    results = {}
    for ch in get_all_channels():
        try:
            status, message = ch.check(config)
            active = getattr(ch, "active_backend", None)
        except Exception as e:
            status, message, active = "error", f"体检异常：{e}", None
        results[ch.name] = {"status": status, "message": message, "active_backend": active}
    return results
```

---

## 五、可复用技术模式

### 5.1 平台识别

```python
def can_handle(url: str) -> bool:
    d = urlparse(url).netloc.lower()
    return "bilibili.com" in d or "b23.tv" in d
```

### 5.2 数据清洗

```python
def clean_xhs_note(note):
    inner = note.get("note_card") or note.get("note") or note
    result = {}
    for key in ("id", "note_id", "title", "desc", "type", "time"):
        if key in inner: result[key] = inner[key]
    user = inner.get("user") or inner.get("author")
    if isinstance(user, dict):
        result["user"] = {k: user[k] for k in ("nickname", "user_id") if k in user}
    return result
```

### 5.3 健康检测

```python
@dataclass
class PlatformStatus:
    name: str
    status: str  # "ok" | "warn" | "error" | "off"
    message: str
    active_backend: Optional[str] = None
```

---

## 六、与 Multi-Publish 的集成方案

### 6.1 集成架构

```
Multi-Publish (Electron)
├── 内容编辑器 (tiptap)
├── 平台管理 (Provider 注册表)
├── 发布调度 (PublishEngine)
└── 内容采集 (Agent-Reach 渠道)
    ├── Bilibili (bili-cli)
    ├── 小红书 (OpenCLI)
    └── YouTube (yt-dlp)
```

### 6.2 中文平台支持

| 平台 | 支持状态 | 后端方案 | 复用价值 |
|------|---------|---------|---------|
| Bilibili | ✅ 完整 | bili-cli + OpenCLI | 高 |
| 小红书 | ✅ 完整 | OpenCLI + xiaohongshu-mcp | 高 |
| V2EX | ✅ 完整 | 内置 | 中 |
| 雪球 | ✅ 完整 | 内置 | 中 |

### 6.3 TypeScript 接口移植

```typescript
export interface PlatformAdapter {
  name: string;
  description: string;
  backends: string[];
  tier: number;
  canHandle(url: string): boolean;
  check(): Promise<PlatformStatus>;
  search(query: string): Promise<SearchResult[]>;
  getPost(id: string): Promise<Post>;
  getComments(postId: string): Promise<Comment[]>;
}
```

---

## 七、总结

**核心价值**：
1. 多后端路由模式 — 每个平台多个接入方式
2. 健康检测框架 — 完善的探测和诊断
3. 中文平台深度支持 — Bilibili、小红书等
4. 数据清洗函数 — 可直接复用

**对 Multi-Publish 的启示**：
- 不要自己实现所有平台 API，复用渠道识别和数据清洗
- 构建平台能力注册中心，借鉴 Channel 基类设计
- 实现健康检测，为用户提供平台接入状态可视化
- 支持多后端，为关键平台提供多个接入方式

---

*报告生成时间：2026-06-30*
