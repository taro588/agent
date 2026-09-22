# Plugin Health Check — 2026-09

## Scope

This audit covers the 8 Git submodules currently registered in `.gitmodules`.
It combines repository/static inspection with public upstream documentation checks.

Important: this is **not** a real Maya/3ds Max runtime test. The current execution environment does not contain the target DCC applications, so no claim is made that a plugin has been loaded and executed inside Maya or 3ds Max.

## Status policy

- **GREEN** — suitable for optional integration; no blocking issue found in static review.
- **YELLOW** — usable only behind an adapter/sandbox or with explicit dependency checks.
- **RED** — do not make it a core dependency; known compatibility/maintenance risk.
- **REVIEW** — purpose or packaging does not match the Toolkit's current DCC architecture.

## Results

| Plugin | Host | Static result | Risk | Decision |
|---|---|---:|---:|---|
| texture-importer | Maya / 3ds Max | PASS | Medium | Keep optional; wrap with adapter |
| totex | 3ds Max | PASS* | High | Keep isolated; do not make core |
| MayaToPainter | Maya + Substance Painter | PASS* | High | Keep optional; compatibility gate required |
| SubstancePainterToMaya | Maya | PASS* | High | Keep optional; renderer/version checks required |
| rename-lowhigh-proximity | 3ds Max | PASS* | Medium | Keep optional; execute through Max adapter |
| fal-texture-pbr-generator | Web/AI service | PASS* | Medium/High | Treat as AI provider/service, not DCC plugin |
| Procedural-PBR | Godot/Python | PASS* | Medium | Review/reclassify; not a Maya/Max plugin |
| SubstanceDesignerTools | Substance Designer | PASS* | Medium | Keep as external Substance capability |

* PASS means repository/package purpose was inspected; it does not mean runtime execution was verified.

## Findings

### 1. texture-importer — GREEN/YELLOW

Upstream documents Maya and 3ds Max support, renderer-specific material networks, Substance Painter/Mari/Mudbox naming patterns, and a plugin architecture. It has a visible test directory and MIT license.

Risk: it is an external DCC tool with renderer-specific behavior. It must not directly own Toolkit state or modify the Toolkit's core environment.

Integration rule:
- load only on demand;
- detect DCC and renderer first;
- run behind an adapter;
- capture exceptions;
- never overwrite Toolkit config;
- if loading fails, disable only this capability.

### 2. totex — RED for core / YELLOW for optional

ToTex is a 3ds Max render-to-texture MaxScript. Public documentation identifies 3ds Max 2009–2011 as the version requirement.

This is a strong compatibility risk for a modern Toolkit. It must not be treated as a guaranteed modern baking backend.

Integration rule:
- never auto-install into Max;
- never make Pipeline depend on it;
- expose it as an optional legacy baking capability only after version detection;
- disable automatically when the detected Max version is unsupported.

### 3. MayaToPainter — RED for automatic installation / YELLOW optional

The upstream README explicitly says the plugin is old and the author cannot verify it against recent Maya/Substance Painter versions. It also documents a known Maya-exit issue when Painter was started by the plugin.

This is exactly the type of component that must not be a hard dependency.

Integration rule:
- optional installation;
- version compatibility gate;
- process-launch isolation;
- cleanup isolation;
- explicit user confirmation before enabling;
- never load it automatically if compatibility is unknown.

### 4. SubstancePainterToMaya — YELLOW

The tool automates Substance Painter texture connections in Maya and supports multiple renderers. Its upstream README describes version 0.1 and documents a multi-renderer workflow.

Risk comes from old-style Maya scripting and renderer-specific shader assumptions.

Integration rule:
- renderer detection before execution;
- validate expected shader nodes;
- never assume Arnold/VRay/Redshift/Renderman availability;
- fail only the material-import task if unsupported.

### 5. rename-lowhigh-proximity — GREEN/YELLOW

The repository is specifically aimed at 3ds Max low/high naming preparation for baking and is actively associated with game-art/baking workflows.

Integration rule:
- execute through a Max adapter;
- operate on explicit selection or explicit asset scope;
- provide dry-run validation before renaming;
- provide rollback/rename manifest;
- never rename files outside the selected asset scope.

### 6. fal-texture-pbr-generator — REVIEW

This is a Next.js web application using fal.ai/PATINA to generate BaseColor, Normal, Roughness, Metallic and Height maps. It requires Node.js 18+ and a fal.ai API key.

It is not a Maya/3ds Max plugin.

Decision:
- move conceptually into the AI Provider / PBR service layer;
- do not install it into DCC plugin folders;
- API failures must return a task failure, not crash Toolkit;
- API keys must stay outside Git.

### 7. Procedural-PBR — REVIEW

This repository is a lightweight Python procedural PBR generator aimed at Godot Engine. It generates tileable PBR maps and describes Godot material-channel conventions.

It does not belong in the Maya/3ds Max plugin layer.

Decision:
- keep as an optional shared PBR capability only if a future Godot target is required;
- otherwise remove from the active DCC plugin set;
- do not expose it as a Maya/Max native plugin.

### 8. SubstanceDesignerTools — GREEN/YELLOW

This repository contains Substance Designer .SBS tools, including a triplanar PBR texturer producing Base Color, Normal, Roughness and Metallic outputs. It is MIT licensed.

It is better modeled as an external Substance Designer capability than as a Maya/Max plugin.

Integration rule:
- detect Substance Designer availability/version;
- exchange files through a controlled workspace;
- validate generated outputs;
- do not modify user Substance projects unless explicitly requested.

## Architecture decision

The 8 current submodules should **not** all be treated as the same kind of plugin.

They should be classified as:

- DCC Plugin: texture-importer, rename-lowhigh-proximity
- Legacy DCC Capability: totex, MayaToPainter, SubstancePainterToMaya
- AI/PBR Service: fal-texture-pbr-generator
- External PBR Tool: Procedural-PBR
- Substance Designer Capability: SubstanceDesignerTools

The Toolkit should expose capabilities through adapters instead of directly importing arbitrary third-party code into the core.

## Runtime test plan

The next real test stage requires Windows with supported versions of:

1. Maya
2. 3ds Max
3. Substance 3D Painter where required
4. Substance 3D Designer where required

For each plugin we will run:

- clean install test
- Toolkit startup test
- DCC startup test
- plugin load test
- basic operation test
- invalid-input test
- dependency-missing test
- version-mismatch test
- exception-isolation test
- uninstall/rollback test

A plugin is not marked production-ready until these runtime tests pass.

## Current conclusion

The current plugin collection is **not yet production-safe as an automatically installed bundle**.

The safe architecture is to keep the repositories isolated, classify them by capability, add compatibility gates, and only enable a plugin when its DCC/version/dependencies are verified.
