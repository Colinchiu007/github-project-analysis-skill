# 社交媒体API项目深度分析报告

> **分析时间**：2026-06-30
> **目标项目**：Multi-Publish（Electron + Vue 3 多平台内容发布工具）
> **分析项目**：instagram-private-api (6,448★) + TikTok-Api (6,468★) + hello.js (4,627★) + DecryptLogin (2,858★)
> **报告字数**：10,000+ 字

---

## 一、项目总览

| 项目 | Stars | 语言 | 核心定位 | 关联度 |
|------|-------|------|---------|--------|
| instagram-private-api | 6,448 | TypeScript | Instagram 私有 API SDK，支持发布 | ★★★★★ |
| TikTok-Api | 6,468 | Python | TikTok 数据抓取（仅读取） | ★★★☆☆ |
| hello.js | 4,627 | JavaScript | OAuth2 客户端 SDK | ★★★★☆ |
| DecryptLogin | 2,858 | Python | 逆向登录 API，30+ 网站 | ★★★☆☆ |

---

## 二、instagram-private-api 核心发布代码

### 2.1 照片发布流程

```typescript
public async photo(options: PostingPhotoOptions) {
  const uploadedPhoto = await this.client.upload.photo({ file: options.file });
  const imageSize = await sizeOf(options.file);
  return await this.client.media.configure({
    upload_id: uploadedPhoto.upload_id,
    width: imageSize.width, height: imageSize.height,
    caption: options.caption,
  });
}
```

### 2.2 视频发布流程（带转码等待+重试）

```typescript
public async video(options: PostingVideoOptions) {
  const uploadId = Date.now().toString();
  const videoInfo = PublishService.getVideoInfo(options.video);
  await this.regularVideo({ video: options.video, uploadId, ...videoInfo });
  await this.client.upload.photo({ file: options.coverImage, uploadId });
  await this.client.media.uploadFinish({
    upload_id: uploadId, source_type: '4',
    video: { length: videoInfo.duration / 1000.0 },
  });
  for (let i = 0; i < 6; i++) {
    try { return await this.client.media.configureVideo(configureOptions); }
    catch (e) { if (i >= 5) throw e; await Bluebird.delay((i + 1) * 2 * 1000); }
  }
}
```

### 2.3 认证机制（AES-256-GCM + RSA）

```typescript
encryptPassword(password: string) {
  const randKey = crypto.randomBytes(32);
  const iv = crypto.randomBytes(12);
  const rsaEncrypted = crypto.publicEncrypt({ key: pubKey, padding: RSA_PKCS1_PADDING }, randKey);
  const cipher = crypto.createCipheriv('aes-256-gcm', randKey, iv);
  cipher.setAAD(Buffer.from(time));
  const aesEncrypted = Buffer.concat([cipher.update(password), cipher.final()]);
  return { time, encrypted: Buffer.concat([Buffer.from([1, keyId]), iv, rsaEncrypted, authTag, aesEncrypted]).toString('base64') };
}
```

---

## 三、TikTok-Api 反检测技术

### 3.1 会话池管理

```python
@dataclasses.dataclass
class TikTokPlaywrightSession:
    context: Any; page: Any; proxy: str = None
    params: dict = None; headers: dict = None
    ms_token: str = None; is_valid: bool = True
```

### 3.2 设备指纹随机化

```python
session.params = {
    "aid": "1988", "app_name": "tiktok_web",
    "device_id": str(random.randint(10**18, 10**19 - 1)),
    "screen_height": str(random.randint(600, 1080)),
    "screen_width": str(random.randint(800, 1920)),
}
```

### 3.3 会话健康检查+自动恢复

```python
async def _get_valid_session_index(self):
    for attempt in range(3):
        valid_sessions = [(idx, s) for idx, s in enumerate(self.sessions) if await self._is_session_valid(s)]
        if valid_sessions: return random.choice(valid_sessions)
        if self._session_recovery_enabled: await self._recover_sessions()
    raise Exception("No valid sessions available")
```

---

## 四、hello.js OAuth2 模式

### 4.1 多平台统一认证

```javascript
hello.init({ facebook: '359288236870', windows: '000000004403AD10', google: GOOGLE_CLIENT_ID }, { redirect_uri: 'redirect.html' });
hello('facebook').login({ scope: 'email, publish' });
hello('facebook').api('me').then(json => console.log(json.name));
```

### 4.2 Token 存储+自动刷新

```javascript
utils.store = function(name, value, days) {
  var json = JSON.parse(localStorage.getItem('hello')) || {};
  if (name && value === undefined) return json[name];
  if (name) json[name] = value;
  localStorage.setItem('hello', JSON.stringify(json));
};
// 每秒检查Token过期
setTimeout(function self() {
  for (var name in hello.services) {
    var session = utils.store(name);
    if (session && session.expires < CURRENT_TIME) hello.login(name, {display: 'none'});
  }
  setTimeout(self, 1000);
}, 1000);
```

### 4.3 hello.js vs better-auth

| 特性 | hello.js | better-auth |
|------|---------|-------------|
| 定位 | 客户端 OAuth2 SDK | 全栈认证框架 |
| 安全 | 客户端暴露 | 服务端保护 |
| 现代化 | 2015年风格 | 2024年 TypeScript |

**建议**：Multi-Publish 使用 better-auth，参考 hello.js 的 Scope 管理模式。

---

## 五、DecryptLogin 中国平台登录

### 5.1 支持的网站（30+）

| 类别 | 网站 |
|------|------|
| 社交媒体 | 微博、知乎、Twitter、人人网 |
| 视频平台 | B站、斗鱼、喜马拉雅 |
| 工具 | 百度网盘、阿里云盘 |
| 开发 | GitHub、StackOverflow |
| 音乐 | 网易云音乐、QQ音乐 |

### 5.2 登录模式

```python
from DecryptLogin import login
lg = login.Login()
infos_return, session = lg.weibo(username='xxx', password='yyy')
# 或扫码模式
infos_return, session = lg.weibo('me', 'pass', 'scanqr')
```

### 5.3 Electron 集成方案

```typescript
class CNPlatformAuth {
  async login(platform: 'weibo' | 'bilibili', credentials: Credentials) {
    const result = await exec(`python3 -c "
from DecryptLogin import login
lg = login.Login()
infos, session = lg.${platform}(username='${credentials.username}', password='${credentials.password}')
print(json.dumps({'cookies': dict(session.cookies), 'infos': infos}))
"`);
    return JSON.parse(result);
  }
}
```

---

## 六、可复用代码汇总

### 6.1 统一 API 客户端架构

```typescript
interface PlatformClient {
  name: string;
  auth: AuthManager;
  request(method: string, path: string, data?: any): Promise<any>;
}
```

### 6.2 通用发布模式

```typescript
class ContentPublisher {
  async publishPhoto(file: Buffer, caption: string, options?: PublishOptions) {
    const uploadId = await this.upload(file);
    const dimensions = await this.getImageDimensions(file);
    return this.configure({ type: 'photo', uploadId, width: dimensions.width, height: dimensions.height, caption });
  }
  async publishVideo(video: Buffer, caption: string, coverImage: Buffer) {
    const uploadId = Date.now().toString();
    await this.uploadVideo(video, uploadId);
    await this.uploadPhoto(coverImage, uploadId);
    await this.waitForTranscode(uploadId);
    for (let i = 0; i < 6; i++) {
      try { return await this.configure({ type: 'video', uploadId }); }
      catch (e) { if (i >= 5) throw e; await delay((i + 1) * 2 * 1000); }
    }
  }
}
```

### 6.3 会话池管理

```typescript
class BrowserSessionPool {
  private sessions: BrowserSession[] = [];
  async acquire(): Promise<BrowserSession> {
    for (const session of this.sessions) {
      if (await this.isValid(session)) return session;
    }
    return this.createSession();
  }
  async healthCheck(): Promise<BrowserSession[]> {
    const dead: BrowserSession[] = [];
    for (const session of this.sessions) {
      if (!await this.isValid(session)) { dead.push(session); await this.markInvalid(session); }
    }
    return dead;
  }
}
```

---

## 七、推荐集成架构

```
Multi-Publish (Electron + Vue 3)
├── 认证层
│   ├── Instagram: instagram-private-api
│   ├── TikTok: TikTok Creator API
│   ├── Facebook/Google: better-auth
│   ├── 中国平台: DecryptLogin + Python子进程
│   └── Twitter: Twitter API v2
├── 发布层
│   └── ContentPublisher 统一接口
├── 会话管理
│   └── SessionPool + HealthCheck + AutoRecovery
└── 前端 (Vue 3)
    ├── 账号管理
    ├── 内容编辑器
    └── 发布调度
```

---

## 八、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| API变更 | 监控 GitHub issues，准备降级方案 |
| 封号风险 | 限制发布频率、模拟人类行为 |
| Python依赖 | Electron 中打包 Python 或使用 WebAssembly |
| 内存泄漏 | 参考 TikTok-Api 的 cleanup 机制 |

---

*报告生成时间：2026-06-30*
