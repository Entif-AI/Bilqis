# Mission Control Electron security boundary

GUI20 owns the Electron security membrane. It does not own the Mission Control
views, the CP01 transport, or the CP02 BAMF records.

The renderer receives one frozen preload object, `window.bamfMissionControl`.
That object exposes connect/status, snapshot, event, dry-run, command, and receipt
operations through fixed IPC channels. It does not expose `ipcRenderer`, generic
send/invoke primitives, Node, filesystem, shell, process, run-directory, or service
credential access.

Electron main owns the service session. `ControlPlaneBridge` expects an adapter with
the following main-process methods:

- `connect() -> { session, publicStatus }`
- `disconnect(session)`
- `status(session)`
- `snapshot(session, request)`
- `dryRun(session, request)`
- `command(session, request)`
- `receipt(session, stableRef)`
- `subscribe(session, callback) -> unsubscribe`

The `session` value is opaque and never crosses into renderer state. The accepted
CP01 `ControlPlaneClient` is consumed through a private Python stdio broker owned by
Electron main. The broker emits only a sanitized service/learner health record; CP01
socket path, run path, service identity and session identity remain behind that
boundary. Electron never invokes a shell: the broker is started with fixed argv and
`shell: false`.

The GUI shell consumes the accepted canonical CP02 records and the merged
cross-runtime `assertOperatorView` consumer. GUI20 therefore does not define a
competing CP02 record grammar. CP01 now transports the accepted bounded query,
event, command-preview, command-submit, and command-inspection surfaces through
the private Python broker. The renderer still receives no socket path, run path,
service credential, command argv, or process identity. Fixture-backed views remain
explicit fixture evidence rather than command authority.

`createMissionControlWindow` forces `contextIsolation`, sandboxing, no Node
integration, no webviews, and normal web security even when caller options try to
weaken them. Production renderer loading is pinned to
`bamf-mc://app/index.html`; `file:`, `http:`, `https:`, `data:` and `javascript:`
documents are never privileged renderer locations. The real Mission Control entry
point registers the `bamf-mc` scheme before Electron readiness and serves only the
checked-in GUI01/GUI02 asset allowlist from that origin. The scheme is registered as
standard/secure without a CSP bypass. New windows, external navigation, webview
attachment, and renderer permission requests are denied.

IPC sender trust binds all three identities: the exact BrowserWindow WebContents,
its exact top frame, and the `bamf-mc://app` origin/document. Service exceptions
are mapped to GUI20-owned safe error codes before they can cross IPC. Malformed or
credential-bearing service events are dropped at the bridge and may emit only a
non-secret violation code to a main-process diagnostic hook.

The checked-in preload entrypoint is deliberately self-contained. Electron's
sandboxed preload runtime does not load arbitrary local CommonJS modules. Tests
execute the actual preload source with a `require` shim that permits only
`electron`, which catches accidental local-module imports before GUI01 packages the
desktop app.

Run the bounded security suite with:

```bash
npm run mission-control:security:test
```

The suite does not launch Electron or a learner. It does exercise a disposable CP01
service over its real Unix socket, the Node-to-Python broker, the accepted CP01
client, the CP02 `OperatorView` consumer, the actual sandboxed preload source and
the GUI01/GUI02 renderer asset protocol. The canonical leaf/premerge commands and
the hosted portable-core workflow run the Mission Control suites so CJS-only
security changes cannot bypass repository gates.
