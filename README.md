# Code_kaizen Cloudflare Collection

This repository contains the `code_kaizen.cloudflare` Ansible Collection.

## Tested with Ansible

Tested with ansible-core >=2.14 releases and the current development version of ansible-core.

## External requirements

Some modules and plugins require external libraries. Please check the requirements for each plugin or module you use in the documentation to find out which requirements are needed.

## Included content

Please check the included content on the [Ansible Galaxy page for this collection](https://galaxy.ansible.com/code_kaizen/cloudflare).

## Using this collection

```
    ansible-galaxy collection install code_kaizen.cloudflare
```

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml` using the format:

```yaml
collections:
  - name: code_kaizen.cloudflare
```

To upgrade the collection to the latest available version, run the following command:

```bash
ansible-galaxy collection install code_kaizen.cloudflare --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax where `X.Y.Z` can be any [available version](https://galaxy.ansible.com/code_kaizen/cloudflare):

```bash
ansible-galaxy collection install code_kaizen.cloudflare:==X.Y.Z
```

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing

### Running Tests

#### Integration Tests

Run all tox integration tests:

```sh
python -m tox --ansible --conf tox-ansible.ini
```

Run tox integration tests for a specific environment:

```sh
python -m tox --conf tox-ansible.ini --ansible -e sanity-py3.12-devel
```

Run tox integration tests for a specific scenario:

```sh
# Unit
python -m tox --conf tox-ansible.ini --ansible --matrix-scope unit
# Integration
python -m tox --conf tox-ansible.ini --ansible --matrix-scope integration
```

Run tox integration tests for a specific environment and a specific scenario:

```sh
# Unit
python -m tox --conf tox-ansible.ini --ansible -e sanity-py3.12-devel --matrix-scope unit
# Integratino
python -m tox --conf tox-ansible.ini --ansible -e sanity-py3.12-devel --matrix-scope integration
```


## Release notes

See the [changelog](https://github.com/ansible-collections/REPONAMEHERE/tree/main/CHANGELOG.rst).

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

<!-- List out where the user can find additional information, such as working group meeting times, slack/IRC channels, or documentation for the product this collection automates. At a minimum, link to: -->

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/devel/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/devel/dev_guide/index.html)
- [Ansible Collections Checklist](https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html)
- [The Bullhorn (the Ansible Contributor newsletter)](https://us19.campaign-archive.com/home/?u=56d874e027110e35dea0e03c1&id=d6635f5420)
- [News for Maintainers](https://github.com/ansible-collections/news-for-maintainers)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.

<!--start requires_ansible-->
<!--end requires_ansible-->

<!--start collection content-->
### Hello_world filter plugins
filter plugin.

Name | Description
--- | ---
code_kaizen.cloudflare.hello_world|Returns Hello message.

### Modules
Name | Description
--- | ---
[code_kaizen.cloudflare.cfd_tunnel](http://example.com/repository/blob/main/docs/code_kaizen.cloudflare.cfd_tunnel_module.rst)|Manage Cloudflare Tunnel

<!--end collection content-->

End
