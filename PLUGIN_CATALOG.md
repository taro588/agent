# GameArt Toolkit — Plugin Catalog

> 第三方项目保持为 Git Submodule；自研代码位于 `src/`。许可证和上游版本发布前逐项复核。

## Maya
- Autodesk/maya-usd — OpenUSD
- TrevisanGMW/gt-tools — 综合工具
- JakobJK/modelChecker — 模型检查
- monster-puppet/RoadKill — UV
- m3trik/mayatk — 综合工具
- Froyok/froRetopo — Retopo
- Amatsukast/Maya-SBTools — 建模/拓扑
- adevra/RizomUV-2024-Maya-Bridge — RizomUV / UV
- arunprksm/Unreal-Maya-Pipeline — Unreal Pipeline
- NguyenNP-24/LOD-Generator-Tool-Maya — LOD
- SaiiPrashanth/Automated_LOD_Tool — LOD
- leetdvn/LeeAutoExportFBX — FBX
- beatreichenbach/texture-importer — 纹理 → 材质
- pramberg/MayaToPainter — Maya → Substance Painter
- Strangenoise/SubstancePainterToMaya — Painter → Maya

## 3ds Max
- Autodesk/3dsmax-usd — OpenUSD
- blurstudio/Py3dsMax — Python / MAXScript
- NevilArt/BsMax — 建模/工作流
- cl0nazepamm/flowstate — 建模/Modifier/Shader
- imanshirani/3DsMax-bridge-for-AutoRemesher — Retopo
- imanshirani/OPEN_KITBASH — Kitbash
- cl0nazepamm/3dsmax-mcp — MCP / AI 控制
- dexise/3dsMax-Asset-Tools-for-Unreal-Engine — Unreal Pipeline
- Joyxt/3dsmax-fbx-conform_and_batch-render — FBX / Batch
- svenfraeys/totex — Texture Bake
- Khanzino3d/maxscript-rename-lowhigh-proximity — High/Low 匹配

## Shared / PBR / AI
- lovisdotio/fal-texture-pbr-generator — AI PBR
- Whappens/Procedural-PBR — 程序化 PBR
- Gil-1/SubstanceDesignerTools — Substance Designer 工具

## 统一 Pipeline
模型检查 → Retopo → UV → High/Low Match → Bake → PBR → Material → LOD → Validation → FBX/USD → Unreal/Unity

## 架构方向
AI Agent → Pipeline Engine → Maya/Max Adapter → ThirdParty / PBR / Validation → Engine Export

## 许可证
以各上游仓库当前 LICENSE 为准。商业发布前重点复核 GPL、SDK linking exception、商业软件授权、第三方服务条款以及 AI API 使用条款。
