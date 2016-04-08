This Ansible role is for building the filesystem image required to run the GVL.
It is likely to be used in the context of the GVL playbook.

Requirements
------------
This role is largely intended to be used in the context of the
larger [GVL playbook][gvlpb]. It must be run on a machine instance on
which the [GVL Image Role][gvlir] has already been executed.

Dependencies
------------
This role depends on several roles, as defined in meta/main.yml. To satisfy these
requirements it is necessary to install the required roles with the following
commands (this will download the given roles from Ansible Galaxy and place them in
`roles` subdirectory; unfortunately, Ansible does not have an option to have this
done automatically):

    $ ansible-galaxy install -r requirements_roles.txt -p roles

Variables
---------
##### Optional variables #####
Note that some of these variables should match equally named ones from the
[GVL playbook][gvlpb].

 - `galaxyFS_base_dir`: (default: `/mnt/galaxy`) the base path under which the
    galaxy file system is planned to be placed
 - `galaxy_user_name`: (default: `galaxy`) system username used for Galaxy
 - `galaxy_server_dir`: (default: `/mnt/galaxy/galaxy-app`) The default
    location where the Galaxy application is stored
 - `galaxy_venv_dir`: (default: `{{ galaxy_server_dir }}/.venv`) The location
    of virtual env used by Galaxy
 - `galaxy_config_file`: (default: `{{ galaxy_server_dir }}/config/galaxy.ini`)
    The location of Galaxy's main configuration file
 - `cmg_setup_files`: A list of files to be copied from this role into Galaxy's
    source tree. See `defaults/main.yml` for the defaults.
 - `cmg_extra_files`: Provides a hook to copy a list of extra, user-defined files
    into Galaxy's source tree. The default is an empty list, but should be in a
    format similar to cmg_setup_files.

##### Control-flow variables #####
Use the following control-flow variables to decide which parts of the role
you'd like to run:

 - `cm_setup_galaxy`: (default: `yes`) whether to run the Galaxy setup step

Dependencies
------------
None.

Example Playbook
----------------
To use the role, wrap it into a playbook file called `playbook.yml` as follows
(the following assumes the role has been placed into directory
`roles/galaxyprojectdotorg.cloudman-galaxy-setup`):

    - hosts: gvl-filesystem-hosts
      sudo: yes
      roles:
        - role: gvl.ansible.filesystem
          sudo_user: "{{ galaxy_user_name }}"

Next, create a `hosts` file:

    [gvl-filesystem-hosts]
    130.56.250.204 ansible_ssh_private_key_file=key.pem ansible_ssh_user=ubuntu

Finally, run the playbook as follows:

    $ ansible-playbook playbook.yml -i hosts


[gvlpb]: https://github.com/gvlproject/gvl.ansible.playbook
[gvlir]: https://github.com/gvlproject/gvl.ansible.filesystem