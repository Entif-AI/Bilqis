"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const {
  SECURITY_PREFERENCES,
  createMissionControlWindow,
  createSecureWindowOptions,
  hardenWebContents,
  securityDiagnostic,
} = require("../../shell/window-security.cjs");
const {
  RENDERER_ENTRY_URL,
  RENDERER_SCHEME,
  registerRendererSchemePrivileges,
} = require("../../shell/renderer-location.cjs");

function webContentsFixture() {
  const handlers = new Map();
  let windowOpenHandler;
  let permissionRequest;
  let permissionCheck;
  return {
    handlers,
    session: {
      setPermissionRequestHandler(handler) {
        permissionRequest = handler;
      },
      setPermissionCheckHandler(handler) {
        permissionCheck = handler;
      },
    },
    on(name, handler) {
      handlers.set(name, handler);
    },
    setWindowOpenHandler(handler) {
      windowOpenHandler = handler;
    },
    get windowOpenHandler() {
      return windowOpenHandler;
    },
    get permissionRequest() {
      return permissionRequest;
    },
    get permissionCheck() {
      return permissionCheck;
    },
  };
}

test("security preferences override attempts to weaken the renderer boundary", () => {
  const options = createSecureWindowOptions("/app/preload.cjs", {
    width: 1200,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      sandbox: false,
      webviewTag: true,
      allowRunningInsecureContent: true,
    },
  });

  assert.equal(options.width, 1200);
  assert.equal(options.webPreferences.preload, "/app/preload.cjs");
  for (const [key, expected] of Object.entries(SECURITY_PREFERENCES)) {
    assert.equal(options.webPreferences[key], expected, key);
  }
  assert.deepEqual(securityDiagnostic(options), {
    schemaVersion: "bamf.gui20.security-diagnostic/v1",
    checks: {
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: true,
      nodeIntegrationInWorker: true,
      nodeIntegrationInSubFrames: true,
      webviewTag: true,
      webSecurity: true,
      allowRunningInsecureContent: true,
      preload: true,
    },
    passed: true,
  });
});

test("navigation, new windows, webviews and permissions fail closed", () => {
  const contents = webContentsFixture();
  hardenWebContents(contents);

  let prevented = false;
  contents.handlers.get("will-navigate")(
    { preventDefault() { prevented = true; } },
    "https://evil.example/phish",
  );
  assert.equal(prevented, true);

  prevented = false;
  contents.handlers.get("will-navigate")(
    { preventDefault() { prevented = true; } },
    `${RENDERER_ENTRY_URL}#capability=A.ADD`,
  );
  assert.equal(prevented, false);

  let webviewPrevented = false;
  contents.handlers.get("will-attach-webview")({
    preventDefault() { webviewPrevented = true; },
  });
  assert.equal(webviewPrevented, true);
  assert.deepEqual(contents.windowOpenHandler({ url: "https://evil.example" }), { action: "deny" });

  let permission;
  contents.permissionRequest({}, "camera", (value) => { permission = value; });
  assert.equal(permission, false);
  assert.equal(contents.permissionCheck({}, "clipboard-read"), false);
});

test("window factory hardens first and requires an explicit renderer load", async () => {
  const instances = [];
  function BrowserWindow(options) {
    this.options = options;
    this.webContents = webContentsFixture();
    this.loaded = null;
    this.loadURL = (url) => { this.loaded = url; };
    instances.push(this);
  }

  const result = createMissionControlWindow({
    BrowserWindow,
    preloadPath: "/Applications/Bilqis/MissionControl/preload.cjs",
    browserWindowOptions: { show: false },
  });

  assert.equal(instances.length, 1);
  assert.equal(result.window.loaded, null);
  assert.equal(result.window.options.show, false);
  assert.equal(result.window.options.webPreferences.nodeIntegration, false);
  assert.equal(result.window.options.webPreferences.contextIsolation, true);
  assert.equal(result.window.options.webPreferences.sandbox, true);
  assert.deepEqual(
    result.window.options.webPreferences.additionalArguments,
    ["--bilqis-mission-control-mode=production"],
  );
  assert.equal(result.diagnostic.passed, true);
  await result.loadRenderer();
  assert.equal(result.window.loaded, RENDERER_ENTRY_URL);
  await result.loadRenderer("#/view/capability?kind=capability&id=B.AND");
  assert.equal(
    result.window.loaded,
    RENDERER_ENTRY_URL + "#/view/capability?kind=capability&id=B.AND",
  );
});

test("window passes explicit fixture posture to preload without weakening security", () => {
  function BrowserWindow(options) {
    this.options = options;
    this.webContents = webContentsFixture();
    this.loadURL = () => {};
  }
  const result = createMissionControlWindow({
    BrowserWindow,
    preloadPath: "/Applications/Bilqis/MissionControl/preload.cjs",
    launchMode: "fixtures",
  });
  assert.deepEqual(
    result.window.options.webPreferences.additionalArguments,
    ["--bilqis-mission-control-mode=fixtures"],
  );
  assert.equal(result.window.options.webPreferences.nodeIntegration, false);
  assert.equal(result.window.options.webPreferences.contextIsolation, true);
  assert.equal(result.window.options.webPreferences.sandbox, true);
});

test("privileged renderer scheme is secure and does not bypass CSP", () => {
  const calls = [];
  registerRendererSchemePrivileges({
    registerSchemesAsPrivileged(value) { calls.push(value); },
  });

  assert.equal(calls.length, 1);
  assert.equal(calls[0][0].scheme, RENDERER_SCHEME);
  assert.deepEqual(calls[0][0].privileges, {
    standard: true,
    secure: true,
    supportFetchAPI: true,
    codeCache: true,
  });
  assert.equal(calls[0][0].privileges.bypassCSP, undefined);
});

test("navigation rejects file, data, javascript and remote renderer documents", () => {
  const contents = webContentsFixture();
  hardenWebContents(contents);
  for (const targetUrl of [
    "file:///etc/passwd",
    "data:text/html,<script>alert(1)</script>",
    "javascript:alert(1)",
    "https://evil.example/index.html",
    "bamf-mc://other/index.html",
    "bamf-mc://app/other.html",
  ]) {
    let prevented = false;
    contents.handlers.get("will-navigate")(
      { preventDefault() { prevented = true; } },
      targetUrl,
    );
    assert.equal(prevented, true, targetUrl);
  }
});
