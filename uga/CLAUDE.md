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

### B. 配置 Mapbox token（NOO 需要）

申请：https://account.mapbox.com/access-tokens/ （免费层够用，使用 public token，前缀 `pk.`）。

**重要：token 不要 commit 到这个 public 仓库**，下面三种本地存储方式任选一种：

```bash
# 方式 1: 环境变量（每次终端要重新 export 或写进 .bashrc 不入仓的部分）
export MAPBOX_TOKEN=pk.your_token_here

# 方式 2: openpilot params（持久化，存在 ~/.comma/params 之类的本地数据库）
python3 -c "from openpilot.common.params import Params; Params().put('MapboxSecretKey', 'pk.your_token_here')"

# 方式 3: ~/.config 之类的非追踪文件（自定义脚本读取，灵活）
```

`selfdrive/navd/navd.py:57-63` 优先读 `MAPBOX_TOKEN` 环境变量，再读 `MapboxSecretKey` param。FrogPilot 多个组件（speed_limit_controller、UI settings）都读 `MapboxSecretKey`，**长期推荐方式 2**。

### C. 启动 manager（PC 自动模式）

```bash
./launch_chffrplus.sh
```

`launch_chffrplus.sh` 会用 `system/hardware/__init__.py:PC = not TICI` 自动检测，manager (`system/manager/process_config.py`) 跳过 sensord/ubloxd/timed/tombstoned 等 Comma-3X-only 进程，只跑 PC 上能跑的：
- modeld（神经网络推理）
- frogpilot_process / mapd / speed_limit_filler
- navd（如果 token 配好）
- ui

### D. 喂数据给 modeld

modeld 通过 **VisionIPC**（共享内存 + YUV NV12）从 `camerad` 进程接收图像。FrogPilot 删了 `tools/sim/` 和 `tools/replay/`，所以没有现成工具，自己写在 `uga/tools/` 下。两个版本对应不同输入：

| 工具 | 输入 | 用途 |
|---|---|---|
| `video_to_vipc.py` | mp4/mkv 等视频文件 | 手机随手录的 dashcam，最快跑通 PC 管线 |
| `ros_image_to_vipc.py` | ROS 2 `sensor_msgs/Image` | rosbag 回放 OR live 实车 ds_video_gst（推荐） |

**`ros_image_to_vipc.py` 是 Step 1 + Step 2 的核心代码**：
- 订阅 `/camera/image_rect`（BAYER_RG_8 2448×2048 @ 5 Hz）
- cv2 demosaic → BGR → PyAV reformat → NV12 1928×1208
- VisionIpcServer 推 ROAD + WIDE_ROAD（mock 双目）
- cereal `roadCameraState` 同步发布
- `--upsample 4` 把 5 Hz 升到 20 Hz（重复帧 + 50ms 间隔合成时间戳）

跑通 rosbag 模式后，**Step 2 = 同样代码加 `--live` 接车上的 ds_video_gst**，几乎免费。

**已知限制（在 Nuvo 上跑后再修）**：
- 不发 `liveCalibration` —— 期望 manager 跑 calibrationd；不跑则 modeld 卡等
- transform 是 identity；Mach-E 的 Lucid 朝前装，第一次跑应该 OK
- 时间戳：mp4 模式合成；rosbag 模式用 `msg.header.stamp` 但 upsample 时合成 sub-frame 时间戳
- 重复帧 4× 让 model 看同帧 4 次，可能干扰 temporal dynamics——长期应该把 Lucid 调到 20 Hz 原生

### D'. 一键启动: `uga/launch/op_pc_run.sh`

三种模式：

```bash
./uga/launch/op_pc_run.sh ~/dashcam_test.mp4          # mp4 模式
./uga/launch/op_pc_run.sh --rosbag ~/recorded_bag     # rosbag 模式 (推荐 Step 1)
./uga/launch/op_pc_run.sh --live                      # live 实车 (Step 2/5)
```

脚本会先把 `IsDriverViewEnabled` param 强制设为 false，避免 manager 启动真 `camerad` 跟我们的 fake VisionIPC server 冲突（real camerad 由 `system/manager/process_config.py:driverview` 条件控制，driverview = started OR IsDriverViewEnabled）。

rosbag/live 模式下脚本会自动 `source /opt/ros/humble/setup.bash` 让 rclpy 可用。

### E. 数据采集

**rosbag 模式（推荐）**：在车上启动 UGA-AUTOWARE 的 `ros2 launch uga devices.launch.xml` 让 ds_video_gst + IMU + GPS 都跑起来，然后：

```bash
ros2 bag record /camera/image_rect      # 最小:只录相机
# 或更全(以后 Step 3.5 雷达接入会需要):
ros2 bag record /camera/image_rect /front_radar/* /rear_radar/* \
  /sensing/imu/imu_data /vehicle/dbw_enabled
```

mache 内开 20-30 分钟，包括直道 + 弯道 + 路口 + 有车流。bag 是个目录（`recorded_bag/metadata.yaml + *.db3`）。

**mp4 模式（fallback）**：手机/GoPro 1080p@30fps，存 `~/dashcam_test.mp4`。比 rosbag 弱：跟实战 Lucid 分辨率/格式/视场角不同；不能用作 Step 2 验证。

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

- **Step 2**: 同样的 `ros_image_to_vipc.py` 代码加 `--live`，接车上的 ds_video_gst 实时流。Step 1 跑通 rosbag 后，Step 2 几乎免费
- **Step 3**: Mach-E + Dataspeed 控制 port（Bridge 方案：cereal `carControl` → ROS 2 → Dataspeed `UlcCmd` + `SteeringCmd`，复用 `UGA-AUTOWARE/dataspeed_mache_interface/vehicle_interface_node.py:144-260` 的转换逻辑）
- **Step 3.5**: ARS408 雷达接入。Continental ARS408 → ROS 2（UGA-AUTOWARE 已有 driver）→ `ros_radar_to_cereal` 桥接 → openpilot `radarState` (`leadOne`/`leadTwo`)。
  - 上游 openpilot Ford 假设 stock Ford 雷达（`opendbc/dbc/FORD_CADS.dbc`），跟 ARS408 协议不通，必须自己写桥接
  - openpilot 0.10+ model 不再吃雷达输入，但 `radard` 仍用雷达给 ACC 提供 lead tracking（vision-only 在远距/雨雾不稳）
  - 工程量：1-2 周。在 Step 5 之前接，让实车 ACC 一上来就稳
- **Step 4**: NOO 在 PC 端跑起来（UI 适配 + Mapbox 设目的地）
- **Step 5**: 实车测试（mache 校园 stationary → 慢速 lateral → NOO 短路径）

## 已知坑 / 风险

1. **PC 路线小众**：FrogPilot 主要 target Comma 3X，PC 端 setup 没有官方文档支持，要踩坑
2. **`tools/sim` 没了**：自己写 video_to_vipc（已实现，见上）
3. **Lucid 5 Hz vs 期望 20 Hz**：要么调相机帧率，要么软件补帧（短期补帧，长期调相机）
4. **UI 假设触摸屏**：FrogPilot Qt UI 在 PC 上能跑但要鼠标操作；NOO 设目的地可能需要 CLI 替代
5. **Mach-E port 是 stock Ford**：`opendbc/opendbc/car/ford/values.py:146` 走的是 stock Ford ADAS，**不是 Dataspeed**。Step 3 要做控制 port
6. **Mach-E 单目 vs FrogPilot model 期望双目**：`selfdrive/modeld/modeld.py:87,113-114` 硬性要求 `input_imgs` (narrow) + `big_input_imgs` (wide) 两个图像输入。Mach-E 上只有 Lucid TRI051S-C 一个相机。
   - **当前对策**：`video_to_vipc.py --wide` 把同一帧 mock 推到 ROAD + WIDE_ROAD 两个 stream，让 model 能跑
   - **预期 degradation**：lane keep / 直道车道保持影响小；wide 镜头主管的远处 leads + 周边/横向目标 + 变道决策 严重退化
   - **对视频效果的影响**：NOO 在分岔路口"选边"是视频核心能力，强依赖 wide camera。单目 mock 可能达不到视频效果
   - **后续选项**：先 mock 同帧跑通验证管线 → 实测后决定 (a) 加第二个 wide-FOV 相机 (b) 退而求其次只做 lane-keep

## 同级仓库交叉引用

如需车辆硬件信息（DBW、CAN 配置、IMU 标定、Nuvo 路径），见 `UGA-AUTOWARE/CLAUDE.md`。Step 3 的 Dataspeed 桥接代码会放在 `UGA-AUTOWARE/cereal_to_dataspeed/` 下。
