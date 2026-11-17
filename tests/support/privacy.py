import re
import json

SENSITIVE = re.compile(r"token|secret|password|credential|cookie|authorization|cdk|chat_id|private|webhook|proxy|push_json|push_serverchan|push_feishu|push_wecom|push_telegram_api|(?:^|_)key(?:$|_)", re.I)


def _strings(value):
    if isinstance(value, str):
        return [value] if len(value) >= 4 else []
    if isinstance(value, dict):
        return [s for item in value.values() for s in _strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in _strings(item)]
    return []


def secrets_in(value):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if SENSITIVE.search(str(key)):
                found.extend(_strings(item))
                if isinstance(item, str):
                    try:
                        found.extend(_strings(json.loads(item)))
                    except (ValueError, TypeError):
                        pass
            found.extend(secrets_in(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(secrets_in(item))
    return found


def redact(value, secrets=()):
    if isinstance(value, dict):
        return {str(k): "[REDACTED]" if SENSITIVE.search(str(k)) else redact(v, secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, secrets) for v in value]
    if isinstance(value, str):
        for secret in sorted(set(secrets), key=len, reverse=True):
            value = value.replace(secret, "[REDACTED]")
        value = re.sub(r"(?i)(bot)[0-9]+:[A-Za-z0-9_-]+", r"\1[REDACTED]", value)
        return re.sub(r"(?i)((?:token|password|secret|authorization|cdk)[\"']?\s*[:=]\s*[\"']?)[^\s\"'&,}]+", r"\1[REDACTED]", value)
    return value
