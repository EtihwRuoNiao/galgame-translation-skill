# galgame-translation-skill

批量化日译中翻译技能，专门处理 galgame（视觉小说）文本。

## 功能特性

- 支持双行格式（★◎...◎★// 为源行、★◎...◎★ 为目标行）
- 支持单行格式（只有源行）
- 保留原文件所有格式提示字符、换行符类型、文件编码
- 使用范例文件学习语言风格
- 使用自定义词典处理专有名词（PERSON/PLACE/TITLE/TERM）
- 自动检测文件编码和格式
- 支持用户指定路径和通配符
- 输出到输入路径同级的新建文件夹
- 生成翻译总结报告

## 安装

### 通过 git clone 安装

```bash
# OpenCode
git clone <repo-url> ~/.config/opencode/skills/galgame-translation-skill

# Claude Code
git clone <repo-url> ~/.claude/skills/galgame-translation-skill

# GitHub Copilot
git clone <repo-url> .github/skills/galgame-translation-skill

# Cursor
git clone <repo-url> .cursor/rules/galgame-translation-skill

# Windsurf
git clone <repo-url> .windsurf/rules/galgame-translation-skill

# Cline
git clone <repo-url> .clinerules/galgame-translation-skill

# Gemini CLI
git clone <repo-url> ~/.gemini/skills/galgame-translation-skill

# Kiro
git clone <repo-url> .kiro/skills/galgame-translation-skill

# Trae
git clone <repo-url> .trae/rules/galgame-translation-skill

# Roo Code
git clone <repo-url> .roo/rules/galgame-translation-skill

# Goose
git clone <repo-url> ~/.config/goose/skills/galgame-translation-skill

# Universal（Codex CLI、Antigravity 等）
git clone <repo-url> ~/.agents/skills/galgame-translation-skill
```

### 使用 install.sh 安装

```bash
# 快速安装（自动检测平台）
git clone <repo-url>
cd galgame-translation-skill
./install.sh

# 指定平台
./install.sh --platform opencode

# 安装到所有检测到的平台
./install.sh --all

# 预览安装（不实际安装）
./install.sh --dry-run
```

## 使用方法

安装后，启动新的会话并输入：

### 指定路径翻译

```
/galgame-translation-skill /path/to/input/              # 翻译整个目录
/galgame-translation-skill /path/to/file.txt            # 翻译单个文件
/galgame-translation-skill *.txt                          # 翻译匹配的文件
```

### 输出位置

翻译结果会输出到输入路径同级的新建文件夹：
- **单文件**：`/path/to/file.txt` → `/path/to/translated/file.txt`
- **目录**：`/path/to/folder/` → `/path/to/folder-translated/`（保持目录结构）
- **通配符**：每个文件按单文件规则处理

## 目录结构

```
galgame-translation-skill/
├── SKILL.md              # 技能定义文件（核心）
├── README.md             # 本文件
├── install.sh            # 跨平台安装脚本
├── assets/
│   ├── dictionary/       # 自定义词典（CSV格式）
│   │   └── sample-dictionary.csv
│   └── examples/        # 范例翻译文件（用于学习风格）
│       ├── sample-dual.txt      # 双行格式示例
│       └── sample-single.txt    # 单行格式示例
├── scripts/              # 辅助脚本
│   ├── path_resolver.py        # 路径解析、文件收集、输出路径生成
│   ├── encoding_detector.py    # 文件编码、换行符、格式检测
│   ├── dict_loader.py          # 词典加载、查询、统计
│   ├── normalize_output.py     # \n 展开修复
│   ├── style_analyzer.py       # 风格缓存管理
│   └── report_generator.py     # 总结报告生成
└── references/          # 详细文档（按需加载）
    ├── format-guide.md
    ├── translation-rules.md
    └── character-handling.md
```

## 配置

1. **词典文件**：放置在 `assets/dictionary/` 目录下，CSV 格式，使用 `==== 类型 ====` 分区
   - 强制区块：PERSON, PLACE, TITLE（必须使用指定译名）
   - 参考区块：TERM（优先参考，可调整）

2. **范例文件**：放置在 `assets/examples/` 目录下，已翻译的完整文件

3. **待翻译文件**：可通过以下方式指定：
   - 直接指定路径：`/path/to/file.txt` 或 `/path/to/folder/`
   - 使用通配符：`*.txt` 或 `/path/to/*.txt`
   - 默认路径：若未指定，使用技能目录下的 `input/` 文件夹

## 注意事项

- 所有翻译结果输出到输入路径同级的新建文件夹，永不修改原始文件
- 输出文件夹自动创建，已存在时直接写入（覆盖同名文件）
- 支持绝对路径、相对路径、通配符模式
- 译文中的中文文本及标点使用全角字符
- 格式提示字符（★◎、◎★、//、#0x、@...、`\n` 等）按原文半角保留
- 输出文件使用与原始文件完全相同的编码和换行符

## 脚本使用

### 路径解析

```bash
cd ~/.config/opencode/skills/galgame-translation-skill/scripts
python path_resolver.py /path/to/input/
python path_resolver.py /path/to/file.txt
python path_resolver.py "*.txt"
```

### 文件属性检测

```bash
python encoding_detector.py /path/to/file.txt
```

### 词典操作

```bash
python dict_loader.py ../assets/dictionary/
python dict_loader.py ../assets/dictionary/ --lookup "こんにちは"
python dict_loader.py ../assets/dictionary/ --stats
```

## 致谢

本技能处理的文本格式来源于 [cokkeijigen/MesTextTool](https://github.com/cokkeijigen/MesTextTool) 项目提取的 TXT 文件格式。

## 许可证

MIT License
