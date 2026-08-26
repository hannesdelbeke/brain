---
date: 2026-08-22
tags:
  - technical
  - hardware
  - gpu
  - benchmark
---
> [!quote] User Prompt
> *a while ago i wrote about laptops with gen 6 or gen 8 thinkpad i think. the one i concluded on or considered. write a comparison similar to "GPU comparison - Razer Blade 15 vs Dell Precision 5680" compare with razor*

Side-by-side comparison of graphics architecture, compute performance, VRAM throughput, local AI inference, thermals, and daily usability between the **[[razor blade 15 rz09-02705w76 2018|Razer Blade 15 (2018)]]** (Dedicated dGPU) and the **[[2026-08-11 laptop research|Lenovo ThinkPad X1 Yoga Gen 7 / Gen 8]]** (Integrated iGPU).
[[Lenovo ThinkPad X1 Yoga Gen 7]]

---

## 1. Silicon & Graphics Architecture Specs

| Specification | [[razor blade 15 rz09-02705w76 2018\|Razer Blade 15]] (2018) | ThinkPad X1 Yoga Gen 8 (2023) / Gen 7 (2022) | Practical Trade-Off |
| :--- | :--- | :--- | :--- |
| **GPU Model** | **NVIDIA GeForce GTX 1060 Max-Q** | **Intel Iris Xe Graphics (96 EUs)** | Dedicated dGPU vs Integrated SoC iGPU |
| **Architecture** | Pascal (16nm FinFET, GP106) | Intel Xe-LP (10nm SuperFin / Intel 7) | Modern low-power SoC integration |
| **VRAM Type & Capacity**| **6 GB GDDR5 (Dedicated)** | **Shared System Memory (LPDDR5-5200 / 6400)** | Dedicated VRAM vs Dynamic Unified Memory |
| **Memory Bus & Bandwidth** | 192-bit / **~192 GB/s** | 128-bit dual-channel / **~83–102 GB/s** | Razer has **~2x higher memory bandwidth** |
| **Execution Units / Cores** | 1,280 CUDA Cores | 96 Execution Units (768 Shading ALUs) | Razer has **1.67x raw shader count** |
| **Tensor / Matrix Cores** | None (0) | DP4A (INT8/FP16 AI matrix instructions) | ThinkPad supports modern INT8/FP16 acceleration |
| **Ray Tracing Hardware** | None (0) | None (0) | Neither supports hardware RT |
| **Peak FP32 Compute** | **~3.8 TFLOPS** | **~2.2 – 2.5 TFLOPS** | Razer leads raw FP32 rasterization by ~55% |
| **TGP / Power Envelope** | **60W – 70W** (Dedicated GPU alone) | **15W – 28W** (Combined CPU + GPU package) | ThinkPad uses **~4x less power** |

---

## 2. Architectural Comparison: Dedicated vs Integrated

### Razer Blade 15 (GTX 1060 Max-Q Dedicated)
- **Dedicated Memory Bus Advantage:** The 192 GB/s dedicated GDDR5 memory bus ensures frame rates in 3D viewports (Maya, Blender, Unreal) and games do not stall due to CPU memory contention.
- **Older Instruction Set:** Pascal lacks INT8/FP16 matrix math extensions (DP4A / Tensor Cores), requiring all neural operations to run in standard FP32 with higher energy cost.
- **Power & Heat Penalty:** The dedicated GPU requires a minimum 60W power draw under 3D load, necessitating a heavy 230W proprietary barrel power brick and causing persistent fan noise ([[Razor Blade 15 - loud fans]]).

### ThinkPad X1 Yoga Gen 7/8 (Intel Iris Xe 96EU Integrated)
- **Unified Low-Power Architecture:** The GPU shares the CPU’s ultra-fast LPDDR5 system RAM (allocating up to 50% of system RAM, e.g., 16 GB on a 32 GB laptop).
- **Modern Compute & AI Extensions:** Supports Intel OpenVINO, DirectML, and DP4A instructions for fast INT8/FP16 quantization, allowing small AI models and embedding generators to run efficiently within a 20W thermal envelope.
- **AV1 & Modern Media Engine:** Features Intel QuickSync with hardware AV1 decode and modern VP9/HEVC 10-bit hardware acceleration, drawing negligible battery power during video playback.

---

## 3. Real-World Workload Benchmark Estimates

| Workload | Razer Blade 15 (GTX 1060 6GB) | ThinkPad X1 Yoga Gen 8 (Iris Xe 96EU) | Practical Takeaway |
| :--- | :--- | :--- | :--- |
| **PKM Vector Indexing** (`fastembed` / `BGE-small`) | ~30–50 sections/sec (DirectML / CPU) | **45–70 sections/sec** (OpenVINO / DirectML DP4A) | ThinkPad matches or exceeds Razer via modern instructions |
| **Local LLM Inference** (`Llama-3.2-1B-Q4`) | ~20–30 tokens/sec (Full GPU offload) | **25–35 tokens/sec** (OpenVINO / llama.cpp) | Both provide snappy 1B–3B text inference |
| **Local LLM Inference** (`Llama-3.1-8B-Q4`) | **OOM** (Spills into system RAM, ~1–2 t/s) | **6–10 tokens/sec** (Fits in 32GB unified RAM) | ThinkPad runs 8B models without crashing |
| **3D DCC Viewport** (Maya / Blender 1080p) | **60+ FPS** (Dense meshes & textures) | **30–45 FPS** (Light/Medium geometry) | Razer is smoother for heavy DCC viewports |
| **Blender Cycles Render** (Classroom scene) | **~140–180 seconds** (CUDA FP32) | **~320–400 seconds** (oneAPI / CPU fallback) | Razer renders ~2x faster |
| **3D Gaming** (1080p Medium Settings) | **45–60+ FPS** (Stable) | **20–35 FPS** (720p / 1080p Low required) | Razer remains a dedicated gaming machine |

---

## 4. Daily Usability, Acoustics, and Portability

| Factor | Razer Blade 15 (2018) | ThinkPad X1 Yoga Gen 7 / 8 | Impact on Daily Use |
| :--- | :--- | :--- | :--- |
| **Chassis Weight** | **2.07 kg (4.5 lbs)** | **1.38 kg (3.0 lbs)** | **Saves 0.7 kg (1.5 lbs)** in bag |
| **Charger & Travel** | Proprietary 230W heavy brick (0.7 kg) | Standard 65W/100W USB-C PD (0.2 kg) | Single charger for phone + laptop |
| **Acoustics & Fan Noise** | 3,500–4,000 RPM locked idle floor | **0 RPM (Fan off)** during note-taking/browsing | Silent, distraction-free thinking |
| **Form Factor** | Rigid clamshell only | **360° 2-in-1 convertible** + touchscreen | Tablet mode for reading, sketching, and reviews |
| **Stylus Support** | None | **Integrated garaged stylus** (Always charged) | Instant handwriting and whiteboarding |
| **Battery Life** | 2.5 – 4 hours (Degraded 65 Wh) | **7 – 10 hours** (57 Wh on low-power U/P CPU) | Full day of note-taking untethered |

---

## 5. Bottom Line: Workstation Role Distribution

- **Keep the Razer Blade 15 for:** Stationary desk tasks requiring sustained GPU shader throughput, 3D viewport manipulation in Maya/Unreal, and PC gaming.
- **Choose the ThinkPad X1 Yoga Gen 8 / Gen 7 for:** The ideal mobile PKM, coding, and writing companion—saving substantial bag weight, eliminating fan noise, supporting all-day battery life on USB-C charging, and running local vector indexing silently.

---

## Top Relevant Notes
- [[2026-08-11 laptop research]] — comprehensive used-market buying guide for ThinkPad X1 Yoga generations (Gen 7–11).
- [[razor blade 15 rz09-02705w76 2018]] — hardware breakdown, ports, and upgrade history for the Razer Blade 15.
- [[Razor Blade 15 - loud fans]] — analysis of Razer Synapse fan floor and thermal behavior.
- [[GPU comparison - Razer Blade 15 vs Dell Precision 5680]] — companion comparison with workstation-tier Ada Lovelace silicon.
- [[what AI models can razor blade run]] — local model boundaries on 6GB VRAM.
