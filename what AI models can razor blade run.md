---
tags:
  - ai
  - hardware
  - gpu
  - llm
  - local-ai
---
To get fast, responsive performance on a 2018 Razer Blade (GTX 1060 Max-Q 6GB VRAM), use models sized to fit entirely in VRAM to process text instantly and generate images in seconds without paging into system RAM.

## 1. Large Language Models (Fast Text)

For real-time typing speeds (~20–35 tokens/sec), target 1B to 3B parameter models quantized to 4-bit (Q4_K_M or Q4_0):

- **Qwen2.5-1.5B-Instruct:** Extremely fast, low latency, strong coding and reasoning for its size.
- **Llama-3.2-1B-Instruct / 3B-Instruct:** Optimized by Meta; runs at high tokens/second on 6GB VRAM.
- **Phi-3.5-mini (3.8B):** Pushing the ceiling of 6GB VRAM, but fast if GPU offload is set to 100%.
- **Setup:** In Ollama or LM Studio, ensure `GPU Offload` is set to 100% (all layers in VRAM).

## 2. Computer Vision & Audio

Task-specific, non-generative models run at real-time speeds on Pascal CUDA cores:

- **[[Whisper]] (Base or Small):** Speech-to-text transcription runs faster than real-time speed.
- **YOLOv8 / YOLOv10:** Real-time object detection on live webcam feeds at 30+ frames per second.
- **Fastembed / BGE-small-en-v1.5:** Offline text embeddings at 150+ sections/second via DirectML.

## 3. Image Generation (Under 10 Seconds)

Standard Stable Diffusion 1.5/SDXL base runs slow. Use distilled Latent Consistency Models (LCM) or Turbo models:

- **SDXL Turbo / SD 1.5 LCM:** Generates images in 1 to 4 inference steps instead of 20–50 steps.
- **Setup:** Run via Fooocus or ComfyUI with `--lowvram` or `--medvram` enabled.

## References
- [[razor blade 15 rz09-02705w76 2018]]
- [[GPU comparison - Razer Blade 15 vs Dell Precision 5680]]
- [[GPU comparison - Razer Blade 15 vs ThinkPad X1 Yoga]]
- [[offline GPU embeddings with incremental cache]]
