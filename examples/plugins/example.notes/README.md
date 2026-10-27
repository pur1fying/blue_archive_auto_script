# Example notes plugin

This example runs a small, useful formatter without a GUI dependency. It adds a
configured heading to a note and can turn the result into uppercase. It never
reads files, accesses the network, changes BAAS profiles or controls a device.

## Package and install

Create a ZIP whose root contains `plugin.json` and `main.py`; do not include this
README, a parent directory, virtual environment, secrets or configuration files.
For example, from this directory:

```sh
zip example.notes.zip plugin.json main.py
```

Open **Plugins** in the client, choose the ZIP and install it. External plugins
start disabled. Review the code before enabling it and explicitly confirm the
code trust prompt. A Python plugin is executable code; declared permissions are
host API capabilities, not an operating-system sandbox.

Set **Heading** to `Daily plan`, leave **Uppercase** off and run **Format note**
with `note` equal to `Collect cafe AP`. The result is:

```json
{"text":"Daily plan\nCollect cafe AP","characters":26,"lines":2}
```

Settings are stored by the host for the selected BAAS profile. The entrypoint
receives only JSON: `context` contains `api_version`, `plugin_id`, `config_id` and
`settings`; `inputs` is validated against the action schema. Return a JSON value
matching `output_schema`. Do not import `service`, `core`, Qt or application
objects. A compute worker can be terminated when its timeout expires.

For a new plugin, change the globally unique manifest ID, localized names,
settings and action schemas. Keep `schema_version` and `api_version` at `1` for
this API. Do not add install hooks or automatically install Python dependencies.
