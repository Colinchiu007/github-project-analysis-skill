# 社交媒体API分类报告（82个项目）

> **分析时间**：2026-06-30
> **目标项目**：Multi-Publish（Electron + Vue 3 多平台内容发布工具）

---

## 一、按平台分类

| 平台 | 项目数 | 已分析 | 高价值 |
|------|--------|--------|--------|
| Twitter/X | 5+ | Agent-Reach ✅ | twint (16K★) |
| Instagram | 5+ | — | instagram-private-api (6.4K★) |
| TikTok/Douyin | 6+ | Douyin_API ✅ | TikTok-Api (6.5K★) |
| LinkedIn | 3 | — | — |
| Facebook | 4+ | — | hello.js (4.6K★) |
| YouTube | 4+ | — | youtube-transcript-api (7.8K★) |
| 小红书 | 4 | XHS-Downloader ✅, social-media-copilot ✅ | xiaohongshu-cli (2.3K★) |
| 微博 | 3 | — | DecryptLogin (2.9K★) |
| Medium | 2 | — | — |
| 通用工具 | 4+ | — | — |

---

## 二、按功能分类

| 功能类别 | 项目数 | 占比 |
|---------|--------|------|
| 数据采集/爬取 | ~40 | 49% |
| API客户端/SDK | ~20 | 24% |
| 认证授权 | ~10 | 12% |
| 媒体播放器 | ~5 | 6% |
| NLP处理 | ~3 | 4% |
| 编辑器 | ~2 | 2% |
| 其他 | ~2 | 3% |

---

## 三、关联度评估

| 关联度 | 项目数 | 占比 | 说明 |
|--------|--------|------|------|
| 高关联 | 15 | 18% | 可直接用于发布功能 |
| 中关联 | 10 | 12% | 可辅助发布流程 |
| 低关联 | 57 | 70% | 与发布功能无关 |

---

## 四、已分析项目 ✅

| 项目 | Stars | 报告位置 |
|------|-------|---------|
| Agent-Reach | 45,060 | `深度分析/内容采集工具/Agent-Reach深度分析报告.md` |
| Douyin_TikTok_Download_API | 18,547 | `深度分析/内容采集工具/抖音小红书下载工具深度分析报告.md` |
| XHS-Downloader | 11,733 | `深度分析/内容采集工具/抖音小红书下载工具深度分析报告.md` |
| social-media-copilot | 1,126 | `深度分析/内容采集工具/social-media-copilot深度分析报告.md` |

---

## 五、推荐深度分析

### 高优先级（3个）

| 项目 | Stars | 推荐理由 |
|------|-------|---------|
| instagram-private-api | 6,448 | Instagram发布SDK，TypeScript技术栈匹配 |
| TikTok-Api | 6,468 | TikTok API封装，会话管理+反检测 |
| instagrapi | 6,397 | Instagram私有API，活跃维护 |

### 中优先级（3个）

| 项目 | Stars | 推荐理由 |
|------|-------|---------|
| xiaohongshu-cli | 2,273 | 小红书CLI，逆向工程API |
| twint | 16,391 | Twitter数据采集 |
| hello.js | 4,627 | OAuth2认证库 |

---

## 六、关键发现

1. **80%项目专注于数据采集**，发布功能项目较少
2. **Python占主导**（~60%），TypeScript/JavaScript次之
3. **Instagram API最成熟**：instagram-private-api提供完整发布SDK
4. **中国平台认证困难**：微博/B站等不支持标准OAuth，需要DecryptLogin
5. **TikTok-Api不支持发布**：仅限数据读取，发布需使用官方API

---

*报告生成时间：2026-06-30*
