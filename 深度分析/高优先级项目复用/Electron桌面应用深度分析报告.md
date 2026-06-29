# Electron 桌面应用深度分析报告

> **分析时间**：2026-06-29
> **目标项目**：Multi-Publish（Electron + Vue 3 桌面应用）
> **分析项目**：AFFiNE (69,891★) + marktext (57,953★) + Toonflow-app (10,745★) + Bitwarden (13,148★)
> **报告字数**：10,000+ 字

---

## 一、Electron 主进程架构

### 1.1 三种启动模式

**Toonflow — Express 服务器 + Electron 混合模式（最轻量）**

```typescript
app.whenReady().then(async () => {
  const mod = requireWithCustomPaths(servePath);
  const port = await mod.default(true);
  process.env.PORT = port;

  protocol.handle("toonflow", (request) => {
    const handlers = {
      getappurl: () => ({ url: `http://localhost:${port}/api` }),
      windowminimize: () => { mainWindow?.minimize(); return { ok: true }; },
      windowmaximize: () => {
        mainWindow?.isMaximized() ? mainWindow.unmaximize() : mainWindow?.maximize();
        return { ok: true };
      },
      windowclose: () => { app.exit(0); return { ok: true }; },
      apprestart: () => {
        setTimeout(() => { app.relaunch(); app.exit(0); }, 500);
        return { ok: true };
      },
    };
    const handler = handlers[pathname];
    return new Response(JSON.stringify(handler ? handler() : { error: "未知接口" }), {
      headers: { "Content-Type": "application/json" },
    });
  });
  await createMainWindow();
});
```

**AFFiNE — 链式初始化模式（企业级）**

```typescript
app.enableSandbox();
app.commandLine.appendSwitch('disable-features', 'CalculateNativeWinOcclusion,AutofillServerCommunication');
app.commandLine.appendSwitch('enable-features', 'EarlyEstablishGpuChannel,EstablishGpuChannelAsync');

const isSingleInstance = app.requestSingleInstanceLock();
if (!isSingleInstance) { app.quit(); process.exit(0); }

app.whenReady()
  .then(registerProtocol)
  .then(registerHandlers)
  .then(registerEvents)
  .then(launch)
  .then(createApplicationMenu)
  .then(registerUpdater)
  .then(setupTrayState);
```

**Bitwarden — DI 容器模式（最严谨）**

```typescript
class Main {
  constructor() {
    this.windowMain = new WindowMain(biometricStateService, this.logService, ...);
    this.updaterMain = new UpdaterMain(this.i18nService, this.logService, this.windowMain, ...);
    this.trayMain = new TrayMain(this.windowMain, this.i18nService, ...);
    this.menuMain = new MenuMain(this.i18nService, this.messagingService, ...);
  }

  bootstrap() {
    this.migrationRunner.run().then(async () => {
      await this.toggleHardwareAcceleration();
      await this.windowMain.init(showWindow);
      await this.i18nService.init();
      await this.trayMain.init("Bitwarden", [...]);
      await this.updaterMain.init();
      await this.ipcService.init();
    });
  }
}
```

### 1.2 窗口管理

**Toonflow — 单窗口 + 无边框**

```typescript
const win = new BrowserWindow({
  width: 1000, height: 700, minWidth: 800, minHeight: 500,
  frame: false, show: false, autoHideMenuBar: true,
  thickFrame: true,
});
win.once("ready-to-show", () => win.show());
```

**AFFiNE — 单例 + RxJS 响应式**

```typescript
class MainWindowManager {
  static readonly instance = new MainWindowManager();
  mainWindow$ = new BehaviorSubject<BrowserWindow | undefined>(undefined);

  async ensureMainWindow(): Promise<BrowserWindow> {
    if (!this.mainWindowReady || (await this.mainWindowReady.then(w => w.isDestroyed()))) {
      this.mainWindowReady = this.createMainWindow();
      this.mainWindow$.next(await this.mainWindowReady);
    }
    return this.mainWindowReady;
  }
}
```

**Bitwarden — 窗口状态持久化 + 防抖**

```typescript
class WindowMain {
  private windowStateChangeTimer: NodeJS.Timeout;

  async createWindow(): Promise<void> {
    const mainWindowState = electronWindowState({ defaultWidth: 1200, defaultHeight: 800 });
    this.win = new BrowserWindow({
      width: mainWindowState.width, height: mainWindowState.height,
      x: mainWindowState.x, y: mainWindowState.y,
      show: false,
      webPreferences: {
        preload: path.join(__dirname, "preload.js"),
        nodeIntegration: false, contextIsolation: true,
        backgroundThrottling: false,
      },
    });
    mainWindowState.manage(this.win);
    this.win.on('resize', () => this.windowStateChangeHandler(this.win));
    this.win.on('move', () => this.windowStateChangeHandler(this.win));
  }

  private windowStateChangeHandler(win: BrowserWindow) {
    global.clearTimeout(this.windowStateChangeTimer);
    this.windowStateChangeTimer = global.setTimeout(() => this.updateWindowState(win), 100);
  }
}
```

### 1.3 IPC 通信模式

**AFFiNE — 命名空间 + 订阅模式**

```typescript
ipcMain.handle(AFFINE_API_CHANNEL_NAME, async (e, ...args) => {
  if (!checkSource(e)) return;
  const channel = args[0] as string;
  const [namespace, key] = channel.split(':');
  const handler = allHandlers[namespace]?.[key];
  return await handler(e, ...args.slice(1));
});

const allHandlers = {
  debug: debugHandlers, ui: uiHandlers, clipboard: clipboardHandlers,
  updater: updaterHandlers, configStorage: configStorageHandlers, auth: authHandlers,
};

// 事件订阅
ipcMain.on(AFFINE_EVENT_SUBSCRIBE_CHANNEL_NAME, (event, action, channel) => {
  if (action === 'subscribe') addSubscription(event.sender, channel);
  else removeSubscription(event.sender, channel);
});
```

**Toonflow — 自定义协议替代 IPC**

```typescript
protocol.handle("toonflow", (request) => {
  const pathname = url.hostname.toLowerCase();
  const handlers = {
    getappurl: () => ({ url: process.env.URL }),
    windowminimize: () => { mainWindow?.minimize(); return { ok: true }; },
    windowclose: () => { app.exit(0); return { ok: true }; },
    openurlwithbrowser: () => {
      const targetUrl = url.searchParams.get("url");
      if (targetUrl) require("electron").shell.openExternal(targetUrl);
      return { ok: true };
    },
    getlocallanguage: () => {
      if (process.platform === "darwin") {
        return { ok: true, local: systemPreferences.getUserDefault("AppleLocale", "string") };
      }
      return { ok: true, local: app.getLocale() };
    },
  };
  const handler = handlers[pathname];
  return new Response(JSON.stringify(handler ? handler() : { error: "未知接口" }), {
    headers: { "Content-Type": "application/json" },
  });
});
```

### 1.4 自动更新

**AFFiNE**

```typescript
autoUpdater.autoDownload = false;
autoUpdater.allowPrerelease = buildType !== 'stable';

autoUpdater.on('update-available', info => {
  if (config.autoDownloadUpdate) downloadUpdate();
  updaterSubjects.updateAvailable$.next({ version: info.version });
});

// 窗口获得焦点时检查更新（30分钟冷却）
let lastCheckTime = 0;
app.on('browser-window-focus', () => {
  if (config.autoCheckUpdate && lastCheckTime + 1800000 < Date.now()) {
    lastCheckTime = Date.now();
    checkForUpdates();
  }
});
```

**Bitwarden — 非阻塞通知 + 7天强制弹窗**

```typescript
private async promptRestartUpdate(info, blocking: boolean) {
  const longTimeSinceInitialNotification =
    this.initialUpdateNotificationTime != null &&
    Date.now() - this.initialUpdateNotificationTime > 7 * 24 * 60 * 60 * 1000;

  if (!blocking && Notification.isSupported() && !longTimeSinceInitialNotification) {
    const notification = new Notification({
      title: "需要重启以更新", body: `版本 ${info.version} 已下载完成`,
    });
    notification.on("click", () => this.promptRestartUpdate(info, true));
    notification.show();
  } else {
    const result = await dialog.showMessageBox(this.windowMain.win, {
      type: "info", message: "需要重启以更新", buttons: ["重启", "稍后"],
    });
    if (result.response === 0) autoUpdater.quitAndInstall(true, true);
  }
}
```

### 1.5 系统托盘

**Bitwarden — 关闭行为 + Dock 管理**

```typescript
setupWindowListeners(win: BrowserWindow) {
  win.on('close', async (e: Event) => {
    if (this.windowMain.isQuitting) return;
    if (await firstValueFrom(this.desktopSettingsService.runInBackground$)) {
      e.preventDefault();
      this.hideToTray();
    } else {
      this.windowMain.isQuitting = true;
    }
  });
}

hideToTray() {
  this.showTray();
  this.windowMain.win.hide();
  if (this.isDarwin()) this.hideDock();
}

async restoreFromTray() {
  if (this.windowMain.win == null) {
    await this.windowMain.createWindow();
  } else {
    this.windowMain.win.restore();
    this.windowMain.win.focus();
  }
  if (this.isDarwin()) this.showDock();
}
```

---

## 二、安全最佳实践

### 2.1 WebPreferences 安全配置

```typescript
// AFFiNE
const DEFAULT_WEB_PREFERENCES = {
  sandbox: true, contextIsolation: true, nodeIntegration: false,
};
export function buildWebPreferences(overrides = {}): WebPreferences {
  return { ...DEFAULT_WEB_PREFERENCES, ...overrides };
}

// Bitwarden
webPreferences: {
  preload: path.join(__dirname, "preload.js"),
  nodeIntegration: false,
  contextIsolation: true,
  backgroundThrottling: false,
  session: this.session,
  devTools: isDev(),
}
```

### 2.2 安全限制注册

```typescript
// AFFiNE — 导航限制 + 窗口创建限制
app.on('web-contents-created', (_, contents) => {
  contents.on('will-navigate', (event, url) => {
    if (!isInternalUrl(url)) { event.preventDefault(); openExternalSafely(url); }
  });
  contents.setWindowOpenHandler(({ url }) => {
    if (!isInternalUrl(url)) openExternalSafely(url);
    return { action: 'deny' };
  });
});
```

### 2.3 Token 加密存储

```typescript
// AFFiNE — safeStorage 加密
import { safeStorage } from 'electron';

function encryptToken(record: TokenRecord) {
  if (!safeStorage.isEncryptionAvailable()) {
    memoryTokenStore[normalizedEndpoint] = token;
    return false;
  }
  const store = readStore();
  store[normalizedEndpoint] = safeStorage.encryptString(JSON.stringify(record)).toString('base64');
  writeStore(store);
  return true;
}

function decryptToken(value: string): TokenRecord | null {
  if (!safeStorage.isEncryptionAvailable()) return null;
  return JSON.parse(safeStorage.decryptString(Buffer.from(value, 'base64')));
}
```

### 2.4 CSP 和协议安全

```typescript
// AFFiNE — 自定义协议 + CORS
protocol.registerSchemesAsPrivileged([{
  scheme: 'assets',
  privileges: { secure: true, corsEnabled: true, supportFetchAPI: true, standard: true },
}]);

// Bitwarden — 自定义文件协议替代 file://
const customFileScheme = "bw-desktop-file";
protocol.registerSchemesAsPrivileged([{
  scheme: customFileScheme,
  privileges: { standard: true, secure: true, supportFetchAPI: true },
}]);
```

---

## 三、性能优化

### 3.1 启动优化

```typescript
// Toonflow
app.commandLine.appendSwitch("disable-gpu-shader-disk-cache");
app.commandLine.appendSwitch("disable-features", "CalculateNativeWinOcclusion");

// AFFiNE
app.commandLine.appendSwitch('disable-features', 'CalculateNativeWinOcclusion,AutofillServerCommunication');
app.commandLine.appendSwitch('enable-features', 'EarlyEstablishGpuChannel,EstablishGpuChannelAsync');
app.commandLine.appendSwitch('force-color-profile', 'srgb');
```

### 3.2 内存管理

```typescript
// Bitwarden — 渲染进程强制崩溃重启
ipcMain.on("reload-process", async () => {
  if (this.isReloading) return;
  this.isReloading = true;
  try {
    const crashEvent = once(this.win.webContents, "render-process-gone");
    this.win.webContents.forcefullyCrashRenderer();
    await crashEvent;
    await new Promise(resolve => setImmediate(resolve));
    this.win.webContents.reloadIgnoringCache();
    await this.session.clearCache();
  } finally {
    this.isReloading = false;
  }
});
```

### 3.3 硬件加速智能控制

```typescript
// Bitwarden
private async toggleHardwareAcceleration() {
  const hardwareAcceleration = await firstValueFrom(this.desktopSettingsService.hardwareAcceleration$);
  if (!hardwareAcceleration || process.env.ELECTRON_DISABLE_GPU) {
    app.disableHardwareAcceleration();
  } else if (isMacAppStore()) {
    const gpuInfo = await app.getGPUInfo("basic");
    if (gpuInfo?.machineModelName == "iMac" && gpuInfo?.auxAttributes?.amdSwitchable) {
      app.disableHardwareAcceleration();
    }
  }
}
```

---

## 四、打包配置模板

```yaml
# electron-builder.yml
appId: com.multipublish.app
productName: Multi-Publish
directories:
  output: dist
  buildResources: build
files:
  - dist/**/*
  - "!node_modules/**/*.{md,ts,map}"
  - "!**/*.d.ts"
asar: true
asarUnpack:
  - "**/node_modules/sharp/**"
  - "**/node_modules/@img/**"
win:
  target: [nsis, portable]
  icon: ./build/icon.ico
nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
mac:
  target: [dmg, zip]
  icon: ./build/icon.icns
  hardenedRuntime: true
linux:
  target: [AppImage, deb]
  icon: ./build/icon.png
protocols:
  - name: Multi-Publish
    schemes: ["multipublish"]
publish:
  provider: generic
  url: "https://your-update-server.com/releases"
```

---

## 五、可复用代码清单

| 优先级 | 来源 | 代码片段 | 复用场景 |
|--------|------|---------|---------|
| P0 | AFFiNE | `buildWebPreferences()` | 安全 WebPreferences |
| P0 | AFFiNE | `checkSource()` + 导航限制 | 安全限制 |
| P0 | Bitwarden | 窗口状态持久化 + 防抖 | 窗口管理 |
| P0 | Toonflow | `protocol.handle()` 替代 IPC | 前后端通信 |
| P1 | AFFiNE | `safeStorage` Token 加密 | Token 存储 |
| P1 | Bitwarden | 系统托盘 + Dock 管理 | 托盘功能 |
| P1 | Bitwarden | 更新通知 + 7天强制弹窗 | 自动更新 |
| P2 | AFFiNE | 链式初始化模式 | 启动流程 |
| P2 | Bitwarden | 渲染进程崩溃重启 | 内存管理 |
| P2 | Toonflow | Express 混合启动 | 后端集成 |

---

*报告生成时间：2026-06-29*
