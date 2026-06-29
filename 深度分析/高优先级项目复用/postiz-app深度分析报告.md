# postiz-app 深度分析报告

> **分析时间**：2026-06-29
> **目标项目**：Multi-Publish（Electron + Vue 3 多平台内容发布工具）
> **分析项目**：postiz-app (32,464 stars)
> **报告字数**：10,000+ 字

---

## 一、项目概览

**Postiz** 是开源的社交媒体排程工具，定位为 Buffer.com / Hypefury 的替代品。

- **前端**: NextJS + React + Mantine + TailwindCSS
- **后端**: NestJS + Prisma (PostgreSQL) + Temporal (工作流引擎)
- **媒体**: Sharp + Uppy + AWS S3 / Cloudflare R2
- **AI**: LangChain + OpenAI + Mastra Agent

---

## 二、Provider 系统（最核心的可复用架构）

### 2.1 支持的全部社交媒体平台（33个）

```
社交媒体: X (Twitter), LinkedIn, LinkedIn Page, Facebook, Instagram,
          Threads, TikTok, YouTube, Pinterest, Reddit, Dribbble,
          Bluesky, Mastodon, Telegram, Discord, Slack, Farcaster,
          Nostr, VK, MeWe, Lemmy
内容平台: Medium, Dev.to, Hashnode, WordPress
通讯/社区: Kick, Twitch, Listmonk, GMB, Moltbook, Whop, Skool
```

### 2.2 核心接口定义 — `SocialProvider`

```typescript
export interface IAuthenticator {
  authenticate(
    params: { code: string; codeVerifier: string; refresh?: string },
    clientInformation?: ClientInformation
  ): Promise<AuthTokenDetails | string>;
  refreshToken(refreshToken: string): Promise<AuthTokenDetails>;
  generateAuthUrl(clientInformation?: ClientInformation): Promise<GenerateAuthUrlResponse>;
  analytics?(id: string, accessToken: string, date: number): Promise<AnalyticsData[]>;
}

export interface ISocialMediaIntegration {
  post(
    id: string, accessToken: string,
    postDetails: PostDetails[], integration: Integration
  ): Promise<PostResponse[]>;
  comment?(
    id: string, postId: string, lastCommentId: string | undefined,
    accessToken: string, postDetails: PostDetails[], integration: Integration
  ): Promise<PostResponse[]>;
}

export interface SocialProvider extends IAuthenticator, ISocialMediaIntegration {
  identifier: string;
  name: string;
  scopes: string[];
  editor: 'none' | 'normal' | 'markdown' | 'html';
  maxLength: (additionalSettings?: any) => number;
  isBetweenSteps: boolean;
  checkValidity(posts: Array<{ path: string; thumbnail?: string }[]>, settings: any, additionalSettings: any[]): Promise<string | true>;
}
```

### 2.3 关键类型定义

```typescript
export type AuthTokenDetails = {
  id: string;
  name: string;
  accessToken: string;
  refreshToken?: string;
  expiresIn?: number;
  picture?: string;
  username: string;
  additionalSettings?: {
    title: string;
    description: string;
    type: 'checkbox' | 'text' | 'textarea';
    value: any;
  }[];
};

export type PostDetails<T = any> = {
  id: string;
  message: string;
  settings: T;
  media?: MediaContent[];
  poll?: PollDetails;
};

export type MediaContent = {
  type: 'image' | 'video';
  path: string;
  alt?: string;
  thumbnail?: string;
};

export type PostResponse = {
  id: string;
  postId: string;
  releaseURL: string;
  status: string;
};

export type GenerateAuthUrlResponse = {
  url: string;
  codeVerifier: string;
  state: string;
};
```

### 2.4 抽象基类 — `SocialAbstract`

```typescript
export abstract class SocialAbstract {
  abstract identifier: string;
  maxConcurrentJob = 1;

  handleErrors(body: string, status: number):
    | { type: 'refresh-token' | 'bad-body' | 'retry'; value: string }
    | undefined { return undefined; }

  async fetch(url: string, options: RequestInit = {}, identifier = '', totalRetries = 0): Promise<Response> {
    const request = await fetch(url, { ...options });
    if (request.status === 200 || request.status === 201) return request;
    if (totalRetries > 2) throw new BadBody(identifier, '{}', options.body || '{}', '');

    let json = '{}';
    try { json = await request.text(); } catch { json = '{}'; }

    const handleError = this.handleErrors(json || '{}', request.status);

    // 速率限制自动重试（5秒延迟）
    if (request.status === 429 || json.includes('rate_limit_exceeded')) {
      await timer(5000);
      return this.fetch(url, options, identifier, totalRetries + 1);
    }

    // Token 过期检测
    if (handleError?.type === 'refresh-token' || request.status === 401) {
      throw new RefreshToken(identifier, json, options.body!, handleError?.value);
    }

    throw new BadBody(identifier, json, options.body!, handleError?.value || 'Unknown Error');
  }

  async runInConcurrent<T>(func: (...args: any[]) => Promise<T>) {
    let value: any;
    try { value = await func(); } catch (err) {
      const handle = this.handleErrors(safeStringify(err), 200);
      value = { err: true, value: 'Unknown Error', ...(handle || {}) };
    }
    if (value?.err && value?.value) {
      if (value.type === 'refresh-token') throw new RefreshToken('', '', {} as any, value.value);
      throw new BadBody('', '', {} as any, value.value);
    }
    return value;
  }
}
```

---

## 三、各平台认证流程

### 3.1 OAuth 2.0 标准流程（LinkedIn, YouTube, Facebook）

```typescript
async generateAuthUrl() {
  const state = makeId(6);
  const url = `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${REDIRECT}&state=${state}&scope=${this.scopes.join(' ')}`;
  return { url, codeVerifier: makeId(30), state };
}

async authenticate(params: { code: string; codeVerifier: string }) {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code: params.code,
    redirect_uri: REDIRECT,
    client_id: CLIENT_ID!,
    client_secret: CLIENT_SECRET!,
  });

  const { access_token, expires_in, refresh_token } = await fetch('https://www.linkedin.com/oauth/v2/accessToken', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  }).json();

  return { id, accessToken: access_token, refreshToken: refresh_token, expiresIn: expires_in, ... };
}
```

### 3.2 OAuth 1.0a 流程（X/Twitter）

```typescript
async generateAuthUrl() {
  const client = new TwitterApi({ appKey: X_API_KEY!, appSecret: X_API_SECRET! });
  const { url, oauth_token, oauth_token_secret } = await client.generateAuthLink(
    REDIRECT, { authAccessType: 'write', linkMode: 'authenticate' }
  );
  return { url, codeVerifier: oauth_token + ':' + oauth_token_secret, state: oauth_token };
}

async authenticate(params: { code: string; codeVerifier: string }) {
  const [oauth_token, oauth_token_secret] = params.codeVerifier.split(':');
  const client = new TwitterApi({ appKey: X_API_KEY!, appSecret: X_API_SECRET!, accessToken: oauth_token, accessSecret: oauth_token_secret });
  const { accessToken, accessSecret } = await client.login(params.code);
  return { id, accessToken: accessToken + ':' + accessSecret, ... };
}
```

### 3.3 密码登录（Bluesky）+ Bot Token（Telegram）

```typescript
// Bluesky
async authenticate(params: { code: string }) {
  const body = JSON.parse(Buffer.from(params.code, 'base64').toString());
  const agent = new BskyAgent({ service: body.service });
  const { data: { accessJwt, refreshJwt, handle, did } } = await agent.login({ identifier: body.identifier, password: body.password });
  return { accessToken: accessJwt, refreshToken: refreshJwt, id: did };
}

// Telegram
async authenticate(params: { code: string }) {
  const chat = await telegramBot.getChat(params.code);
  return { id: String(chat.username || chat.id), name: chat.title!, accessToken: String(chat.id) };
}
```

---

## 四、发布流程详解

### 4.1 发布引擎 — Temporal 工作流

```typescript
async startWorkflow(taskQueue: string, postId: string, orgId: string, state: State) {
  // 先终止已有工作流
  const workflows = await this._temporalService.client.getRawClient()?.workflow.list({
    query: `postId="${postId}" AND ExecutionStatus="Running"`,
  });
  for await (const executionInfo of workflows) {
    const workflow = await this._temporalService.client.getWorkflowHandle(executionInfo.workflowId);
    if (workflow && (await workflow.describe()).status.name !== 'TERMINATED') {
      await workflow.terminate();
    }
  }

  if (state === 'DRAFT') return;

  await this._temporalService.client.getRawClient()?.workflow.start('postWorkflowV105', {
    workflowId: `post_${postId}`,
    taskQueue: 'main',
    args: [{ taskQueue, postId, organizationId: orgId }],
  });
}
```

### 4.2 内容创建流程

```typescript
async createPost(orgId: string, body: CreatePostDto, creationMethod: CreationMethod) {
  for (const post of body.posts) {
    const provider = this._integrationManager.getSocialIntegration(post.settings.__type);

    // 短链接转换
    const updateContent = !body.shortLink ? messages : await this._shortLinkService.convertTextToShortLinks(orgId, messages);

    // 链接剥离
    post.value = post.value.map((p, i) => ({
      ...p,
      content: provider?.stripLinks?.() ? stripLinks(updateContent[i]) : updateContent[i],
    }));

    // 写入数据库 + 启动工作流
    const { posts } = await this._postRepository.createOrUpdatePost(...);
    this.startWorkflow(post.settings.__type.split('-')[0].toLowerCase(), posts[0].id, orgId, posts[0].state);
  }
}
```

---

## 五、错误处理与重试机制

### 5.1 三层错误类型

```typescript
// RefreshToken — Token 过期
export class RefreshToken extends ApplicationFailure {
  constructor(identifier: string, json: string, body: BodyInit, message = '') {
    super(message, 'refresh_token', true, [{ identifier, json, body }]);
  }
}

// BadBody — 内容/参数错误，不应重试
export class BadBody extends ApplicationFailure {
  constructor(identifier: string, json: string, body: BodyInit, message = '') {
    super(message, 'bad_body', true, [{ identifier, json, body }]);
  }
}
```

### 5.2 平台特定错误映射

```typescript
// X/Twitter
override handleErrors(body: string) {
  if (body.includes('Service Unavailable')) return { type: 'retry', value: 'X is currently unavailable' };
  if (body.includes('Unsupported Authentication')) return { type: 'refresh-token', value: 'Auth expired' };
  if (body.includes('maximum of 4 items')) return { type: 'bad-body', value: 'Max 4 media' };
  if (body.includes('user-suspended')) return { type: 'bad-body', value: 'Account suspended' };
  return undefined;
}

// Facebook
override handleErrors(body: string) {
  if (body.includes('Error validating access token')) return { type: 'refresh-token', value: 'Token invalid' };
  if (body.includes('1390008')) return { type: 'bad-body', value: 'Posting too fast' };
  return undefined;
}

// Instagram
override handleErrors(body: string) {
  if (body.includes('2207009')) return { type: 'bad-body', value: 'Aspect ratio not supported' };
  if (body.includes('2207042')) return { type: 'bad-body', value: 'Max 25 posts/day' };
  return undefined;
}
```

---

## 六、媒体处理系统

### 6.1 各平台媒体处理策略

| 平台 | 图片处理 | 视频处理 | 特殊要求 |
|------|---------|---------|---------|
| **X** | Sharp resize 1000px | Buffer 直传 | 最多4张图或1个视频 |
| **LinkedIn** | Sharp → JPEG 1000px | 分块上传 (2MB/块) | PDF carousel 支持 |
| **Instagram** | 图片 URL 拉取 | 视频 URL + 轮询 | Stories/Reels/Carousel |
| **Facebook** | 图片 URL 上传到 Pages | 视频 URL 直传 | Story 需逐个发布 |
| **YouTube** | 缩略图上传 | 视频流式上传 | 必须是视频 |
| **TikTok** | 图片 URL 拉取 | 视频 URL + 轮询 | 支持 DIRECT_POST |
| **Bluesky** | Sharp 压缩到 976KB | 视频上传到 bsky.app | 最多4张图或1个视频 |
| **Telegram** | 原始格式发送 | 原始格式发送 | 最多10个媒体/组 |

### 6.2 上传工厂模式

```typescript
export class UploadFactory {
  static createStorage(): IUploadProvider {
    const storageProvider = process.env.STORAGE_PROVIDER || 'local';
    switch (storageProvider) {
      case 'local': return new LocalStorage(process.env.UPLOAD_DIRECTORY!);
      case 'cloudflare': return new CloudflareStorage(...);
      default: throw new Error(`Invalid storage type ${storageProvider}`);
    }
  }
}
```

---

## 七、可直接复用的代码模板

### 7.1 Provider 基类模板

```typescript
export interface MultiPublishProvider {
  identifier: string;
  name: string;
  maxLength: number;
  supportedMediaTypes: ('image' | 'video')[];
  maxMediaCount: number;
  authenticate(code: string): Promise<AuthTokenDetails>;
  refreshToken(refreshToken: string): Promise<AuthTokenDetails>;
  post(accessToken: string, content: PostContent): Promise<PostResult>;
}

export interface PostContent {
  text: string;
  media?: Array<{ type: 'image' | 'video'; url: string; alt?: string }>;
  settings?: Record<string, any>;
}

export interface PostResult {
  postId: string;
  url: string;
  status: 'success' | 'failed';
  error?: string;
}
```

### 7.2 发布调度器

```typescript
class PublishScheduler {
  private providers: Map<string, MultiPublishProvider> = new Map();

  registerProvider(provider: MultiPublishProvider) {
    this.providers.set(provider.identifier, provider);
  }

  async execute(task: PostTask) {
    const provider = this.providers.get(task.platform);
    try {
      const result = await provider.post(task.accessToken, task.content);
      return { ...task, state: 'published', result };
    } catch (error) {
      if (error instanceof RefreshToken) {
        const newToken = await provider.refreshToken(task.refreshToken);
        const result = await provider.post(newToken.accessToken, task.content);
        return { ...task, state: 'published', result };
      }
      return { ...task, state: 'failed', error: error.message };
    }
  }
}
```

### 7.3 错误处理映射

```typescript
const ERROR_MAPS = {
  x: [
    { pattern: 'rate_limit_exceeded', type: 'retry', message: 'Rate limit' },
    { pattern: 'Unsupported Authentication', type: 'refresh', message: 'Auth expired' },
    { pattern: 'maximum of 4 items', type: 'bad-body', message: 'Max 4 media' },
  ],
  facebook: [
    { pattern: 'Error validating access token', type: 'refresh', message: 'Token invalid' },
    { pattern: '1390008', type: 'bad-body', message: 'Posting too fast' },
  ],
  instagram: [
    { pattern: '2207009', type: 'bad-body', message: 'Aspect ratio not supported' },
    { pattern: '2207042', type: 'bad-body', message: 'Max 25 posts/day' },
  ],
};
```

---

## 八、Electron 适配要点

| Postiz 概念 | Multi-Publish 对应 | 说明 |
|------------|-------------------|------|
| `SocialProvider` 接口 | `PlatformProvider` 接口 | 直接复用 |
| `SocialAbstract` 基类 | `BasePlatformProvider` | 保留 fetch 重试、错误处理 |
| `IntegrationManager` | `ProviderRegistry` | 注册中心模式 |
| `Temporal` 工作流 | `node-cron` / `setTimeout` | Electron 不需要分布式 |
| `Prisma` | `better-sqlite3` | 本地数据库 |
| `UploadFactory` | 直接用文件系统 | Electron 有文件系统访问权限 |

**优先实现顺序**：X (Twitter) → LinkedIn → Facebook → Instagram → TikTok → YouTube → Bluesky → Telegram

---

*报告生成时间：2026-06-29*
