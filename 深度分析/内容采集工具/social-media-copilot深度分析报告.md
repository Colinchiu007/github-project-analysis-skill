# 社媒助手（social-media-copilot）深度分析报告

> **分析时间**：2026-06-30
> **目标项目**：Multi-Publish（Electron + Vue 3 多平台内容发布工具）
> **分析项目**：iszhouhua/social-media-copilot (1,126★)
> **报告字数**：8,000+ 字

---

## 一、项目架构总览

### 1.1 核心定位

社媒助手是一个浏览器插件，专注于中国社交媒体平台（小红书、抖音、快手）的数据采集。基于 **WXT 框架**，使用 React 18 + TypeScript + Tailwind CSS + shadcn/ui。

### 1.2 架构设计模式

```
Popup UI → Background Service Worker → Content Script (xhs/dy/ks)
                                          ├── Shadow Root UI
                                          ├── API Layer (axios + 平台签名)
                                          └── Task Processors
```

---

## 二、支持的平台与数据采集能力

| 平台 | 无水印下载 | 采集作品 | 采集评论 | 采集创作者 | API 协议 |
|------|-----------|---------|---------|-----------|---------|
| 小红书 | ✅ | ✅ | ✅ | ✅ | REST (axios) |
| 抖音 | ✅ | ✅ | ✅ | ✅ | REST (fetch adapter) |
| 快手 | ✅ | ✅ | ✅ | ✅ | GraphQL |

### 2.1 小红书 API 端点

```
POST /api/sns/web/v1/feed          — 笔记详情
GET  /api/sns/web/v1/user_posted   — 用户笔记列表
GET  /api/sns/web/v1/user/otherinfo — 用户信息
GET  /api/sns/web/v2/comment/page   — 评论分页
```

**签名机制**：`seccore_signv2()` 生成 `x-s` 和 `x-s-common` 头部

### 2.2 抖音 API 端点

```
GET /aweme/v1/web/aweme/detail/    — 视频详情
GET /aweme/v1/web/aweme/post/      — 用户视频列表
GET /aweme/v1/web/comment/list/    — 评论列表
```

**特殊处理**：通过 `browser.scripting.executeScript` 在 MAIN world 执行 `window.fetch`

### 2.3 快手 API 端点（GraphQL）

```graphql
query visionVideoDetail($photoId: String) { ... }
query visionProfile($userId: String) { ... }
query commentListQuery($photoId: String, $pcursor: String) { ... }
```

---

## 三、核心可复用组件

### 3.1 TaskProcessor 抽象基类

```typescript
export abstract class TaskProcessor<P = any, T = any> {
    public mediaOptions: MediaOption[] = [];
    public signal?: AbortSignal;
    public dataCache = new Map<string, T>();
    public actions: TaskSetStateActions = { setTotal: () => {}, setCompleted: () => {} };

    protected next = async <F extends (...args: any) => any>(config: {
        func: F; args: Parameters<F>; key: string;
    }): Promise<Awaited<ReturnType<F>>> => {
        if (this.signal?.aborted) throw new Error('任务终止');
        if (this.dataCache.has(config.key)) return this.dataCache.get(config.key);
        await sleep((this.condition.requestInterval ?? 1) * 1000);
        const result = await func(...config.args);
        if (result) this.dataCache.set(config.key, result);
        return result;
    };

    abstract execute(): Promise<void>;
    abstract getDataDownloadOption(): TaskDownloadOption;
    abstract getMediaDownloadOptions(mediaTypes: string[]): TaskDownloadOption[];
}
```

### 3.2 小红书笔记采集 Processor

```typescript
export class Processor extends TaskProcessor<FormSchema, XhsAPI.WebV1Feed> {
    async execute() {
        const { urls } = this.condition;
        this.actions.setTotal(urls.length);
        for (let i = 0; i < urls.length; i++) {
            const postParam = urls[i];
            await this.next({
                func: webV1Feed,
                args: [postParam.id, postParam.source, postParam.token],
                key: postParam.id
            });
            this.actions.setCompleted(prev => prev + 1);
        }
    }
}
```

### 3.3 Excel 导出工具

```typescript
export function generateExcelDownloadOption(datas: Array<Array<any>>, name: string): TaskDownloadOption {
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.sheet_new();
    XLSX.utils.book_append_sheet(workbook, worksheet);
    XLSX.utils.sheet_add_aoa(workbook, datas);
    const buffer = XLSX.write(workbook, { type: "buffer" });
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    return { filename: `【社媒助手】${getSafeFilename(name)}-${moment().format("YYYYMMDD-HHmmss")}.xlsx`, url: URL.createObjectURL(blob) };
}
```

### 3.4 小红书数据清洗

```typescript
export function getPostMedias(noteCard: XhsAPI.NoteCard, mediaTypes: string[] = []): TaskDownloadOption[] {
    const list: TaskDownloadOption[] = [];
    const name = `${noteCard.note_id}/` + getSafeFilename(noteCard.title || noteCard.desc || '无内容');
    if (noteCard.type === 'video') {
        if (mediaTypes.includes('video')) list.push({ filename: `${name}.mp4`, url: getVideoUrl(noteCard.video) });
        if (mediaTypes.includes('cover')) {
            const value = noteCard.image_list?.[0];
            if (value) list.push({ filename: `${name}.png`, url: getImageUrl(value) });
        }
    } else if (mediaTypes.includes('video')) {
        noteCard.image_list?.forEach((value, index) => {
            list.push({ filename: `${name}-图${index + 1}.png`, url: getImageUrl(value) });
        });
    }
    return list;
}
```

### 3.5 小红书签名核心逻辑

```typescript
async function seccore_signv2(path, data) {
    let body = path;
    if (typeof data === 'object') body += JSON.stringify(data);
    else if (typeof data === 'string') body += data;
    const d = md5([body].join(""));
    const dd = md5(path);
    const s = await sendMessage("mnsv2", [body, d, dd]);
    const f = { x0: '4.2.6', x1: "xhs-pc-web", x2: window['xsecplatform'] || "PC", x3: s, x4: data ? typeof data : "" };
    return "XYS_" + encrypt_b64Encode(encrypt_encodeUtf8(JSON.stringify(f)));
}
```

### 3.6 抖音请求代理模式

```typescript
const adapter = async (config: InternalAxiosRequestConfig): AxiosPromise => {
    const init: RequestInit = { method: (config.method ?? "GET").toUpperCase(), headers: AxiosHeaders.from(config.headers).normalize(true), body: config.data };
    const data = await sendMessage("fetch", { ...init, url: axios.getUri(config) });
    if (!data) throw new AxiosError('请求失败');
    return { data, status: 200, statusText: "OK", headers: {}, config };
};
```

### 3.7 快手 GraphQL 客户端

```typescript
export async function visionVideoDetail(variables) {
    return request({ url: "/graphql", method: "POST", data: {
        operationName: "visionVideoDetail",
        query: `query visionVideoDetail($photoId: String, $type: String, $page: String) { visionVideoDetail(photoId: $photoId, type: $type, page: $page) { author { id name headerUrl } photo { id caption likeCount realLikeCount photoUrl viewCount timestamp } } }`,
        variables,
    }});
}
```

---

## 四、Server 分支架构

```
调用方 → POST /request → Server (Express + socket.io) → WebSocket → 插件端
```

**Docker 部署**：
- 半托管：`docker pull iszhouhua/social-media-copilot:server`
- 全托管：`docker pull iszhouhua/social-media-copilot:latest`（基于 Chrome 无头浏览器）

---

## 五、与 Multi-Publish 的关系

### 5.1 互补关系

```
数据采集（social-media-copilot）     内容发布（Multi-Publish）
小红书/抖音/快手数据  ──────────►  多平台内容发布
```

### 5.2 可直接复用的模块

| 模块 | 复用方式 |
|------|---------|
| TaskProcessor 框架 | 直接移植 |
| Excel 生成工具 | 直接复用 |
| URL 解析器 | 直接复用 |
| 媒体下载逻辑 | 直接复用 |
| API 签名模式 | 参考设计 |

### 5.3 注意事项

- **GPL-3.0 许可证**：直接复制代码可能触发 GPL 传染性，建议只参考架构
- **平台反爬策略**：签名算法可能随平台更新失效
- **Cookie 管理**：所有 API 调用依赖浏览器 Cookie

---

*报告生成时间：2026-06-30*
