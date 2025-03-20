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
      - Must be at least 32 bytes and encoded as a base64 string.
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
- Kaitlyn Wyland (@kwyland22)
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
    """Fetches a tunnel by name and returns the tunnel data."""
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
                if tunnel["name"] == name and not tunnel.get("deleted_at"):
                    return tunnel

            # Check if there are more pages
            pagination = response.json().get("result_info", {})
            if pagination.get("page") >= pagination.get("total_pages", 1):
                break

            # Move to the next page
            params["page"] += 1

        return None

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
    # Check mode handling
    if module.check_mode:
        module.exit_json(changed=True, msg="Would have created tunnel (check mode)")

    url = f"{CF_API_BASE}/{account_id}/tunnels"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    data = {
        "name": name,
        "config_src": config_src,
        "tunnel_secret": tunnel_secret,
    }

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


def update_tunnel(module, api_token, account_id, tunnel_id, config_src, tunnel_secret):
    """Updates an existing Cloudflare Tunnel."""
    # First fetch current tunnel config
    url = f"{CF_API_BASE}/{account_id}/tunnels/{tunnel_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        current_tunnel = response.json().get("result")

        # Check if update is needed
        if current_tunnel.get("config_src", "local") == config_src and not current_tunnel.get(
            "deleted_at",
        ):
            return module.exit_json(changed=False, tunnel=current_tunnel)

        # Check mode handling
        if module.check_mode:
            return module.exit_json(changed=True, msg="Would have updated tunnel (check mode)")

        # Prepare the data to update
        data = {"config_src": config_src}
        if tunnel_secret:
            data["tunnel_secret"] = tunnel_secret

        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        return module.exit_json(changed=True, tunnel=response.json().get("result"))

    except requests.exceptions.HTTPError as e:
        module.fail_json(
            msg=(f"HTTP Error: {e.response.status_code} - " f"{e.response.text}"),
        )
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Error updating tunnel: {str(e)}")


def delete_tunnel(module, api_token, account_id, name):
    """Deletes a tunnel by name"""
    # First check if tunnel exists
    existing_tunnel = fetch_tunnel(module, api_token, account_id, name)

    # If tunnel doesn't exist, return with changed=False
    if not existing_tunnel:
        return module.exit_json(
            changed=False,
            msg="Tunnel does not exist",
        )

    # Check mode handling
    if module.check_mode:
        return module.exit_json(
            changed=True,
            msg="Would have deleted tunnel (check mode)",
        )

    # Delete the existing tunnel
    url = f"{CF_API_BASE}/{account_id}/tunnels/{existing_tunnel['id']}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()

        # After successful deletion
        return module.exit_json(
            changed=True,
            msg="Tunnel deleted",
        )

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # If we get here, the tunnel doesn't exist (which shouldn't happen since we checked)
            return module.exit_json(
                changed=False,
                msg="Tunnel does not exist",
            )
        module.fail_json(
            msg=f"HTTP Error: {e.response.status_code} - {e.response.text}",
        )
    except requests.exceptions.RequestException as e:
        module.fail_json(
            msg=f"Error deleting tunnel: {str(e)}",
        )


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
        tunnel = fetch_tunnel(module, api_token, account_id, name)
        if tunnel:
            # Tunnel found
            module.exit_json(changed=False, tunnel=tunnel)
        else:
            # Tunnel not found, fail the task
            module.fail_json(msg=f"Tunnel with name '{name}' not found.")
    elif state == "present":
        try:
            existing_tunnel = fetch_tunnel(module, api_token, account_id, name)

            if existing_tunnel:
                # Tunnel exists; update it
                update_tunnel(
                    module,
                    api_token,
                    account_id,
                    existing_tunnel["id"],
                    config_src,
                    tunnel_secret,
                )
            else:
                # Tunnel does not exist; create it
                create_tunnel(
                    module,
                    api_token,
                    account_id,
                    name,
                    config_src,
                    tunnel_secret,
                )
        except RuntimeError as e:
            module.fail_json(msg=str(e))
    elif state == "absent":
        delete_tunnel(module, api_token, account_id, name)


if __name__ == "__main__":
    main()
