#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
from typing import List, Optional
import traceback
__metaclass__ = type

DOCUMENTATION = '''
---
module: repo_variable
short_description: Manage repository variables on Github
version_added: 1.0.0
description:
  - Manages Github Actions variables in repositories using PyGithub library.
  - Authentication can be done with O(access_token) or with O(username) and O(password).
extends_documentation_fragment:
  - webfx.github_api.attributes
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  api_url:
    description:
    - URL to the GitHub API if not using github.com but you own instance.
    type: str
    default: 'https://api.github.com'
    version_added: "3.5.0"
  username:
    description:
    - Username used for authentication.
    - This is only needed when not using O(access_token).
    type: str
    required: false
  password:
    description:
    - Password used for authentication.
    - This is only needed when not using O(access_token).
    type: str
    required: false
  access_token:
    description:
    - Token parameter for authentication.
    - This is only needed when not using O(username) and O(password).
    type: str
    required: false
  organization:
    description:
    - Organization for the repository.
    type: str
    required: false
  name:
    description:
    - Repository name.
    type: str
    required: true
  variable_name:
    description:
    - Name of the environment variable.
    type: str
    required: true
  variable_value:
    description:
    - Value of the environment variable.
    type: str
    required: true
  state:
    description:
    - Whether the variable should exist or not.
    type: str
    default: present
    choices: [ absent, present, fetched ]
    required: false
requirements:
- PyGithub>=1.54
notes:
- For Python 3, PyGithub>=1.54 should be used.
- "For Python 3.5, PyGithub==1.54 should be used. More information: U(https://pygithub.readthedocs.io/en/latest/changes.html#version-1-54-november-30-2020)."
- "For Python 2.7, PyGithub==1.45 should be used. More information: U(https://pygithub.readthedocs.io/en/latest/changes.html#version-1-45-december-29-2019)."
author:
- Andrew Dawes (@andrewjdawes)
'''

EXAMPLES = '''
- name: Add or update a variable
  webfx.github_api.repo_variable:
    access_token: mytoken
    organization: MyOrganization
    name: myrepo
    variable_name: MY_SUPER_VARIABLE_KEY
    variable_value: abc123
    state: present
  register: result

- name: Delete a variable
  webfx.github_api.repo_variable:
    access_token: mytoken
    organization: MyOrganization
    name: myrepo
    variable_name: MY_SUPER_VARIABLE_KEY
    state: absent
  register: result

- name: Fetch variables
  webfx.github_api.repo_variable:
    access_token: mytoken
    organization: MyOrganization
    name: myrepo
    state: fetched
  register: result

'''

RETURN = '''
variable:
  description: Variable information as JSON. See U(https://docs.github.com/en/rest/actions/variables?apiVersion=2022-11-28#create-or-update-an-organization-variable).
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