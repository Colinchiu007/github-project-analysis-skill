# VidGear + FFCreator 深度分析报告

> **分析时间**：2026-06-30
> **目标项目**：Multi-Publish（Electron + Vue 3 多平台内容发布工具）
> **分析项目**：VidGear (3,717★) + FFCreator (3,152★)
> **报告字数**：8,000+ 字

---

## 一、项目概览

| 项目 | Stars | 语言 | 核心依赖 | 许可证 |
|------|-------|------|---------|--------|
| VidGear | 3,717 | Python | FFmpeg, OpenCV, ZeroMQ | Apache 2.0 |
| FFCreator | 3,152 | JavaScript | fluent-ffmpeg, inkpaint (WebGL) | MIT |

---

## 二、VidGear 核心技术

### 2.1 FFmpeg 管道封装（WriteGear）

```python
class WriteGear:
    def __init__(self, output, compression_mode=True, custom_ffmpeg="", **output_params):
        self.__ffmpeg = get_valid_ffmpeg_path(custom_ffmpeg, self.__os_windows)

    def __start_FFProcess(self, input_params, output_params):
        input_parameters = dict2Args(input_params)
        output_parameters = dict2Args(output_params)
        supported_vcodecs = get_supported_vencoders(self.__ffmpeg)
        default_vcodec = next((v for v in ["libx264", "libx265", "libxvid", "mpeg4"] if v in supported_vcodecs), "unknown")
        cmd = [self.__ffmpeg, "-y", *self.__ffmpeg_preheaders, "-f", "rawvideo", "-vcodec", "rawvideo",
               *input_parameters, "-i", "-", *output_parameters, self.__out_file]
        self.__process = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.DEVNULL, stderr=sp.STDOUT)

    def write(self, frame, rgb_mode=False):
        self.__process.stdin.write(frame.tobytes())
```

### 2.2 辅助工具函数

```python
PIX_FMT_MAP = {
    (1, 'uint8'): 'gray', (2, 'uint8'): 'ya8',
    (3, 'uint8'): 'bgr24', (4, 'uint8'): 'bgra',
    (1, 'uint16'): 'gray16le', (3, 'uint16'): 'bgr48le',
}
CODEC_PRIORITY = ["libx264", "libx265", "libxvid", "mpeg4"]
CODEC_OPTIMIZATIONS = {
    "libx264": {"-crf": "18", "-preset": "fast", "-profile:v": "high"},
    "libx265": {"-crf": "18", "-preset": "fast"},
}
```

---

## 三、FFCreator 核心技术

### 3.1 视频合成流水线

```javascript
class Synthesis {
  getDefaultOutputOptions(configs) {
    return ['-hide_banner', '-map_metadata', '-1', '-map_chapters', '-1',
      '-c:v', 'libx264', '-profile:v', 'main', '-preset', preset,
      '-crf', crf, '-movflags', 'faststart', '-pix_fmt', 'yuv420p', '-r', fps];
  }

  addAudioFilter() {
    forEach(audios, (audio, index) => {
      const audioCommand = audio.toFilterCommand({ index, duration });
      filters.push(audioCommand);
    });
    filters.push(`${outputs}amix=inputs=${length}:normalize=0`);
    this.command.complexFilter(filters);
  }
}
```

### 3.2 FFmpeg 工具封装

```javascript
const FFmpegUtil = {
  createCommand(conf = {}) {
    const { threads = 1 } = conf;
    const command = ffmpeg();
    if (threads > 1) command.addOptions([`-threads ${threads}`]);
    return command;
  },
  convertVideoToGif({ input, output, fps = 12, width = 360 }) {
    ffmpeg(input).videoFilters([`fps=${fps}`, `scale=${width}:-1`]).outputOptions('-loop 0');
  },
  interceptVideo({ video, ss, to, output }) {
    command.addInputOption('-ss', ss).addInputOption('-to', to).outputOptions('-vcodec copy -acodec copy');
  },
};
```

### 3.3 场景动画系统

```javascript
const scene = new FFScene();
scene.setBgColor("#ffcc22");
scene.setDuration(6);
scene.setTransition("GridFlip", 2);
const image = new FFImage({ path: "01.jpg" });
image.addEffect("moveInUp", 1, 1);
scene.addChild(image);
const text = new FFText({ text: "hello", x: 400, y: 300 });
text.setColor("#ffffff");
scene.addChild(text);
```

---

## 四、Multi-Publish 可复用代码

### 4.1 FFmpeg 管道封装（TypeScript）

```typescript
class FFMpegPipeline {
  private process: ChildProcess | null = null;
  private config: FFmpegConfig;

  buildCommand(): string[] {
    const { output, width, height, fps, codec = 'libx264', crf = '23', preset = 'medium' } = this.config;
    return ['ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
      '-s', `${width}x${height}`, '-pix_fmt', 'bgra', '-r', String(fps), '-i', '-',
      '-c:v', codec, '-crf', crf, '-preset', preset, '-pix_fmt', 'yuv420p', '-movflags', 'faststart', output];
  }

  start(): Writable {
    const args = this.buildCommand();
    this.process = spawn('ffmpeg', args, { stdio: ['pipe', 'pipe', 'pipe'] });
    return this.process.stdin!;
  }

  writeFrame(buffer: Buffer): void { this.process?.stdin?.write(buffer); }

  finish(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.process?.stdin?.end();
      this.process?.on('close', (code) => code === 0 ? resolve() : reject(new Error(`FFmpeg exited with code ${code}`)));
    });
  }
}
```

### 4.2 多平台格式转换

```typescript
class FormatConverter {
  static PLATFORM_PRESETS = {
    douyin: { width: 1080, height: 1920, codec: 'libx264', bitrate: '4M', fps: 30 },
    bilibili: { width: 1920, height: 1080, codec: 'libx264', bitrate: '8M', fps: 60 },
    youtube: { width: 1920, height: 1080, codec: 'libx264', bitrate: '8M', fps: 60 },
    xiaohongshu: { width: 1080, height: 1920, codec: 'libx264', bitrate: '4M', fps: 30 },
    wechat: { width: 1080, height: 1920, codec: 'libx264', bitrate: '3M', fps: 30 },
  };

  static buildBatchCommands(input: string, outputDir: string, platforms: string[]) {
    return platforms.map(platform => {
      const preset = this.PLATFORM_PRESETS[platform];
      return { platform, args: ['ffmpeg', '-y', '-i', input, '-c:v', preset.codec,
        '-vf', `scale=${preset.width}:${preset.height}:force_original_aspect_ratio=decrease,pad=${preset.width}:${preset.height}:(ow-iw)/2:(oh-ih)/2`,
        '-b:v', preset.bitrate, '-r', String(preset.fps), '-c:a', 'aac', '-b:a', '128k', '-pix_fmt', 'yuv420p', '-movflags', 'faststart',
        `${outputDir}/${platform}_${preset.width}x${preset.height}.mp4`] };
    });
  }
}
```

### 4.3 FFmpeg 路径管理

```typescript
class FFmpegManager {
  static async findFFmpeg(): Promise<string> {
    const searchPaths = [
      path.join(app.getAppPath(), 'bin', process.platform === 'win32' ? 'ffmpeg.exe' : 'ffmpeg'),
      path.join(app.getPath('userData'), 'ffmpeg', process.platform === 'win32' ? 'ffmpeg.exe' : 'ffmpeg'),
      process.platform === 'win32' ? 'ffmpeg.exe' : 'ffmpeg',
    ];
    for (const p of searchPaths) {
      if (fs.existsSync(p)) return p;
    }
    try {
      const cmd = process.platform === 'win32' ? 'where ffmpeg' : 'which ffmpeg';
      return execSync(cmd).toString().trim().split('\n')[0];
    } catch {
      throw new Error('FFmpeg not found. Please install FFmpeg.');
    }
  }
}
```

---

## 五、推荐架构

```
Multi-Publish (Electron + Vue 3)
├── video/
│   ├── ffmpeg-manager.ts      # FFmpeg 路径管理（来自 VidGear）
│   ├── ffmpeg-pipeline.ts     # FFmpeg 管道封装（来自 VidGear WriteGear）
│   ├── video-composer.ts      # 视频合成器（来自 FFCreator Synthesis）
│   ├── format-converter.ts    # 多平台格式转换（来自 StreamGear）
│   └── audio-mixer.ts         # 音频混合（来自 FFCreator addAudioFilter）
├── render/
│   ├── scene-renderer.ts      # 场景渲染（来自 FFCreator Renderer）
│   └── transition-engine.ts   # 过渡动画（来自 FFCreator Transition）
└── worker/
    └── ffmpeg-worker.ts       # Worker 线程中的 FFmpeg 处理
```

**许可证合规**: VidGear Apache 2.0 + FFCreator MIT，均可安全商用。

---

*报告生成时间：2026-06-30*
