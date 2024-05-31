# FROM ghcr.io/codekaizen-github/cloudflare-ansible-collection:latest
FROM test

# https://www.reddit.com/r/ansible/comments/1bke62w/ansiblenavigator_install_error/
RUN apt-get update && apt-get install -y \
    git \
    libonig-dev

# https://ansible.readthedocs.io/projects/dev-tools/#included-packages
# https://ansible.readthedocs.io/projects/dev-tools/installation/
RUN pip install ansible-dev-tools
