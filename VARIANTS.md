## Image variants

### For the `Fedora.kiwi` kiwi file

| Name                           | Image type | Image profiles                   |
|--------------------------------|------------|----------------------------------|
| Base Cloud Edition for clouds  | `oem`      | `Cloud-Base-Generic`             |
|                                |            | `Cloud-Base-AmazonEC2`           |
|                                |            | `Cloud-Base-Azure`               |
|                                |            | `Cloud-Base-GCE`                 |
| Base Cloud Edition for Vagrant | `oem`      | `Cloud-Base-Vagrant-libvirt`     |
|                                |            | `Cloud-Base-Vagrant-VirtualBox`  |
| Base Container                 | `oci`      | `Container-Base-Generic-Init`    |
|                                |            | `Container-Base-Generic-Minimal` |
|                                |            | `Container-Base-Generic`         |
| Toolbox Container              | `oci`      | `Container-Toolbox`              |
| RootFS for FEX                 | `erofs`    | `FEX-RootFS`                     |
| KDE Spin                       | `iso`      | `KDE-Desktop-Live`               |
|                                | `oem`      | `KDE-Desktop-Disk`               |
| KDE Mobile Spin                | `iso`      | `KDE-Mobile-Live`                |
|                                | `oem`      | `KDE-Mobile-Disk`                |
| Workstation Edition            | `iso`      | `Workstation-Live`               |
