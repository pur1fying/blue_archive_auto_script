import requests
import json
from core.utils import Logger
from core.config.generated_user_config import Config
serverchan_url = 'https://sctapi.ftqq.com/{KEY}.send'

headers = {
    "Content-type": "application/json"
}


def push(logger: Logger, config: Config, error: str = None):
    data = {}
    if error and config.push_after_error:
        data['title'] = "Baas Error"
        data['desp'] = error

    if not error and config.push_after_completion:
        data['title'] = "Baas Completed"
        data['desp'] = "all activities finished"

    if data:
        if config.push_json != '':
            push_json(logger, config.push_json, data)
        if config.push_serverchan != '':
            push_serverchan(logger, serverchan_url.format(KEY=config.push_serverchan), data)
        if config.push_feishu != '':
            push_feishu(logger, config.push_feishu, data)


def push_json(logger: Logger, url: str, data: dict):
    try:
        if requests.post(url, data=json.dumps(data), headers=headers).status_code == 200:
            logger.info("push success")
        else:
            raise Exception("push failed")
    except Exception as e:
        logger.error(e)


def push_serverchan(logger: Logger, url: str, data: dict):
    try:
        if requests.post(url, data=json.dumps(data), headers=headers).status_code == 200:
            logger.info("[ Server Chan ] push success")
        else:
            raise Exception("[ Server chan ] push failed")
    except Exception as e:
        logger.error("[ Server Chan ] push error : " + e.__str__())


def push_feishu(logger: Logger, webhook_url: str, data: dict):
    feishu_data = {
        "msg_type": "text",
        "content": {
            "text": f"{data['title']}\n{data['desp']}"
        }
    }
    try:
        resp = requests.post(
            webhook_url,
            json=feishu_data,
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 0:
                logger.info("[ Feishu ] push success")
            else:
                logger.error(f"[ Feishu ] push failed: {result.get('msg', 'unknown error')}")
        else:
            logger.error(f"[ Feishu ] push HTTP error: {resp.status_code}")
    except Exception as e:
        logger.error(f"[ Feishu ] push exception: {e.__str__()}")
