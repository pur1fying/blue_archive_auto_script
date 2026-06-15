from enum import Enum, auto

REPO_BRANCH = "master"
DEFAULT_UPDATE_CHANNEL = "stable"

class GetShaMethod(Enum):
    GITHUB_API = auto()
    PYGIT2 = auto()
    MIRRORC_API = auto()


CHANNEL_REPO_SHA_METHODS = {
    "stable": [
        {
            "name": "github",
            "method": GetShaMethod.GITHUB_API,
            "owner": "pur1fying",
            "repo": "blue_archive_auto_script",
            "branch": REPO_BRANCH,
            "url": "https://github.com/pur1fying/blue_archive_auto_script.git",
        },
        {
            "name": "mirrorc",
            "method": GetShaMethod.MIRRORC_API,
        },
        {
            "name": "gitee",
            "method": GetShaMethod.PYGIT2,
            "url": "https://gitee.com/pur1fy/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "gitcode",
            "method": GetShaMethod.PYGIT2,
            "url": "https://gitcode.com/m0_74686738/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "github_proxy_v4",
            "method": GetShaMethod.PYGIT2,
            "url": "https://v4.gh-proxy.org/https://github.com/pur1fying/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "github_proxy_v6",
            "method": GetShaMethod.PYGIT2,
            "url": "https://v6.gh-proxy.org/https://github.com/pur1fying/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "github_proxy_cdn",
            "method": GetShaMethod.PYGIT2,
            "url": "https://cdn.gh-proxy.org/https://github.com/pur1fying/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "gh_proxy",
            "method": GetShaMethod.PYGIT2,
            "url": "https://gh-proxy.org/https://github.com/pur1fying/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "sevencdn",
            "method": GetShaMethod.PYGIT2,
            "url": "https://gh.sevencdn.com/https://github.com/pur1fying/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "githubfast",
            "method": GetShaMethod.PYGIT2,
            "url": "https://githubfast.com/pur1fying/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "baas_cdn",
            "method": GetShaMethod.PYGIT2,
            "url": "https://baas-cdn.kiramei.workers.dev/https://github.com/pur1fying/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "tencent_c_coding",
            "method": GetShaMethod.PYGIT2,
            "url": "https://e.coding.net/g-jbio0266/baas/blue_archive_auto_script.git",
            "branch": REPO_BRANCH,
        },
    ],
    "dev": [
        {
            "name": "github",
            "method": GetShaMethod.GITHUB_API,
            "owner": "Kiramei",
            "repo": "baas-dev",
            "branch": REPO_BRANCH,
            "url": "https://github.com/Kiramei/baas-dev.git",
        },
        {
            "name": "mirrorc",
            "method": GetShaMethod.MIRRORC_API,
        },
        {
            "name": "gitee",
            "method": GetShaMethod.PYGIT2,
            "url": "https://gitee.com/kiramei/baas-dev.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "github_proxy_v4",
            "method": GetShaMethod.PYGIT2,
            "url": "https://v4.gh-proxy.org/https://github.com/Kiramei/baas-dev.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "github_proxy_v6",
            "method": GetShaMethod.PYGIT2,
            "url": "https://v6.gh-proxy.org/https://github.com/Kiramei/baas-dev.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "github_proxy_cdn",
            "method": GetShaMethod.PYGIT2,
            "url": "https://cdn.gh-proxy.org/https://github.com/Kiramei/baas-dev.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "gh_proxy",
            "method": GetShaMethod.PYGIT2,
            "url": "https://gh-proxy.org/https://github.com/Kiramei/baas-dev.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "sevencdn",
            "method": GetShaMethod.PYGIT2,
            "url": "https://gh.sevencdn.com/https://github.com/Kiramei/baas-dev.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "githubfast",
            "method": GetShaMethod.PYGIT2,
            "url": "https://githubfast.com/Kiramei/baas-dev.git",
            "branch": REPO_BRANCH,
        },
        {
            "name": "baas_cdn",
            "method": GetShaMethod.PYGIT2,
            "url": "https://baas-cdn.kiramei.workers.dev/https://github.com/Kiramei/baas-dev.git",
            "branch": REPO_BRANCH,
        },
    ],
}


def normalize_update_channel(channel):
    value = str(channel or DEFAULT_UPDATE_CHANNEL).strip().lower()
    return value if value in CHANNEL_REPO_SHA_METHODS else DEFAULT_UPDATE_CHANNEL


def get_remote_sha_methods_for_channel(channel=DEFAULT_UPDATE_CHANNEL):
    return [dict(item) for item in CHANNEL_REPO_SHA_METHODS[normalize_update_channel(channel)]]


def repo_url_for_method(method_name, channel=DEFAULT_UPDATE_CHANNEL):
    for method in get_remote_sha_methods_for_channel(channel):
        if method.get("name") == method_name and method.get("url"):
            return method["url"]
    return None


def method_for_repo_url(url):
    for methods in CHANNEL_REPO_SHA_METHODS.values():
        for method in methods:
            if method.get("url") == url:
                return method["name"]
    return None


get_remote_sha_methods = get_remote_sha_methods_for_channel(DEFAULT_UPDATE_CHANNEL)
