# Plugin system, API v1

The service owns plugin discovery, profile settings and jobs. Desktop, Android and WebUI use the same authenticated trigger commands and declarative interface. A plugin never supplies executable frontend JavaScript, HTML, Qt widgets or CSS. The host renders its names, schemas and results with the application's own components and theme.

The mechanisms in [upstream PR 583](https://github.com/pur1fying/blue_archive_auto_script/pull/583) informed this design. Its Qt UI and the UI changes in [PR 2](https://github.com/sakurairsora/blue_archive_auto_script/pull/2) are not part of this implementation. The old five tools are not silently imported or registered as compatible v1 extensions.

## Package and compatibility

A package contains `plugin.json` at its root and, for computation, ordinary Python source files. Bundled packages live under `service/plugins/bundled/<id>/`. User packages live under `plugins/<id>/`, outside the tracked source and outside other plugins' configuration namespaces. The client can upload a local ZIP after authentication; no pip commands, installation hooks or arbitrary download URLs are run.

`schema_version` describes the manifest format, `api_version` describes the host contract, and `version` is the plugin's own version. All three are separate. API v1 accepts schema/API integer `1`; incompatible versions are reported in the catalog. A stable, lowercase plugin ID may use namespaced dots, underscores or hyphens. IDs are never paths. Duplicate IDs cannot replace a bundled plugin or another installed plugin.

A computation entry point uses `module:function` syntax, for example `main:run`:

```python
def run(context, inputs):
    # Both arguments are plain JSON values. No service objects or auth data.
    prefix = context["settings"]["prefix"]
    return {"text": prefix + inputs["text"]}
```

The context contains `api_version`, `plugin_id`, `config_id` and the validated settings snapshot. It does not contain the login Key, session keys, core runtime, arbitrary configuration files or a device object. Return JSON-compatible values only; invalid, non-finite or excessively large output fails the job. Standard output is a worker protocol, not a UI rendering surface.

## Manifest

The required fields are `schema_version`, `api_version`, `id`, `version`, `name`, `description`, `permissions`, `settings_schema` and `actions`. Names and descriptions may be strings or locale maps such as `{"en": "Notes", "zh": "笔记"}`. Clients use the selected language, then English, then an available translation.

An action has a stable `id`, localized `name`, optional description, an `execution` kind and an `input_schema`. An optional closed `output_schema` validates its result before publication. A `compute` action declares `entrypoint: "main:run"` and the `compute` permission. It executes in a separate, terminable Python process. A `device_task` action declares a host-supported `task_name` and the `device.tasks` permission. It has no Python entry point and cannot introduce an arbitrary core function name.

Settings and action inputs use a deliberately restricted JSON Schema subset: object properties, required keys and `additionalProperties: false`; bounded arrays with an item schema; strings, booleans, numbers and integers; defaults, enums, numeric bounds, titles and descriptions. Unsupported schema keywords or versions are rejected instead of silently interpreted with different semantics. The service validates every write and run; client-side validation only improves feedback.

An optional `contributions.home` array contains `{id, title, description?, action_id}` entries. Each entry references a declared action. The host may show a shortcut for an enabled plugin; opening it does not automatically execute the action. The manifest cannot inject arbitrary UI or override an existing application route. New execution kinds, permissions, schema features and contribution types require explicit host capability negotiation before use.

## Bundled automation capability

Hosts advertising `host.automation.v1` also accept `execution: "host_automation"` for a closed list of shipped tool/action pairs. These actions require `device.tasks` and declare neither an entry point nor a task name. External ZIPs cannot request this execution mode, even by copying a bundled ID. The host dispatches its own adapter, never Python loaded from the plugin package into the device process.

`baas.auto-push` provides independent normal/hard mission lists, story episodes, activity actions and formation attributes. Its `current_stage` and `current_story` actions recognize supported screens and stop on unknown pages. Temporary task overrides are restored on success, failure and cancellation, while actual inventory updates remain persistent.

`baas.hoard-ap` provides three actions: `plan` is a pure forecast, optionally accepting a `mailbox_snapshot`; `scan_mail` reads a fresh anonymous mailbox inventory without claiming rewards or requiring a target date; `start` rescans the device and executes the plan. Both device actions use the profile's exclusive runtime ownership gate, shared with the scheduler and other device tasks. Another task receives `already-running`/`DEVICE_BUSY`; scanning is read-only but still cannot race device automation. Starting owns the profile until completion or cancellation, with a maximum seven-day deadline. Long timelines do not occupy a compute-worker slot. Backend restart requires the user to replan and start again.

Hoarding results distinguish `available_at_target` from the projected remaining `summary`, and `inventory` separates verified mail from user-entered estimates and forecast source deliveries. The timeline tracks natural recovery caps, cafe capacity, server-day resets, already purchased AP and mail deadlines. A caller-provided snapshot supports forecasting; it never authorizes a device claim. Execution reads fresh character AP and the complete mailbox, and replans from those observations. AP purchases using pyroxene remain manual: a plan containing them reports `executable: false` and `PREMIUM_PURCHASES_ARE_MANUAL`, and `start` rejects it before claiming a source.

The verified mailbox/source adapters currently support the CN landscape layout, normalized to 1280×720; an unsupported server or uncertain recognition stops execution. Mail scanning verifies the AP icon, amount, received date, anonymous identity and individual claim button, and traverses the full unclaimed list against its displayed count. Equal-amount and identical letters retain their multiplicity. Visual stabilization is bounded; a count change or cancellation stops it.

Letters are indivisible. The executor creates headroom for a whole parcel, rescans and relocates it, clicks its individual button, then verifies the exact character-AP increase and complete mailbox multiset with only that letter removed. It never uses collect-all or splits a parcel to fit AP 999. Stale locators are not reused. Clearing AP uses the configured host route and requires an observed AP decrease.

Source collection requires an observed amount and a recognized source-state receipt, followed by character-AP and full-mailbox verification. Daily collection verifies the selected daily tab and claims individual AP cards; it does not claim weekly rewards or use the global reward button. Club sign-in delivers its AP through mail and is now executable when that source receipt and new whole parcel are verified. Overflow can also be verified at AP 999: direct AP gain plus new AP-mail amounts must equal the source receipt, and unrelated or missing mail stops execution. A capped counter, an arbitrary new letter or a legacy task's boolean return alone is insufficient proof.

Expiry is an interval, not a newly granted lifetime. Parcels carry conservative `expires_at`/`expires_before` bounds and `expiry_precision` (`day`, `hour`, `minute`, `second` or `under-hour`). A first “under one hour” observation has an immediate lower bound. During an execution, matching retained parcel copies keep the earlier observed deadline across rescans; independent scans and backend restarts do not share a persistent deadline cache. Forecast overflow lifetimes do not become execution deadlines; fresh source mail is read from the game.

The closed `scan_mail` result contains `complete`, `observed_at`, `mailbox_count`, `parcels`, `total_ap`, `fingerprint` and verified `character_ap`, plus result-kind fields. Public parcels contain `id`, `amount`, expiry bounds/precision, `received_at` and `occurrence`. Compact 32-character digest locators keep all 200 letters within the 64 KiB result limit; full digests and non-AP rows remain internal. Inventory is never truncated. Bounded history reports its total, offset and truncation status. Mail titles, senders, raw OCR text and screenshots stay outside the DTO and mail-recognition logs.

Anonymous CN live verification covered one three-star normal 28-2 sweep (one attempt, AP 999→989), one selected AP10 letter (AP 989→999, mailbox 4→3 with only that letter removed), and the daily-login AP100 reward at AP 999 (mailbox 3→4, AP-mail inventory 10→110, character AP unchanged). The new letter's displayed 23-hour expiry was retained as a conservative 22–24-hour interval. No pyroxene or JJC currency was spent. These observations verify those paths rather than asserting a universal overflow policy or exact lifetime for every reward source.

String schemas may declare `format: "date-time"` as a rendering hint. The client edits local date/time and sends an ISO 8601 instant with an explicit time zone. The hoarding tool uses its separate `server_utc_offset_minutes` and `reset_hour` for game-day boundaries, so a browser sending UTC does not shift the reset time. Empty initial values remain editable; the automation adapter validates required dates, time zones and the bounded planning horizon. Other format names and nonstring formats are rejected.

## Authenticated commands

All commands use the existing `CommandMessage` envelope on the authenticated trigger channel. A successful response retains `status: "ok"` and returns the following `data`. Errors retain `status: "error"`, a stable `code` and a human-readable `error` string. There is no unauthenticated plugin HTTP endpoint.

| Command | Scope and payload | Result |
| --- | --- | --- |
| `get_plugin_catalog` | Optional `config_id` | `{api_version: 1, capabilities, plugins, errors}` |
| `get_plugin_settings` | `config_id`, `{plugin_id}` | `{plugin_id, config_id, revision, values}` |
| `update_plugin_settings` | `config_id`, `{plugin_id, revision, values}` | Updated settings and revision |
| `set_plugin_enabled` | `config_id`, `{plugin_id, enabled, trust_code?}` | Plugin descriptor |
| `run_plugin_action` | `config_id`, `{plugin_id, action_id, input, request_id}` | Job snapshot |
| `get_plugin_job` | `config_id`, `{job_id}` | Job snapshot |
| `cancel_plugin_job` | `config_id`, `{job_id}` | Job snapshot |
| `install_plugin` | Binary ZIP upload with `{binary: true, filename?}` | Installed descriptor |
| `uninstall_plugin` | `{plugin_id}` | Removal result |

A descriptor includes the manifest and `source`, `enabled`, `trusted`, `state`, and an optional structured error. The catalog can be read without selecting a profile, but still requires an authenticated connection. Profile-dependent operations require a real existing configuration ID. Old services return an unsupported-command error, which clients present as an upgrade requirement.

## Settings and lifecycle

Settings are stored in the profile's separate `plugins.json` namespace. They are not appended to `ConfigSet` attributes, global defaults, `setup.toml` or `service_auth.json`. Atomic writes and monotonically increasing revisions prevent two clients from silently overwriting each other. On `REVISION_CONFLICT`, reload and explicitly reapply edits. Invalid JSON is preserved and reported rather than overwritten with empty defaults. Copy/export/import operations preserve optional plugin settings with the profile; import clears code trust and enablement.

Catalog discovery parses bounded JSON only. Disabled external plugins are not imported. Installing an external package leaves it disabled. Enabling external Python requires an explicit `trust_code: true` decision; trust is tied to the installed package, not merely its display name. Python plugins are trusted backend code, **not a security sandbox**. A child process supplies cancellation and failure isolation; it does not revoke operating-system access to files or the network. Install only code you trust.

Jobs report `queued`, `running`, `succeeded`, `failed` or `cancelled`, with identity, timestamps, optional JSON result and a structured error. A `request_id` deduplicates retries within the service's retained job window. Polling and cancellation are profile-scoped; another profile cannot retrieve or cancel a job by guessing its ID. Completed jobs and output have bounded retention. Computations are concurrency-limited and terminate on timeout/cancel/shutdown. Device tasks use the existing profile runtime lock, initialization, logging, Android display guard and stop lifecycle. A task already running in that profile is never replaced by a plugin action.

Running jobs prevent uninstall or unsafe enable/disable changes. Uninstall removes installed code and its registration, not unrelated profiles or application credentials. Bundled plugins cannot be removed. There is no automatic plugin update or dependency installation in v1.

The initial limits are 10 MiB per uploaded ZIP, 32 MiB unpacked, 256 package files/nodes, 16 directory levels, 100 discovered packages, two concurrent workers, eight active jobs and 128 retained jobs. Inputs/settings/results are bounded JSON; results are limited to 64 KiB. Computation timeouts default to 30 seconds and may be declared from 0.1 to 120 seconds. Device tasks default to 30 minutes, with a maximum of one hour. Linux/macOS use an owned process group; Windows assigns each worker to a Job Object before it receives executable input. Cleanup is a runtime responsibility on every supported transport.

Android's embedded Chaquopy runtime uses two private native service processes instead of launching `sys.executable` or forking the JVM. They execute the same standard-library worker protocol through bounded private files. Native leases bind cancellation to a slot, random token and process identity; an old cancellation cannot stop a replacement job. Each service owns its process group, watches its backend owner and has an independent hard deadline. Worker services are not exported or automatically restarted. An older Android client reports `ANDROID_WORKER_UNAVAILABLE` and needs updating; desktop and WebUI workers keep their existing launch path.

## Included plugins

The five bundled tools use the application's own theme and components: `baas.hoard-ap` supplies forecasting, mailbox scanning and verified execution; `baas.auto-push` supplies supported mission/story automation; `baas.equipment-planner` supplies equipment planning, estimates, eleph calculations and catalog lookup; `baas.inventory-calculator` solves inventory calculations; and `baas.home-editor` stores per-profile home-section visibility and order. The home editor has no executable actions. Device automation starts only when the user explicitly runs an action; opening a shortcut or editing settings does not start it.

New solvers, policy hooks or task adapters must declare compatible APIs and capabilities. Resource operations must specify verification, failure and cancellation behavior; an uncertain receipt stops execution rather than silently continuing or replaying a potentially completed claim.
