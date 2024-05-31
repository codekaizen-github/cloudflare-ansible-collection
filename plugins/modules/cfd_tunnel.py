#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
from typing import List, Optional
import traceback
from ..module_utils.test import test_func
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

# https://developers.cloudflare.com/api/operations/cloudflare-tunnel-list-cloudflare-tunnels
# https://developers.cloudflare.com/api/operations/cloudflare-tunnel-create-a-cloudflare-tunnel

DOCUMENTATION = '''
---
module: cfd_tunnel
short_description: Manage Cloudflare Tunnel
version_added: 0.0.1
description:
  - Manages Cloudflare Tunnel
extends_documentation_fragment:
  - code_kaizen.cloudflare.attributes
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  api_token:
    description:
    - The Cloudflare API token.
    details:
      - See: https://developers.cloudflare.com/fundamentals/api/get-started/create-token/
    type: str
    required: true
    version_added: "0.0.1"
  account_id:
    description:
    - ID of the Cloudflare account.
    type: str
    required: true
    version_added: "0.0.1"
  name:
    description:
    - A user-friendly name for a tunnel.
    type: str
    required: true
    version_added: "0.0.1"
    examples:
      - blog
  config_src:
    description:
      - Indicates if this is a locally or remotely configured tunnel.
    details:
      - If local, manage the tunnel using a YAML file on the origin machine.
      - If cloudflare, manage the tunnel on the Zero Trust dashboard or using the Cloudflare Tunnel configuration endpoint.
    type: str
    required: false
    choices: [ local, cloudflare ]
    default: local
    version_added: "0.0.1"
    examples:
      - local
  tunnel_secret:
    description:
      - Sets the password required to run a locally-managed tunnel. Must be at least 32 bytes and encoded as a base64 string.
    type: str
    required: false
    version_added: "0.0.1"
    examples:
      - "AQIDBAUGBwgBAgMEBQYHCAECAwQFBgcIAQIDBAUGBwg="
  state:
    description:
    - Whether the tunnel should exist or not.
    details:
      - If present, the tunnel will be created if it does not exist or updated if it does.
      - If absent, the tunnel will be deleted.
      - If fetched, the tunnel will be fetched.
    type: str
    required: false
    choices: [ absent, present, fetched ]
    default: present
    version_added: "0.0.1"
requirements:
- requests>=2.22.0
author:
- Andrew Dawes (@andrewjdawes)
notes:
- N/A
seealso:
- name: Cloudflare Tunnels API reference
  description: Complete reference of the Cloudflare Tunnels API.
  link: https://developers.cloudflare.com/api/operations/cloudflare-tunnel-create-a-cloudflare-tunnel
'''

EXAMPLES = '''
- name: Add or update a Cloudflare Tunnel
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
'''

RETURN = '''
variable:
  description: A list of Cloudflare Tunnels as JSON. See U(https://developers.cloudflare.com/api/operations/cloudflare-tunnel-list-cloudflare-tunnels).
  returned: success and O(state=present)
  type: list
'''


GITHUB_IMP_ERR = None
try:
    from github import GithubException
    from github.Repository import Repository
    from github.Variable import Variable
    from github.GithubException import UnknownObjectException
    HAS_GITHUB_PACKAGE = True
except Exception:
    GITHUB_IMP_ERR = traceback.format_exc()
    HAS_GITHUB_PACKAGE = False


def testing():
    return test_func()

def fetch(repo: Repository, variable_name: Optional[str] = None):

    results = dict(
        changed=False,
        variables=[]
    )
    instances: List[Variable] = []
    try:
        existing_instances = github_repo_environment.get_variables(repo=repo)
        print('Looping through instances')
        for instance in existing_instances:
            if variable_name is not None and instance.name != variable_name:
                continue
            instances.append(instance)
    except UnknownObjectException:
        pass
    print(f'Getting raw data')
    results['variables'] = [k.raw_data for k in instances]
    return results


def create(repo: Repository, variable_name: str, variable_value: Optional[str], check_mode: bool = False):
    results = dict(
        changed=False,
        variables=[]
    )
    instance: Variable | None
    raw_data: dict | None = None
    try:
        instance = github_repo_environment.get_variable(
            repo, variable_name=variable_name)
        # TODO: Evaluate whether this is still necessary. "Must access the getter to trigger the network request"
        raw_data = instance.raw_data
    except UnknownObjectException:
        instance = None
    if instance is None:
        results['changed'] = True
        if not check_mode:
            instance = github_repo_environment.create_variable(repo=repo,
                                                               variable_name=variable_name, value=variable_value)
            raw_data = instance.raw_data
    else:
        if instance.value != variable_value:
            results['changed'] = True
            if not check_mode:
                instance.edit(value=variable_value)
                # Update is required to get the new values in raw_data
                instance.update()
                raw_data = instance.raw_data
    results['variables'] = [raw_data] if raw_data is not None else []
    return results


def delete(repo: Repository, variable_name: str, check_mode: bool = False):
    results = dict(
        changed=False,
        variables=[]
    )
    raw_data = []
    try:
        instance = github_repo_environment.get_variable(
            repo=repo, variable_name=variable_name)
        raw_data.append(instance.raw_data)
        # Delay setting to True in case there is an exception fetching instance
        results['changed'] = True
        if not check_mode:
            instance.delete()
    except UnknownObjectException:
        pass
    results['variables'] = raw_data
    return results


def run_module(params: dict, check_mode: bool = False):
    results = dict(
        changed=False,
        variables=[],
    )
    gh = authenticate(
        username=params['username'], password=params['password'], access_token=params['access_token'],
        api_url=params['api_url'])
    target = get_target(gh=gh, organization=params['organization'])
    repo = target.get_repo(params['name'])
    # Uppercase variable name for accurate comparison (GitHub will uppercase) - leave as None if not set
    variable_name: str | None = params.get('variable_name', None)
    if variable_name is not None:
        variable_name = variable_name.upper()
    if params['state'] == 'present':
        results = create(
            repo, variable_name, params['variable_value'], check_mode)
    elif params['state'] == 'absent':
        results = delete(repo, variable_name, check_mode)
    elif params['state'] == 'fetched':
        results = fetch(repo, variable_name)
    else:
        raise Exception("Invalid state")
    return results


def main():
    module_args = dict(
        api_url=dict(type='str', required=False,
                     default='https://api.github.com'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        access_token=dict(type='str', no_log=True),
        organization=dict(
            type='str', required=False, default=None),
        name=dict(type='str', required=True),
        variable_name=dict(type='str', required=False),
        variable_value=dict(type='str', required=False),
        state=dict(type='str', choices=[
                   'present', 'absent', 'fetched'], default='present'),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_together=[('username', 'password')],
        required_one_of=[('username', 'access_token')],
        mutually_exclusive=[('username', 'access_token')]
    )

    if not HAS_GITHUB_PACKAGE:
        module.fail_json(msg=missing_required_lib(
            "PyGithub"), exception=GITHUB_IMP_ERR)

    if module.params['state'] == 'present' and module.params['variable_name'] is None:
        module.fail_json(
            msg='When state is "present", variable_name parameter is required')
    if module.params['state'] == 'absent' and module.params['variable_name'] is None:
        module.fail_json(
            msg='When state is "absent", variable_name parameter is required')

    try:
        result = run_module(module.params, module.check_mode)
        module.exit_json(**result)
    except GithubException as e:
        module.fail_json(msg="Github error. {0}".format(repr(e)))
    except Exception as e:
        module.fail_json(msg="Unexpected error. {0}".format(repr(e)))


if __name__ == '__main__':
    main()
