#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests

from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = """
---
module: cfd_tunnel
short_description: Manage Cloudflare Tunnel
version_added: 0.0.1
description:
  - Manages Cloudflare Tunnel
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  api_token:
    description:
    - The Cloudflare API token.
    type: str
    required: true
  account_id:
    description:
    - ID of the Cloudflare account.
    type: str
    required: true
  name:
    description:
    - A user-friendly name for a tunnel.
    type: str
    required: true
  config_src:
    description:
      - Indicates if this is a locally or remotely configured tunnel.
    type: str
    required: false
    choices: [ local, cloudflare ]
    default: local
  tunnel_secret:
    description:
      - Sets the password required to run a locally-managed tunnel.
    type: str
    required: false
  state:
    description:
    - Whether the tunnel should exist or not.
    type: str
    required: false
    choices: [ absent, present, fetched ]
    default: present
requirements:
- requests>=2.22.0
author:
- Andrew Dawes (@andrewjdawes)
- Kaitlyn Wyland (kwyland22)
"""

EXAMPLES = """
- name: Create a Cloudflare Tunnel
  code_kaizen.cloudflare.cfd_tunnel:
    api_token: mytoken
    account_id: 12345
    name: my-tunnel
    config_src: cloudflare
    tunnel_secret: "AQIDBAUGBwgBAgMEBQYHCAECAwQFBgcIAQIDBAUGBwg="
    state: present
  register: results

- name: Delete a Cloudflare Tunnel
  code_kaizen.cloudflare.cfd_tunnel:
    api_token: mytoken
    account_id: 12345
    name: my-tunnel
    state: absent
  register: results

- name: Fetch a Cloudflare Tunnel
  code_kaizen.cloudflare.cfd_tunnel:
    api_token: mytoken
    account_id: 12345
    name: my-tunnel
    state: fetched
  register: results
"""

RETURN = """
variable:
  description: A list of Cloudflare Tunnels as JSON.
  returned: success
  type: list
"""

CF_API_BASE = "https://api.cloudflare.com/client/v4/accounts"


def fetch_tunnel(module, api_token, account_id, name):
    """Fetches a tunnel by name, handling pagination."""
    url = f"{CF_API_BASE}/{account_id}/tunnels"
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {"page": 1, "per_page": 50}

    try:
        while True:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            tunnels = response.json().get("result", [])

            # Check if the desired tunnel exists on this page
            for tunnel in tunnels:
                if tunnel["name"] == name:
                    module.exit_json(changed=False, tunnel=tunnel)

            # Check if there are more pages
            pagination = response.json().get("result_info", {})
            if pagination.get("page") >= pagination.get("total_pages", 1):
                break  # No more pages to fetch

            # Move to the next page
            params["page"] += 1

        module.fail_json(msg="Tunnel not found.")

    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Error fetching tunnel: {str(e)}")


def create_tunnel(
    module,
    api_token,
    account_id,
    name,
    config_src,
    tunnel_secret,
):
    """Creates a new Cloudflare Tunnel."""
    url = f"{CF_API_BASE}/{account_id}/tunnels"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    data = {
        "name": name,
        "config_src": config_src,
    }

    if tunnel_secret:
        data["secret"] = tunnel_secret

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        module.exit_json(changed=True, tunnel=response.json().get("result"))

    except requests.exceptions.HTTPError as e:
        module.fail_json(
            msg=(f"HTTP Error: {e.response.status_code} - " f"{e.response.text}"),
        )
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Error creating tunnel: {str(e)}")


def delete_tunnel(module, api_token, account_id, name):
    """Deletes a tunnel by name, handling pagination."""
    url = f"{CF_API_BASE}/{account_id}/tunnels"
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {"page": 1, "per_page": 50}

    try:
        while True:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            tunnels = response.json().get("result", [])

            # Check if the desired tunnel exists on this page
            for tunnel in tunnels:
                if tunnel["name"] == name:
                    tunnel_id = tunnel["id"]
                    delete_url = f"{url}/{tunnel_id}"
                    delete_response = requests.delete(
                        delete_url,
                        headers=headers,
                    )

                    delete_response.raise_for_status()
                    module.exit_json(changed=True, msg="Tunnel deleted")

            # Check if there are more pages
            pagination = response.json().get("result_info", {})
            if pagination.get("page") >= pagination.get("total_pages", 1):
                break  # No more pages to fetch

            # Move to the next page
            params["page"] += 1

        module.exit_json(changed=False, msg="Tunnel does not exist.")

    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Error deleting tunnel: {str(e)}")


def main():
    module_args = dict(
        api_token=dict(type="str", required=True, no_log=True),
        account_id=dict(type="str", required=True),
        name=dict(type="str", required=True),
        config_src=dict(
            type="str",
            default="local",
            choices=["local", "cloudflare"],
        ),
        tunnel_secret=dict(type="str", required=False, no_log=True),
        state=dict(
            type="str",
            default="present",
            choices=["absent", "present", "fetched"],
        ),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    api_token = module.params["api_token"]
    account_id = module.params["account_id"]
    name = module.params["name"]
    config_src = module.params["config_src"]
    tunnel_secret = module.params.get("tunnel_secret")
    state = module.params["state"]

    if state == "fetched":
        fetch_tunnel(module, api_token, account_id, name)
    elif state == "present":
        create_tunnel(
            module,
            api_token,
            account_id,
            name,
            config_src,
            tunnel_secret,
        )
    elif state == "absent":
        delete_tunnel(module, api_token, account_id, name)


if __name__ == "__main__":
    main()
