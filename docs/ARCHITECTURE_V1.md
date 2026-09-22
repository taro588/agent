# GameArt AI Toolkit — Architecture v1

## 1. Layers

### AI Layer
Agent / Planner / Executor / Reviewer / Vision / MCP / Provider

### Core Layer
Asset / Task / Pipeline / Registry / Validation / Export

### DCC Layer
MayaAdapter / MaxAdapter / Maya Python / MAXScript / DCC APIs

### ThirdParty Layer
Retopo / UV / Bake / LOD / PBR / USD / FBX / Unreal tools

## 2. Core object model

```
Asset
 ├─ geometry
 ├─ materials
 ├─ uv_sets
 ├─ textures
 ├─ lods
 └─ validation

Task
 ├─ input
 ├─ output
 ├─ parameters
 ├─ execute()
 └─ validate()

Pipeline
 ├─ add_task()
 ├─ execute()
 ├─ validate()
 └─ export()
```

## 3. AI loop

用户需求 → Planner → Pipeline → Executor → Validation → Reviewer → 修正/Export

## 4. Adapter rule

Core 不直接调用 Maya/Max API。所有 DCC 特定实现必须经过 Adapter。

## 5. Provider rule

AIProvider 统一云端与本地模型接口，API Key 不进入 Git。

## 6. First Golden Pipeline

Model Check → Retopo → UV → High/Low Match → Bake → PBR → Material → LOD → Validation → FBX/USD → Unreal/Unity
