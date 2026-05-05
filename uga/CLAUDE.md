# UGA-openpilot — FrogPilot fork for UGA Mach-E

## 项目目标

复刻 [Bilibili 视频 BV11x421Q7VP](https://www.bilibili.com/video/BV11x421Q7VP/) 的效果：
**L2 ADAS + Navigate-on-openpilot (NOO) + 端到端模型在分岔路口"选边"**，能从 A 到 B（驾驶员监督）。

明确**不是 L4 自主驾驶**。L4 路径走 sibling 仓库 [UGA-AUTOWARE](https://github.com/UGA-MOBILITY-LAB/UGA-AUTOWARE)（Autoware + mache HD 地图）。

## 仓库结构

- **upstream**: `FrogAi/FrogPilot`（commaai/openpilot 的社区 fork，保留了 NOO + Mapbox 集成）
- **default branch**: `uga-main`（不是 `FrogPilot`）—— UGA 自己的工作分支
- **`FrogPilot` 分支**: 跟随上游，**不要在该分支上提交**
- **同级仓库**: `UGA-AUTOWARE`（Autoware 栈），跟此仓库**互不干扰**保留共存

### Sync 上游流程

```bash
git fetch upstream
git checkout FrogPilot
git merge --ff-only upstream/FrogPilot
git push origin FrogPilot
git checkout uga-main
git rebase FrogPilot
```

## 关键决策（2026-05-05）

- **硬件**：Nuvo PC + Lucid 相机 + Mach-E + Dataspeed by-wire（**不买 Comma 3X**）
- **Fork**：FrogPilot（不是 commaai 上游）—— 因为只有 FrogPilot 保留了 NOO
- **目标场景**：mache 校园内 + 周边公开道路
- **共存**：`UGA-AUTOWARE` 保持工作，本仓库独立

## FrogPilot vs commaai 上游差异

1. **vendor 子模块**：`cereal/`、`panda/`、`opendbc/`、`tinygrad_repo/` 直接是目录，不是 git submodule（没 `.gitmodules`）
2. **路径少一层**：commaai 上游 `opendbc_repo/opendbc/car/ford/` → FrogPilot `opendbc/opendbc/car/ford/`
3. **删了 tools/sim 和 tools/replay**：没法直接跑离线视频；要自己写 video → VisionIPC 桥接（见 Step 1）
4. **新增 `frogpilot/` 顶级目录**：含 navigation/mapd、speed_limit_filler、UI 主题等
5. **navd 仍存在**：`selfdrive/navd/navd.py`（commaai 上游已 deprecate）+ 增强版 `frogpilot/navigation/mapd.py`（离线 OSM）

## Step 1: 在 Nuvo 上跑通 modeld（offline）

**前置**：Ubuntu 22.04 + NVIDIA GPU + OpenCL libs。

### A. 装依赖

```bash
cd ~  # 或选你想放的位置
git clone git@github.com:UGA-MOBILITY-LAB/UGA-openpilot.git
cd UGA-openpilot
tools/op.sh setup       # PC 模式，自动跳过 ARM-only 依赖
```

留意 `tools/op.sh` 在 PC 上的安装日志，记下 ARM-only 失败包（如 qcom/agnos 相关）—— 这些可以 skip。

### B. 申请 Mapbox token（NOO 需要）

去 https://account.mapbox.com/access-tokens/ 申请免费 token。用法（任选一）：
- env var: `export MAPBOX_TOKEN=pk.xxx`
- 或 param: `params.put("MapboxSecretKey", "pk.xxx")`

### C. 启动 manager（PC 自动模式）

```bash
./launch_chffrplus.sh
```

`launch_chffrplus.sh` 会用 `system/hardware/__init__.py:PC = not TICI` 自动检测，manager (`system/manager/process_config.py`) 跳过 sensord/ubloxd/timed/tombstoned 等 Comma-3X-only 进程，只跑 PC 上能跑的：
- modeld（神经网络推理）
- frogpilot_process / mapd / speed_limit_filler
- navd（如果 token 配好）
- ui

### D. 喂视频给 modeld（关键工程）

modeld 通过 **VisionIPC**（共享内存 + YUV NV12）从 `camerad` 进程接收图像。FrogPilot 删了 `tools/sim/` 和 `tools/replay/`，所以**没有现成的"视频喂 modeld"工具**，要自己写。

参考资料：
- VisionIPC Python binding: `msgq_repo/msgq/visionipc/__init__.py`
- camerad C++ 实现: `system/camerad/main.cc`
- 学习 VisionIPC API: `system/camerad/snapshot/snapshot.py`（reader 例子）

**TODO（未实现）**：`uga/tools/video_to_vipc.py` —— 用 ffmpeg/opencv 解码 MP4 → NV12 → VisionIpcServer 推到 ROAD_CAMERA stream。

### E. 录 dashcam 视频

mache 校园开 20-30 分钟，1080p@30fps（手机/GoPro 都行），保存到 `~/dashcam_test.mp4`。注意：
- modeld 期望帧率 ~20 Hz，30 fps 可以下采
- 分辨率最终要 crop/resize 到 1928×1208（YUV）
- camera intrinsics 要伪造（focal length / principal point），第一次跑可以用 commaai default 然后看 model 输出是否合理

### F. 验证

```bash
# 启动 manager 后另开一个 shell
cd ~/UGA-openpilot
python3 -c "
from cereal.messaging import SubMaster
sm = SubMaster(['modelV2'])
while True:
    sm.update(1000)
    if sm.updated['modelV2']:
        m = sm['modelV2']
        print(f'frame={m.frameId} laneLines={len(m.laneLines)} leads={len(m.leadsV3)}')
"
```

期望：消息频率 ≥ 5 Hz，laneLines = 4，leadsV3 ≥ 0。

## Step 2-5（后续）

见 plan 文件 `/home/haohua/.claude/plans/openpilot-mech-e-uga-autoware-cryptic-parrot.md`：

- **Step 2**: Lucid 相机 → openpilot VisionIPC（实时）
- **Step 3**: Mach-E + Dataspeed 控制 port（Bridge 方案：cereal `carControl` → ROS 2 → Dataspeed）
- **Step 4**: NOO 在 PC 端跑起来（UI 适配 + Mapbox 设目的地）
- **Step 5**: 实车测试（mache 校园 stationary → 慢速 lateral → NOO 短路径）

## 已知坑 / 风险

1. **PC 路线小众**：FrogPilot 主要 target Comma 3X，PC 端 setup 没有官方文档支持，要踩坑
2. **`tools/sim` 没了**：要么从 commaai 上游 cherry-pick 旧的 metadrive/CARLA bridge，要么自己写 video_to_vipc
3. **Lucid 5 Hz vs 期望 20 Hz**：要么调相机帧率，要么软件补帧（短期补帧，长期调相机）
4. **UI 假设触摸屏**：FrogPilot Qt UI 在 PC 上能跑但要鼠标操作；NOO 设目的地可能需要 CLI 替代
5. **Mach-E port 是 stock Ford**：`opendbc/opendbc/car/ford/values.py:146` 走的是 stock Ford ADAS，**不是 Dataspeed**。Step 3 要做控制 port

## 同级仓库交叉引用

如需车辆硬件信息（DBW、CAN 配置、IMU 标定、Nuvo 路径），见 `UGA-AUTOWARE/CLAUDE.md`。Step 3 的 Dataspeed 桥接代码会放在 `UGA-AUTOWARE/cereal_to_dataspeed/` 下。
