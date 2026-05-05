# UGA-openpilot — Mach-E 调车清单

> Fork 自 [FrogAi/FrogPilot](https://github.com/FrogAi/FrogPilot)，目标在 Mach-E + Nuvo PC 上复刻 [Bilibili BV11x421Q7VP](https://www.bilibili.com/video/BV11x421Q7VP/) 的 L2 ADAS + NOO 效果。完整背景见 [`uga/CLAUDE.md`](uga/CLAUDE.md)。**驾驶员必须始终监督；这不是 L4。**

## 上车前(在 Nuvo 上)按顺序跑

```bash
# 0. 在 Nuvo 上 clone（如果还没）
cd ~ && git clone git@github.com:UGA-MOBILITY-LAB/UGA-openpilot.git
cd ~/UGA-openpilot

# 1. 拉最新（每次调车前都跑这个）
git pull --rebase origin uga-main

# 2. 装依赖（首次 + 上游有大改时跑）
tools/op.sh setup    # ARM-only 包失败可 skip

# 3. 配 Mapbox token（首次。token 你自己保管,不要 commit）
python3 -c "from openpilot.common.params import Params; Params().put('MapboxSecretKey', 'pk.YOUR_TOKEN_HERE')"

# 4. 准备数据(任选一)
#  4a. 推荐: rosbag(真 Lucid 数据, Step 1+2 同时验证)
#    在车上 / 静止状态: ros2 bag record /camera/image_rect (mache 内开 20-30 min)
#    存到 ~/recorded_bag/  (rosbag2 是个目录,里面有 metadata.yaml + .db3)
#
#  4b. 退而求其次: 手机/GoPro 录的 mp4(只测 PC 管线,跳过 BAYER demosaic)
#    1080p@30fps, 存到 ~/dashcam_test.mp4

# 5. 跑！
./uga/launch/op_pc_run.sh --rosbag ~/recorded_bag       # 模式 4a (推荐)
# 或
./uga/launch/op_pc_run.sh ~/dashcam_test.mp4            # 模式 4b
# 或(实车 stationary, ds_video_gst 已起):
./uga/launch/op_pc_run.sh --live
```

## 在另一个终端验证 model 输出

```bash
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

期望：消息 ≥ 5 Hz，laneLines = 4。

## 出错时

把以下内容贴回 Claude（任一就行，越多越好）：

1. `./uga/launch/op_pc_run.sh ...` 启动后的完整 stderr/stdout
2. `tools/op.sh setup` 装依赖时哪些包失败
3. 进程是否在跑 → `pgrep -af 'modeld|ros_image_to_vipc|video_to_vipc|ros2 bag'`
4. `ros2 topic hz /camera/image_rect`（rosbag 模式下应该有数据）
5. `~/.comma/log/` 或 manager 的 log 路径下最新 log

## 当前进度

- [x] **Step 0**: Fork FrogPilot, clone, uga-main 分支
- [x] **Step 1 写代码**: `uga/tools/{video,ros_image}_to_vipc.py` + `uga/launch/op_pc_run.sh`
- [ ] **Step 1 Nuvo 实测**: 用 rosbag 跑通 modeld，输出合理 modelV2  ← **下次调车做这个**
- [ ] **Step 2**: 同样代码接 live `/camera/image_rect`（车 stationary 接 ds_video_gst）。Step 1 通了基本免费
- [ ] **Step 3**: Mach-E + Dataspeed 控制 port（Bridge 方案，复用 vehicle_interface_node 转换逻辑）
- [ ] **Step 3.5**: ARS408 雷达接入 → openpilot `radarState`（增强 ACC，特别远距 lead 跟踪）
- [ ] **Step 4**: NOO 在 PC 上跑通，能设目的地拿 turn-by-turn
- [ ] **Step 5**: 实车测试（mache 校园，驾驶员监督下）

## 已知风险

1. **Mach-E 是单目相机**，FrogPilot model 硬性期望双目。`--wide` mock 同帧让 model 能跑；wide-FOV 依赖功能（远处 leads / 横向目标 / 分岔选边）会 degrade。Step 5 实测后再决定加二号相机
2. **Mach-E port 是 stock Ford 路径**（PCM/PSCM via stock ADAS），跟你的 Dataspeed 不通，Step 3 必做
3. **PC 路线小众**，FrogPilot 主要 target Comma 3X，要踩坑
4. **雷达暂用 vision-only**（Step 3.5 之前）：低速 ACC 够用，高速 / 雨雾 / 夜可能不稳。Continental ARS408 跟 openpilot 期望的 stock Ford 雷达（FORD_CADS.dbc）协议不通，要写桥接

完整技术上下文 / 决策记录 / step-by-step → [`uga/CLAUDE.md`](uga/CLAUDE.md)

---

# Upstream FrogPilot README（保留作参考）

<div align="center" style="text-align: center;">

<h1>openpilot</h1>

<p>
  <b>openpilot is an operating system for robotics.</b>
  <br>
  Currently, it upgrades the driver assistance system in 300+ supported cars.
</p>

<h3>
  <a href="https://docs.comma.ai">Docs</a>
  <span> · </span>
  <a href="https://docs.comma.ai/contributing/roadmap/">Roadmap</a>
  <span> · </span>
  <a href="https://github.com/commaai/openpilot/blob/master/docs/CONTRIBUTING.md">Contribute</a>
  <span> · </span>
  <a href="https://discord.comma.ai">Community</a>
  <span> · </span>
  <a href="https://comma.ai/shop">Try it on a comma 3X</a>
</h3>

Quick start: `bash <(curl -fsSL openpilot.comma.ai)`

[![openpilot tests](https://github.com/commaai/openpilot/actions/workflows/selfdrive_tests.yaml/badge.svg)](https://github.com/commaai/openpilot/actions/workflows/selfdrive_tests.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![X Follow](https://img.shields.io/twitter/follow/comma_ai)](https://x.com/comma_ai)
[![Discord](https://img.shields.io/discord/469524606043160576)](https://discord.comma.ai)

</div>

<table>
  <tr>
    <td><a href="https://youtu.be/NmBfgOanCyk" title="Video By Greer Viau"><img src="https://github.com/commaai/openpilot/assets/8762862/2f7112ae-f748-4f39-b617-fabd689c3772"></a></td>
    <td><a href="https://youtu.be/VHKyqZ7t8Gw" title="Video By Logan LeGrand"><img src="https://github.com/commaai/openpilot/assets/8762862/92351544-2833-40d7-9e0b-7ef7ae37ec4c"></a></td>
    <td><a href="https://youtu.be/SUIZYzxtMQs" title="A drive to Taco Bell"><img src="https://github.com/commaai/openpilot/assets/8762862/05ceefc5-2628-439c-a9b2-89ce77dc6f63"></a></td>
  </tr>
</table>


Using openpilot in a car
------

To use openpilot in a car, you need four things:
1. **Supported Device:** a comma 3/3X, available at [comma.ai/shop](https://comma.ai/shop/comma-3x).
2. **Software:** The setup procedure for the comma 3/3X allows users to enter a URL for custom software. Use the URL `openpilot.comma.ai` to install the release version.
3. **Supported Car:** Ensure that you have one of [the 275+ supported cars](docs/CARS.md).
4. **Car Harness:** You will also need a [car harness](https://comma.ai/shop/car-harness) to connect your comma 3/3X to your car.

We have detailed instructions for [how to install the harness and device in a car](https://comma.ai/setup). Note that it's possible to run openpilot on [other hardware](https://blog.comma.ai/self-driving-car-for-free/), although it's not plug-and-play.

------

<div align="center" style="text-align: center;">

<h1>FrogPilot 🐸</h1>

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/FrogAi/FrogPilot)
[![Discord](https://img.shields.io/discord/1137853399715549214?label=Discord)](https://discord.frogpilot.com)
[![Last Updated](https://img.shields.io/badge/Last%20Updated-February%2028th%2C%202025-brightgreen)](https://github.com/FrogAi/FrogPilot/releases/latest)
[![Wiki](https://img.shields.io/badge/Wiki-FrogPilot-blue?logo=wiki)](https://frogpilot.com/wiki/)

</div>

------

**FrogPilot** is a custom, community-driven, frog-themed fork of openpilot that grows and improves through the ideas and contributions of its users. It offers exciting new features and cutting-edge experiments that often arrive long before official releases. As an unofficial and highly experimental version of openpilot, **FrogPilot** should *always* be used with caution!

openpilot vs **FrogPilot**
------

#### Community
| Feature | openpilot | **FrogPilot** |
|---------|:---------:|:---------:|
| A Welcoming Community | ❌ | ✅ |
| Erich / Primary Moderators / 🦇 | ✅ | ❌ |

#### Core Features
| Feature | openpilot | **FrogPilot** |
|---------|:---------:|:---------:|
| Always On Lateral (Steering) | ❌ | ✅ |
| Blind Spot Integration | ✅ | ✅ |
| Conditional Experimental Mode | ❌ | ✅ |
| Custom Themes | ❌ | ✅ |
| Driver Monitoring | ✅ | ✅ |
| Driving Model Selector | ❌ | ✅ |
| Holiday Themes | ❌ | ✅ |
| Speed Limit Support | ❌ | ✅ |
| Weather Detection | ❌ | ✅ |

#### Device & Hardware
| Feature | openpilot | **FrogPilot** |
|---------|:---------:|:---------:|
| Advanced Volume Controller | ❌ | ✅ |
| Automatic Version Backups | ❌ | ✅ |
| C3 Support | ❌ | ✅ |
| comma Pedal Support | ❌ | ✅ |
| High Quality Recordings | ❌ | ✅ |
| SDSU Support | ❌ | ✅ |
| ZSS Support | ❌ | ✅ |

#### Gas/Brake
| Feature | openpilot | **FrogPilot** |
|---------|:---------:|:---------:|
| Adaptive Cruise Control (ACC) | ✅ | ✅ |
| Advanced Live Tuning | ❌ | ✅ |
| Custom Following Distances | ❌ | ✅ |
| Faster Human-Like Acceleration | ❌ | ✅ |
| Human-Like Speed Control in Curves | ❌ | ✅ |
| Smoother Human-Like Braking | ❌ | ✅ |

#### Steering
| Feature | openpilot | **FrogPilot** |
|---------|:---------:|:---------:|
| Advanced Live Tuning | ❌ | ✅ |
| Automatic Lane Changes | ❌ | ✅ |
| Increased Steering Torque* | ❌ | ✅ |
| Lane Centering (LKAS) | ✅ | ✅ |
| Lane Change Assist | ✅ | ✅ |

*Select vehicles only

And much much more!

🌟 Highlight Features
------

### 🚗 Always On Lateral (AOL)

With **"Always On Lateral"**, lane-centering stays active whenever cruise control is on, even when you press the accelerator or brake. This means steering assist won't cut out during manual speed adjustments giving you continuous support through curves, traffic, or mountain roads!

---

### 🧠 Conditional Experimental Mode (CEM)

**["Experimental Mode"](https://blog.comma.ai/090release/#experimental-mode)** lets openpilot drive at the speed it thinks a human would to allow slowing for curves, stopping at stoplights/stop signs, and adapting to traffic. This makes it powerful in complex scenarios, but it's still, well, "experimental" and less predictable than **"Chill Mode"**. But **"Conditional Experimental Mode"** gives you the best of both worlds by automatically switching between **"Chill Mode"** for steady cruising and **"Experimental Mode"** for more advanced situations to help fully automate your driving experience!

**"Conditional Experimental Mode"** switches into **"Experimental Mode"** when conditions like these are met:
- Approaching curves and turns
- Detecting slower or stopped lead vehicles
- Driving below a set speed
- Predicting an upcoming stop (e.g. stoplight or stop sign)

Once conditions clear it returns to **"Chill Mode"** for stability and predictability.

**Note: Stay attentive as "Experimental Mode" is an alpha feature and mistakes are expected!**

---

### 🎭 Driving Personalities

With **"Driving Personalities"**, you choose how the vehicle behaves with four adjustable profiles:

- **Traffic:** Catered towards stop-and-go traffic by minimizing gaps and delays  
- **Aggressive:** Aimed to provide tighter following distances and quicker reactions  
- **Standard:** Useful for a balanced, all-purpose driving  
- **Relaxed:** A smoother driving experience with larger following distance gaps  

Each profile can be fine-tuned to change the desired following distance, acceleration, and braking style letting you shape **FrogPilot**'s behavior to match your own driving preferences! Profiles can be switched instantly using the following distance button on the steering wheel, while **"Traffic Mode"** can be enabled by simply holding down the following distance button.

---

### 📏 Speed Limit Controller (SLC)

With **"Speed Limit Controller"**, **FrogPilot** automatically adapts to the road's posted speed using information from downloaded **["OpenStreetMap"](https://www.openstreetmap.org)** maps, online **["Mapbox"](https://www.mapbox.com)** data, and the vehicle's dashboard (if supported).

Offsets let you fine-tune how closely **FrogPilot** follows posted limits across different speed ranges allowing you to cruise slightly above or below for a more natural driving experience. If no speed limit is available, you can choose whether **FrogPilot** drives at the set speed, falls back to the last known speed limit, or uses **"Experimental Mode"** to estimate one with the driving model.

Maps can be downloaded directly in settings and updated automatically on a schedule ensuring your device always has the latest speed limits!

**Note: Speed limits are only as accurate as the available speed limit data. Always stay attentive and adjust your speed when necessary!**

---

### 🎨 Themes

With **"Themes"**, you can personalize **FrogPilot**'s driving screen to make it uniquely yours! Choose from:

- **Color Schemes**
- **Icon Packs**
- **Sound Packs**
- **Turn Signal Animations**
- **Steering Wheel Icons**

Enjoy pre-existing **FrogPilot** and seasonal holiday themes, or you can create your own with the **"Theme Maker"** and even share them with the community! For extra fun, enable features like the Mario Kart–style **"Rainbow Path"** or **"Random Events"** that add playful visual effects while you drive!

---

And lots more! From safety enhancements to personalization options, **FrogPilot** continues to evolve with features that put you in control. Check it out today for yourself!

---

🔧 Branches
------
| Branch                     | Install&nbsp;URL          | Description                                            | Recommended&nbsp;For     |
|----------------------------|---------------------------|--------------------------------------------------------|--------------------------|
| FrogPilot                  | frogpilot.download        | The main release branch.                               | Everyone                 |
| FrogPilot&#8209;Staging    | staging.frogpilot.download| Beta branch with upcoming features. Expect bugs!       | Early&nbsp;Adopters      |
| FrogPilot&#8209;Testing    | testing.frogpilot.download| Alpha branch with bleeding-edge features. Breaks often!| Advanced&nbsp;Testers    |
| FrogPilot&#8209;Development| No :)                     | Active development branch. Do not use!                 | **FrogPilot**&nbsp;Developers|
| MAKE&#8209;PRS&#8209;HERE  | No :)                     | Workspace for pull requests. Do not use!               | Contributors             |

🧰 How to Install
------

The easiest way to install **FrogPilot** is by entering this URL on the installation screen:

```
frogpilot.download
```

**DO NOT** install the **FrogPilot-Development** branch. I'm constantly breaking things on there, so unless you don't want to use **FrogPilot**, **NEVER** install it!

![](https://i.imgur.com/FsufQtO.png)

🐞 Bug Reports / Feature Requests
------

If you run into bugs, issues, or have ideas for new features, please post about it on the **[FrogPilot Discord](https://discord.gg/frogpilot)**! Feedback helps improve **FrogPilot** and create a better experience for everyone!

To report a bug, please post it in [**#bug-reports**](https://discord.com/channels/1137853399715549214/1162100167110053888).  
To request a feature, please post it in [**#feature-requests**](https://discord.com/channels/1137853399715549214/1160318669839147259).  

Please include as much detail as possible! Photos, videos, log files, or anything that can help explain the issue or idea are very helpful!

I'll do my best to respond promptly, but not every request can be addressed right away. Your feedback is always appreciated and helps make **FrogPilot** the best it can be!

📋 Credits
------

* [Aidenir](https://github.com/Aidenir)
* [AlexandreSato](https://github.com/AlexandreSato)
* [cfranyota](https://github.com/cfranyota)
* [cydia2020](https://github.com/cydia2020)
* [dragonpilot-community](https://github.com/dragonpilot-community)
* [ErichMoraga](https://github.com/ErichMoraga)
* [garrettpall](https://github.com/garrettpall)
* [jakethesnake420](https://github.com/jakethesnake420)
* [jyoung8607](https://github.com/jyoung8607)
* [mike8643](https://github.com/mike8643)
* [neokii](https://github.com/neokii)
* [OPGM](https://github.com/opgm)
* [OPKR](https://github.com/openpilotkr)
* [pfeiferj](https://github.com/pfeiferj)
* [realfast](https://github.com/realfast)
* [syncword](https://github.com/syncword)
* [twilsonco](https://github.com/twilsonco)

Star History
------

[![Star History Chart](https://api.star-history.com/svg?repos=FrogAi/FrogPilot&type=Date)](https://www.star-history.com/#FrogAi/FrogPilot&Date)
