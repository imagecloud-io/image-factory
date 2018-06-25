FROM imagecloudio/plant:2018.06.22

LABEL Description="This image is used to build the image factory with code"

ADD .git           /opt/factory/repo/.git
ADD include        /opt/factory/repo/include
ADD inventories    /opt/factory/repo/inventories
ADD library        /opt/factory/repo/library
ADD playbooks      /opt/factory/repo/playbooks
ADD plugins        /opt/factory/repo/plugins
ADD roles          /opt/factory/repo/roles
ADD ansible.cfg    /opt/factory/repo/ansible.cfg
