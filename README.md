# 个人学术主页 — 维护手册

This is the source code for my personal website hosted on GitHub Pages.

## 文件结构总览

```
index.html              主页（不需要手动编辑内容）
reader.html             通用 Markdown 文章阅读器
hydro_simulation.html   3D 水动力可视化工具

sections_config.json    各板块"模块导语"的文件路径索引
projects_config.json    各板块项目卡片的元数据（标题、图片、链接等）
skills_config.json      About Me 里技能条的分值与分类

content/
  sections/             各板块的导语正文（Markdown，一个板块一个文件）
    about.md
    hydrodynamics.md
    hydrology.md
    publications.md
    tools-docs.md
    links.md
  intros/               每张项目卡片的摘要段落（Markdown，一张卡片一个文件）
    hdyn-1d-model.md
    hdyn-2d-model.md
    ...

docs/                   完整文章正文（Markdown）
  example-article.md

assets/figs/            图片资源
```

---

## 日常维护工作流

### 1. 修改某个板块的导语文字

打开 `content/sections/<板块名>.md`，直接写 Markdown 保存即可。

| 板块 | 文件 |
|------|------|
| About Me | `content/sections/about.md` |
| Hydrodynamics | `content/sections/hydrodynamics.md` |
| Hydrology | `content/sections/hydrology.md` |
| Publications | `content/sections/publications.md` |
| Tools & Tech Notes | `content/sections/tools-docs.md` |
| Links | `content/sections/links.md` |

---

### 2. 修改某张项目卡片的摘要

打开 `content/intros/<对应文件>.md`，修改后保存。  
哪张卡片对应哪个文件，查看 `projects_config.json` 里的 `"introFile"` 字段。

---

### 3. 新增一张项目卡片

1. 在 `content/intros/` 下新建一个 `.md` 文件，写卡片摘要内容。
2. 打开 `projects_config.json`，在对应板块的数组中追加一条：

```json
{
    "title": "你的项目标题",
    "link": "#",
    "image": "assets/figs/你的图片.png",
    "introFile": "content/intros/你的文件名.md",
    "btnText": "View Details"
}
```

> `link` 填 `"#"` 表示暂无跳转；填具体路径则会显示跳转按钮。  
> 三个板块对应的 JSON 键名：`"hydrodynamics"`、`"hydrology"`、`"toolsDocs"`。

---

### 4. 新增一篇完整文章（正文页面）

1. 复制 `docs/example-article.md`，改名，例如 `docs/my-new-method.md`。
2. 用 Markdown 写正文。支持语法：
   - 标题 `#` `##` `###`
   - 代码块 ` ```python ... ``` `
   - 行内数学 `$f(x)$`，块级数学 `$$\int_0^T ...$$`（KaTeX 渲染）
   - 表格、引用块、图片等标准 Markdown
3. 在 `projects_config.json` 中追加一条，`link` 填：

```
reader.html?file=docs/my-new-method.md
```

完整示例：

```json
{
    "title": "Saint-Venant Equations: Derivation and Discretization",
    "link": "reader.html?file=docs/my-new-method.md",
    "image": "assets/figs/my-cover.png",
    "introFile": "content/intros/my-new-method-intro.md",
    "date": "May 2026",
    "tags": ["Numerics", "C++"],
    "btnText": "Read Full Text →"
}
```

---

### 5. 修改技能条（About Me 板块）

打开 `skills_config.json`，修改 `score`（分值）、`name`（技能名）或增删条目。  
分值是相对值，系统自动归一化（最高分 = 100%）。

---

### 6. 修改外观（导航栏文字、页面标题等）

需直接编辑 `index.html`。内容文字已全部外移到 JSON / MD，`index.html` 不再存储内容正文。

---

## 发布到 GitHub Pages

```bash
git add .
git commit -m "update content"
git push
```

GitHub Actions 自动部署，约 1~2 分钟后生效。  
根目录的 `.nojekyll` 文件确保 GitHub 跳过 Jekyll 直接部署静态文件。
