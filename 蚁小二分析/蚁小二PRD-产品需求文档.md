# 蚁小二 4.0 — 产品需求文档 (PRD)

> **基于逆向工程分析** | 版本 4.13.19 | 分析时间 2026-06-29

---

## 一、产品概述

### 1.1 产品定位

**蚁小二**是一款**多平台内容一键发布桌面工具**，帮助内容创作者将文章、视频、图文等内容快速发布到多个社交媒体平台。

### 1.2 目标用户

- 内容创作者（自媒体、博主、UP主）
- MCN 机构
- 品牌营销团队
- 个人 IP 运营者

### 1.3 核心价值

| 价值 | 说明 |
|------|------|
| **效率提升** | 一次编辑，多平台发布 |
| **数据聚合** | 统一查看各平台数据 |
| **账号管理** | 同平台多账号切换 |
| **内容管理** | 统一管理所有平台内容 |

---

## 二、功能需求

### 2.1 多平台发布

#### 2.1.1 支持平台

| 平台 | 内容类型 | 集成深度 | 优先级 |
|------|----------|----------|--------|
| **小红书** | 笔记、视频 | ⭐⭐⭐⭐⭐ | P0 |
| **抖音** | 视频、图文 | ⭐⭐⭐⭐ | P0 |
| **视频号** | 视频、图文 | ⭐⭐⭐⭐ | P0 |
| **B站** | 视频、专栏 | ⭐⭐⭐⭐ | P1 |
| **微博** | 图文 | ⭐⭐⭐ | P1 |
| **知乎** | 文章 | ⭐⭐⭐ | P2 |
| **公众号** | 文章 | ⭐⭐⭐ | P2 |

#### 2.1.2 发布流程

```
用户编辑内容
    ↓
选择目标平台
    ↓
选择账号（同平台多账号）
    ↓
配置发布参数（定时、标签、封面等）
    ↓
一键发布
    ↓
实时同步发布状态
```

#### 2.1.3 核心功能点

| 功能 | 说明 | 优先级 |
|------|------|--------|
| **批量发布** | 同一内容发布到多个平台 | P0 |
| **定时发布** | 设置发布时间 | P0 |
| **多账号管理** | 同平台多个账号 | P0 |
| **内容适配** | 自动适配各平台格式 | P1 |
| **封面生成** | 自动生成或选择封面 | P1 |
| **标签管理** | 平台标签/话题管理 | P1 |

### 2.2 小红书深度集成

#### 2.2.1 API 集成

```javascript
// 核心 API 端点
POST /web_api/sns/v5/creator/note/user/posted    // 获取已发布笔记
POST /web_api/sns/capa/postgw/note/delete        // 删除笔记
GET  /api/galaxy/creator/datacenter/note/analyze/list  // 数据分析
GET  /api/galaxy/v2/creator/datacenter/account/base    // 账号概览
```

#### 2.2.2 功能清单

| 功能 | 说明 | 优先级 |
|------|------|--------|
| **笔记发布** | 图文笔记发布 | P0 |
| **视频上传** | 分片上传视频 | P0 |
| **笔记管理** | 查看、编辑、删除笔记 | P0 |
| **数据分析** | 查看笔记数据（阅读、点赞、收藏等） | P1 |
| **好友管理** | 查看好友列表 | P2 |
| **位置管理** | 选择发布位置 | P2 |
| **话题管理** | 创建和管理话题 | P2 |

#### 2.2.3 视频上传流程

```javascript
// 1. 获取上传凭证
POST https://{uploadAddr}/{fileId}?uploads
Header: x-cos-security-token: {token}

// 2. 分片上传
PUT https://{uploadAddr}/{fileId}?partNumber={N}&uploadId={uploadId}
Body: Buffer(chunk)

// 3. 完成上传
POST https://{uploadAddr}/{fileId}?uploadId={uploadId}
Body: CompleteMultipartUpload XML
```

### 2.3 数据分析

#### 2.3.1 数据维度

| 维度 | 说明 | 数据来源 |
|------|------|----------|
| **粉丝数据** | 总粉丝数、涨粉趋势 | 小红书 API |
| **互动数据** | 点赞、收藏、评论、弹幕 | 小红书 API |
| **观看数据** | 观看次数、观看时长 | 小红书 API |
| **分享数据** | 笔记分享次数 | 小红书 API |
| **主页数据** | 主页访客数 | 小红书 API |

#### 2.3.2 数据展示

```javascript
// 数据结构
{
    name: "总粉丝数",
    key: "totalFansCount",
    value: "12,345",
    list: [
        { date: "2026-06-01", value: 100 },
        { date: "2026-06-02", value: 150 },
        // ...
    ]
}
```

### 2.4 实时通信

#### 2.4.1 Socket.IO 集成

```javascript
// 服务端事件
- sync-content         // 同步内容列表
- publish-status       // 发布状态更新
- publish-complete     // 发布完成通知
- sync-progress        // 同步进度

// 客户端事件
- sync-content         // 接收内容列表
- publish-status       // 接收发布状态
- publish-complete     // 接收发布完成
```

#### 2.4.2 使用场景

| 场景 | 事件 | 说明 |
|------|------|------|
| **内容同步** | sync-content | 从平台拉取最新内容 |
| **发布监控** | publish-status | 实时显示发布进度 |
| **发布完成** | publish-complete | 通知用户发布结果 |
| **数据更新** | sync-progress | 实时更新数据统计 |

---

## 三、技术架构

### 3.1 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **桌面框架** | Electron | 跨平台桌面应用 |
| **前端** | React 19 + TypeScript | UI 框架 |
| **构建工具** | Vite (渲染进程) + Webpack (主进程) | 构建打包 |
| **通信** | Socket.IO | 实时通信 |
| **HTTP** | Axios | 网络请求 |
| **验证** | Zod | 数据验证 |
| **样式** | Tailwind CSS | CSS 框架 |
| **图标** | Lucide React | 图标库 |

### 3.2 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    蚁小二 4.0 (Electron)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Main      │  │   Preload    │  │    Renderer      │   │
│  │  (主进程)   │  │  (预加载)    │  │   (渲染进程)     │   │
│  │  Node.js    │  │  桥接层      │  │   React 19       │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    平台 API 集成                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  小红书     │  │  抖音        │  │  视频号          │   │
│  │  完整 API   │  │  完整 API    │  │  完整 API        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  B站        │  │  微博        │  │  知乎            │   │
│  │  完整 API   │  │  完整 API    │  │  完整 API        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    通信层                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Socket.IO (实时通信)                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 数据流

```
用户操作
    ↓
渲染进程 (React)
    ↓ IPC / Socket.IO
主进程 (Node.js)
    ↓
平台 API (小红书/抖音/视频号...)
    ↓
数据存储 (本地)
    ↓
实时同步 (Socket.IO)
    ↓
UI 更新
```

---

## 四、API 设计

### 4.1 小红书 API

#### 4.1.1 内容管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/web_api/sns/v5/creator/note/user/posted` | POST | 获取已发布笔记 |
| `/web_api/sns/capa/postgw/note/delete` | POST | 删除笔记 |
| `/api/galaxy/creator/datacenter/note/analyze/list` | GET | 笔记数据分析 |

#### 4.1.2 用户信息

| 端点 | 方法 | 说明 |
|------|------|------|
| `/web_api/sns/v5/user/info` | GET | 获取用户信息 |
| `/web_api/sns/v5/user/friend/list` | GET | 获取好友列表 |

#### 4.1.3 位置和话题

| 端点 | 方法 | 说明 |
|------|------|------|
| `/web_api/sns/v5/poi/list` | GET | 获取位置列表 |
| `/web_api/sns/v5/topic/list` | GET | 获取话题列表 |
| `/web_api/sns/v5/topic/create` | POST | 创建话题 |

#### 4.1.4 视频上传

| 端点 | 方法 | 说明 |
|------|------|------|
| `https://{uploadAddr}/{fileId}?uploads` | POST | 初始化上传 |
| `https://{uploadAddr}/{fileId}?partNumber={N}` | PUT | 分片上传 |
| `https://{uploadAddr}/{fileId}?uploadId={id}` | POST | 完成上传 |

### 4.2 内部 API

#### 4.2.1 内容管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/content/list` | GET | 获取内容列表 |
| `/api/content/sync` | POST | 同步平台内容 |
| `/api/content/delete` | POST | 删除内容 |

#### 4.2.2 发布管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/publish/create` | POST | 创建发布任务 |
| `/api/publish/status` | GET | 查询发布状态 |
| `/api/publish/cancel` | POST | 取消发布 |

#### 4.2.3 数据分析

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/analytics/overview` | GET | 获取数据概览 |
| `/api/analytics/trend` | GET | 获取趋势数据 |
| `/api/analytics/comparison` | GET | 获取对比数据 |

---

## 五、数据模型

### 5.1 用户模型

```typescript
interface User {
    id: string;
    name: string;
    avatar: string;
    platforms: PlatformAccount[];
}
```

### 5.2 平台账号

```typescript
interface PlatformAccount {
    id: string;
    platform: 'xiaohongshu' | 'douyin' | 'weixin_channel' | 'bilibili' | 'weibo' | 'zhihu' | 'gongzhonghao';
    username: string;
    avatar: string;
    cookie: string;
    status: 'active' | 'expired' | 'banned';
}
```

### 5.3 内容模型

```typescript
interface Content {
    id: string;
    title: string;
    body: string;
    images: string[];
    video?: string;
    tags: string[];
    platforms: PlatformTarget[];
    status: 'draft' | 'publishing' | 'published' | 'failed';
    scheduledAt?: Date;
    publishedAt?: Date;
}
```

### 5.4 发布任务

```typescript
interface PublishTask {
    id: string;
    contentId: string;
    platform: string;
    accountId: string;
    status: 'pending' | 'publishing' | 'success' | 'failed';
    progress: number;
    error?: string;
    publishedAt?: Date;
}
```

### 5.5 数据统计

```typescript
interface Analytics {
    platform: string;
    period: 'day' | 'week' | 'month';
    metrics: {
        fans: number;
        likes: number;
        collects: number;
        comments: number;
        shares: number;
        views: number;
    };
    trend: TrendPoint[];
}
```

---

## 六、UI/UX 设计

### 6.1 页面结构

```
├── 首页
│   ├── 数据概览
│   ├── 最近发布
│   └── 快捷操作
├── 内容管理
│   ├── 内容列表
│   ├── 内容编辑
│   └── 内容预览
├── 发布中心
│   ├── 发布任务
│   ├── 定时发布
│   └── 发布历史
├── 数据分析
│   ├── 数据概览
│   ├── 趋势分析
│   └── 平台对比
├── 账号管理
│   ├── 账号列表
│   ├── 账号绑定
│   └── 账号状态
└── 设置
    ├── 通用设置
    ├── 代理设置
    └── 关于
```

### 6.2 核心页面

#### 6.2.1 首页

```
┌─────────────────────────────────────────────────────────────┐
│  蚁小二 4.0                                    [设置] [托盘] │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    数据概览                          │   │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐           │   │
│  │  │ 粉丝 │  │ 点赞 │  │ 收藏 │  │ 评论 │           │   │
│  │  │ 12K  │  │ 5.2K │  │ 3.1K │  │ 1.8K │           │   │
│  │  └──────┘  └──────┘  └──────┘  └──────┘           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    最近发布                          │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │ [封面] 标题...                    小红书 ✅  │   │   │
│  │  │ [封面] 标题...                    抖音 ✅    │   │   │
│  │  │ [封面] 标题...                    B站 ⏳     │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [+] 新建内容    [📊 数据分析]    [📤 批量发布]      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 6.2.2 发布中心

```
┌─────────────────────────────────────────────────────────────┐
│  发布中心                                        [返回]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  选择平台                                            │   │
│  │  ☑ 小红书   ☑ 抖音   ☐ 视频号   ☐ B站             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  选择账号                                            │   │
│  │  小红书: [账号1 ▼] [账号2] [+添加]                   │   │
│  │  抖音:   [账号1 ▼] [+添加]                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  内容预览                                            │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │                                              │   │   │
│  │  │              内容预览区域                     │   │   │
│  │  │                                              │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  发布设置                                            │   │
│  │  ☐ 定时发布    时间: [2026-06-30 10:00]             │   │
│  │  ☐ 添加话题    话题: [#日常 #分享]                   │   │
│  │  ☐ 添加位置    位置: [北京]                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              [📤 立即发布]                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 七、非功能需求

### 7.1 性能要求

| 指标 | 要求 |
|------|------|
| **启动时间** | < 3 秒 |
| **发布响应** | < 5 秒 |
| **数据同步** | < 10 秒 |
| **内存占用** | < 500MB |
| **CPU 占用** | < 10% (空闲时) |

### 7.2 安全要求

| 要求 | 说明 |
|------|------|
| **Cookie 加密** | 本地存储的 Cookie 需加密 |
| **API Key 保护** | 不硬编码在代码中 |
| **数据传输** | 使用 HTTPS |
| **代理支持** | 支持 HTTP/HTTPS 代理 |

### 7.3 兼容性要求

| 平台 | 要求 |
|------|------|
| **Windows** | Windows 10+ |
| **macOS** | macOS 12+ |
| **Linux** | Ubuntu 20.04+ |

---

## 八、技术实现

### 8.1 视频上传（小红书）

```javascript
// 分片上传实现
class VideoUploader {
    async upload(file, token, uploadAddr) {
        // 1. 初始化上传
        const uploadId = await this.initUpload(token, uploadAddr, file.id);
        
        // 2. 分片上传
        const chunkSize = 5 * 1024 * 1024; // 5MB
        const chunks = this.splitFile(file, chunkSize);
        const etagMap = new Map();
        
        for (let i = 0; i < chunks.length; i++) {
            const etag = await this.uploadChunk(chunks[i], i + 1, uploadId, token, uploadAddr);
            etagMap.set(i + 1, etag);
        }
        
        // 3. 完成上传
        await this.completeUpload(uploadId, etagMap, token, uploadAddr);
    }
}
```

### 8.2 实时通信

```javascript
// Socket.IO 集成
class RealtimeManager {
    constructor() {
        this.socket = io('http://localhost:PORT');
    }
    
    // 监听内容同步
    onSyncContent(callback) {
        this.socket.on('sync-content', callback);
    }
    
    // 监听发布状态
    onPublishStatus(callback) {
        this.socket.on('publish-status', callback);
    }
    
    // 发送发布请求
    emitPublish(data) {
        this.socket.emit('publish', data);
    }
}
```

### 8.3 数据分析

```javascript
// 数据聚合
class AnalyticsService {
    async getOverview(platform, period) {
        const data = await this.fetchData(platform, period);
        return {
            fans: data.fans_count,
            likes: data.like_count,
            collects: data.collect_count,
            comments: data.comment_count,
            shares: data.share_count,
            views: data.view_count
        };
    }
    
    async getTrend(platform, metric, days) {
        const data = await this.fetchTrend(platform, metric, days);
        return data.map(item => ({
            date: item.date,
            value: item.count
        }));
    }
}
```

---

## 九、部署方案

### 9.1 打包配置

```yaml
# electron-builder.yml
appId: com.yixiaoer.desktop
productName: 蚁小二4.0
directories:
  output: dist
files:
  - packages/**/*
  - package.json
win:
  target: nsis
  icon: assets/icon.ico
mac:
  target: dmg
  icon: assets/icon.icns
linux:
  target: AppImage
  icon: assets/icon.png
```

### 9.2 更新配置

```yaml
# app-update.yml
provider: generic
channel: win32-x64
url: https://lite-download.yixiaoer.cn/latest-open
updaterCacheDirName: yixiaoer-updater
```

---

## 十、总结

蚁小二是一款**功能完整的多平台内容发布工具**，核心特点：

1. **多平台支持**：7+ 平台完整集成
2. **实时通信**：Socket.IO 实时状态同步
3. **数据分析**：完整的数据仪表板
4. **视频处理**：分片上传、格式转换

**技术亮点**：
- Electron + React 19 现代技术栈
- Socket.IO 实时通信
- 完整的平台 API 集成
- 分片视频上传

**可借鉴的功能**：
1. Socket.IO 实时通信机制
2. 分片视频上传方案
3. 数据分析仪表板设计
4. 代理支持配置
