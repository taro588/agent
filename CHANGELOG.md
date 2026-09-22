# Changelog

本项目采用 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

## [2.1.4] - 2026-09-22

### Fixed

- 修复 Windows GameArt AI Toolkit 安装器插件安装流程中的验证变量作用域问题。
- 重新验证 8 个声明插件的安装与卸载冒烟测试全部通过。
- 发布流程增加受控的 annotated tag 自动创建步骤，确保版本资产从对应 main 提交构建。

### Verified

- Windows GameArt 安装器构建成功。
- Windows UI 启动截图成功生成。
- Compatibility 全平台检查通过。
- 插件安装/卸载 8/8 通过。

## [2.1.3] - 2026-09-22

### Added

- 恢复 GameArt AI 核心、DCC 适配和插件引用，排除无关示例与旧网页资源。
- 新增 Windows 单文件 GameArt AI Toolkit 安装器，并加入启动界面截图与插件安装/卸载冒烟测试。
- 插件安装后不携带 Git 元数据，Windows 卸载增加只读文件处理。

### Changed

- Windows 插件安装改为直接从 GitHub HTTPS Archive 获取，不要求用户安装 Git。
- 修正安装器版本号与更新检查地址，指向当前 `taro588/agent` Release。
- Codex Windows 一键安装器 Release 同步提供 GameArt AI Toolkit 安装器。

### Added

- 新增跨平台 `auto` 网络判断；OpenAI CDN 快速失败时自动切换 OpenAI 官方 GitHub Release，并避免后续重复等待不可用通道。
- Linux 官方桌面应用安装，覆盖 Ubuntu 24.04/26.04、Debian 13、Fedora 43/44 的 x64/Arm64 包。
- 安装结束输出配置修改步骤，并新增个人/项目配置、备份、验证和回滚案例。

### Changed

- Linux 薄入口默认同时请求安装 ChatGPT 桌面应用，可用 `--skip-app` 明确跳过。
- Upstream smoke 增加 Linux 官方文档与四个桌面包的有界探测。

## [2.0.1] - 2026-08-25

### Security

- Release 内容发现疑似秘密时仅输出固定的文件级诊断，不回显匹配值或秘密类别标签。
- 新增诊断脱敏回归测试，并启用 GitHub CodeQL 默认扫描覆盖 Actions 与 Python。

## [2.0.0] - 2026-08-25

### Added

- 新增 OpenAI 官方 standalone CLI 安装路径，支持固定 `--release` / `-Release`。
- 新增 Linux x64 / Arm64 入口及共享 Unix 核心脚本。
- 新增 Windows ChatGPT 桌面应用精确 Store ID 与官方 MSIX 回退。
- 新增可选开发工具安装、纯预检、bootstrap 下载验证和企业摘要固定。
- 新增定期 upstream smoke、确定性 Release 打包、SHA256SUMS 和 SPDX SBOM。
- 新增 GitHub/Sigstore provenance 与 SBOM attestation、draft 回读校验和幂等发布。
- 新增仓库行为测试、Security Policy、贡献指南、迁移指南和故障排查。

### Changed

- CLI 默认安装方式由 npm 改为 OpenAI 官方 standalone。
- 桌面产品名称统一为 ChatGPT desktop app。
- Windows/macOS 双击安装入口默认安装 CLI 并尝试桌面应用；开发工具改为显式选项。
- macOS 双击安装入口通过 `codex app` 使用官方桌面应用流程。
- Release 同时提供 ZIP 与 tar.gz，并验证解包后的执行权限。

### Security

- 下载 bootstrap 后先在随机私有临时目录中检查，再执行；不使用 pipe-to-shell。
- 下载在传输期限制最大体积；Windows MSIX 额外绑定 `OpenAI.Codex` identity、Store publisher 和目标架构。
- Windows 桌面应用在下载前强制 build 19041 门槛，避免在较旧 LTSC 上下载必然无法部署的大型 MSIX。
- Codex 包的版本解析、SHA256、锁、staging、自检与原子切换委托给官方 installer。
- 安装验收绑定本次方法的确切目标和显式请求版本，并拒绝 PATH 用旧版本冒充成功。
- Release 要求 annotated tag 已进入 `main`，发布前后复核远端 tag；资产在 draft 中回读通过后才公开，不覆盖不一致的既有资产。
- 删除全流程 UAC、持久 ExecutionPolicy 修改、全局 npm registry/prefix 修改和 TLS 1.0/1.1。
- 删除 API Key 提示、`auth.json` / `config.toml` 生成和任意远程 Skills ZIP。
- 删除 macOS 递归 quarantine 清除。
- 所有 GitHub Actions 使用完整提交 SHA 固定。

### Removed

- 删除无法完整追溯来源与许可的 `Codex Installer.exe`。
- 删除 `codex-auth.example.json` 和 `downloads.local.example.json`。
- 删除 Windows 8 / 8.1、Node 16 和手工维护的 Git/Node/Python 下载清单。
- 删除旧 `winget install Codex -s msstore` 模糊包名路径。

### Breaking

- 不再自动创建 Codex 配置或认证文件。
- 不再默认安装或更新 Skills。
- 自定义 EXE、MSI、PKG 与任意 URL 下载执行不再支持。
- Windows 最低基线提升到 10.0.17763，Windows 11 为推荐平台。

## [1.2.0] - 2026-07-06

- Windows 幂等安装、更新入口和可选 App 兜底。
- 该版本的发布 ZIP 曾丢失 macOS 文件执行权限；已在 v2 发布链路中加入真实归档回归测试。
