"""Minimal compute entrypoint: JSON context + JSON inputs -> JSON output."""


def run(context, inputs):
    settings = context.get("settings", {})
    prefix = settings.get("prefix", "BAAS")
    uppercase = settings.get("uppercase", False)
    note = inputs["note"]
    text = f"{prefix}\n{note}" if prefix else note
    if uppercase:
        text = text.upper()
    return {"text": text, "characters": len(text), "lines": len(text.splitlines())}
