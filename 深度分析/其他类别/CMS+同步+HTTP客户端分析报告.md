# CMS + 同步云服务 + HTTP 客户端分析报告

> **分析时间**：2026-06-30
> **目标项目**：Multi-Publish（Electron + Vue 3 多平台内容发布工具）
> **分析类别**：CMS（25个）+ 同步/云服务（28个）+ HTTP 客户端（58个）

---

## 一、CMS 内容管理系统

### 1.1 核心项目

| 项目 | Stars | 语言 | 关联度 |
|------|-------|------|--------|
| Strapi | 72,572 | TypeScript | ⭐⭐⭐⭐⭐ |
| Wagtail | 20,373 | Python | ⭐⭐⭐⭐ |
| TinaCMS | 13,603 | TypeScript | ⭐⭐⭐⭐ |
| Gridea | 10,277 | TypeScript/Vue/Electron | ⭐⭐⭐⭐⭐ |
| KeystoneJS | 14,513 | Node.js | ⭐⭐⭐ |

### 1.2 Strapi — Headless CMS 最佳选择

```typescript
// 内容类型定义
const schema = {
  collections: [{
    label: '文章', name: 'post', path: 'content/posts',
    fields: [
      { type: 'string', name: 'title', label: '标题', isTitle: true },
      { type: 'rich-text', name: 'body', label: '正文', isBody: true },
    ],
  }],
};
```

### 1.3 Gridea — 与 Multi-Publish 技术栈最相似

Electron + Vue 架构，支持多平台发布（GitHub Pages, Netlify）

```typescript
class ContentManager {
  private posts: Post[] = [];
  createPost(post: Omit<Post, 'id'>): Post {
    const newPost = { ...post, id: this.generateId() };
    this.posts.push(newPost);
    return newPost;
  }
  async publishPost(id: string): Promise<boolean> {
    const post = this.posts.find(p => p.id === id);
    if (post) { await this.publishToGitHub(post); await this.publishToNetlify(post); return true; }
    return false;
  }
}
```

### 1.4 Wagtail StreamField

```python
from wagtail.fields import StreamField
from wagtail.blocks import CharBlock, TextBlock, ImageBlock

class ArticlePage(Page):
    body = StreamField([
        ('heading', CharBlock()),
        ('paragraph', TextBlock()),
        ('image', ImageBlock()),
    ], use_json_field=True)
```

---

## 二、同步/云服务

### 2.1 核心项目

| 项目 | Stars | 语言 | 关联度 |
|------|-------|------|--------|
| Rclone | 58,073 | Go | ⭐⭐⭐⭐⭐ |
| Remotely-Save | 7,730 | TypeScript | ⭐⭐⭐⭐ |
| CouchDB | 6,908 | Erlang/JS | ⭐⭐⭐⭐ |

### 2.2 Rclone — 云存储同步标准

```go
func (r *RcloneManager) SyncToCloud(localPath, remotePath string) error {
    cmd := exec.Command("rclone", "sync", localPath, remotePath, "--config", r.configPath, "-v")
    return cmd.Run()
}
```

### 2.3 Remotely-Save — 冲突解决

```typescript
interface ConflictResolver {
  resolve(local: Content, remote: Content, strategy: 'local' | 'remote' | 'merge'): Content;
}

class SmartConflictResolver implements ConflictResolver {
  resolve(local, remote, strategy) {
    switch (strategy) {
      case 'local': return local;
      case 'remote': return remote;
      case 'merge': return { ...remote, ...local, updatedAt: new Date().toISOString() };
    }
  }
}
```

### 2.4 CouchDB/PouchDB — 离线同步

```javascript
class ContentSyncManager {
  constructor() {
    this.localDB = new PouchDB('local-content');
    this.remoteDB = new PouchDB('http://remote-server/content');
  }
  enableSync() {
    this.localDB.sync(this.remoteDB, { live: true, retry: true })
      .on('change', (change) => console.log('内容变更:', change));
  }
}
```

---

## 三、HTTP 客户端

### 3.1 核心项目

| 项目 | Stars | 特性 | 关联度 |
|------|-------|------|--------|
| Axios | 109,224 | 拦截器+取消 | ⭐⭐⭐⭐⭐ 已用 |
| Ky | 16,957 | 轻量+重试 | ⭐⭐⭐⭐ 已用 |
| Got | 14,922 | 重试+流式 | ⭐⭐⭐⭐ |
| Undici | 7,637 | 高性能+HTTP/2 | ⭐⭐⭐⭐ |
| Yaak | 18,802 | 桌面API客户端 | ⭐⭐⭐ 参考 |

### 3.2 Got — 重试+流式

```typescript
import got from 'got';
const client = got.extend({
  prefixUrl: 'https://api.example.com',
  timeout: { request: 10000, response: 30000 },
  retry: { limit: 5, calculateDelay: ({ attemptCount }) => attemptCount * 1000 },
});
const stream = client.stream('large-file.zip');
stream.pipe(fs.createWriteStream('local-file.zip'));
```

### 3.3 Undici — 高性能

```javascript
const { Client } = require('undici');
const client = new Client('https://api.example.com', {
  keepAliveTimeout: 30000, connections: 10, pipelining: 1,
});
```

---

## 四、选型建议

| 场景 | 推荐方案 |
|------|---------|
| 内容建模 | Strapi 内容类型系统 |
| 桌面 CMS | Gridea 架构（Electron + Vue） |
| 多格式内容 | Wagtail StreamField |
| 云同步 | Rclone + Remotely-Save 冲突解决 |
| 离线支持 | CouchDB/PouchDB 同步协议 |
| 基础 HTTP | Axios（已有） |
| 轻量请求 | Ky（已有） |
| 重试机制 | Got 指数退避 |
| 高性能 | Undici 连接池 |

---

*报告生成时间：2026-06-30*
