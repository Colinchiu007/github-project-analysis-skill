# GitHub 项目分析 Skill

> **中文名称**：GitHub 项目分析
> **用途**：针对某个需求和技术领域，在 GitHub 搜索相关项目进行分析，给出可行性复用报告

---

## 功能说明

本 skill 用于：
1. 根据用户需求生成搜索关键词
2. 在 GitHub 上搜索相关项目
3. 按条件筛选项目（Star 数、更新时间）
4. 深入分析每个项目
5. 生成可行性复用报告

---

## 使用方法

### 方式 1：从需求生成关键词

```
在 Claude Code 中输入：
"执行 GitHub 项目分析 skill，分析多平台内容发布工具的需求"
```

### 方式 2：直接提供关键词

```
在 Claude Code 中输入：
"执行 GitHub 项目分析 skill，搜索关键词：multi-platform publish, social media scheduler"
```

### 方式 3：从文档读取关键词

```
在 Claude Code 中输入：
"执行 GitHub 项目分析 skill，使用 D:\Data\projects\GitHub搜索关键词清单.md 中的关键词"
```

---

## 筛选条件

| 条件 | 默认值 | 可自定义 |
|------|--------|----------|
| Star 数 | > 100 | ✅ |
| 最近更新 | < 6 个月 | ✅ |

---

## 输出成果

1. **关键词清单**：`GitHub-关键词清单-{日期}.md`
2. **项目列表**：`GitHub-项目列表-{日期}.md`
3. **分析报告**：`GitHub-项目分析报告-{日期}.md`

---

## 安装方法

### 方法 1：手动安装

```bash
# 1. 创建 skill 目录
mkdir -p ~/.claude/skills/github-project-analysis

# 2. 复制 SKILL.md 到该目录
cp SKILL.md ~/.claude/skills/github-project-analysis/

# 3. 重启 Claude Code
```

### 方法 2：使用 skill-creator

```bash
skill-creator create github-project-analysis
```

---

## 示例

### 输入

```
我想做一个多平台内容发布工具，支持小红书、抖音、视频号、B站
```

### 输出

1. **关键词清单**：49 个关键词
2. **项目列表**：56 个符合条件的项目
3. **分析报告**：每个项目的详细分析 + 综合总结

---

## License

MIT
