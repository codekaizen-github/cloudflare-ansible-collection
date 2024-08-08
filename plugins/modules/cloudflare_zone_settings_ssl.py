#!/usr/bin/python

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def fetch_ssl_settings(module, api_token, zone):
    url = f"https://api.cloudflare.com/client/v4/zones?name={zone}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    response, info = fetch_url(module, url, headers=headers, method="GET")
    if info["status"] != 200:
        module.fail_json(
            msg="Failed to fetch zone information",
            details=info,
        )

    result = json.loads(response.read())
    zone_id = result["result"][0]["id"]

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/ssl"
    response, info = fetch_url(module, url, headers=headers, method="GET")
    if info["status"] != 200:
        module.fail_json(
            msg="Failed to fetch SSL settings",
            details=info,
        )

    result = json.loads(response.read())
    return result["result"]


def set_ssl_settings(module, api_token, zone, value):
    url = f"https://api.cloudflare.com/client/v4/zones?name={zone}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    response, info = fetch_url(module, url, headers=headers, method="GET")
    if info["status"] != 200:
        module.fail_json(
            msg="Failed to fetch zone information",
            details=info,
        )

    result = json.loads(response.read())
    zone_id = result["result"][0]["id"]

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/ssl"
    data = json.dumps({"value": value})
    response, info = fetch_url(
        module,
        url,
        data=data,
        headers=headers,
        method="PATCH",
    )
    if info["status"] != 200:
        module.fail_json(
            msg="Failed to set SSL settings",
            details=info,
        )

    result = json.loads(response.read())
    return result["result"]


def main():
    module = AnsibleModule(
        argument_spec=dict(
            zone=dict(type="str", required=True),
            api_token=dict(type="str", required=True, no_log=True),
            state=dict(
                type="str",
                choices=["fetched", "present"],
                required=True,
            ),
            value=dict(
                type="str",
                choices=["full", "flexible", "strict", "off"],
                required=False,
            ),
        ),
        supports_check_mode=True,
    )

    zone = module.params["zone"]
    api_token = module.params["api_token"]
    state = module.params["state"]
    value = module.params.get("value")

    if state == "fetched":
        result = fetch_ssl_settings(module, api_token, zone)
        module.exit_json(
            changed=False,
            ssl_settings=result,
            message="SSL settings fetched successfully.",
        )
    elif state == "present":
        if not value:
            module.fail_json(
                msg="Value parameter is required when state is 'present'",
            )
        result = set_ssl_settings(module, api_token, zone, value)
        module.exit_json(
            changed=True,
            ssl_settings=result,
            message="SSL settings updated successfully.",
        )


if __name__ == "__main__":
    main()
