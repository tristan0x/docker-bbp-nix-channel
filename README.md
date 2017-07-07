# Docker Nginx BBP NIX Channel

This repository is used by the following Docker Hub 
[automated build repository](https://hub.docker.com/r/tristan0x/bbp-nix-channel).

It constructs a Docker image providing:

* a NIX channel of Blue Brain Project packages over a NGINX web server
* a background process that keep the published channel synchronized when the GitHub repository
  hosting the [BBP NIX expressions](https://github.com/BlueBrain/bbp-nixpkgs) is updated.

# Usage

```
docker run -d -p 80:80 tristan0x/bbp-nix-channel
```

Then you can visit the channel at: http://localhost

# Register the NIX channel

Once the container is started:

```
nix-channel --add http://localhost/channels/bbp-nixpkgs-unstable
nix-channel --update
```

# Workaround

## EPFL Linux workstation

NIX won't be able to fetch BBP source code on EPFL Linux workstations because of an authentication issue. A workaround is to provide Nix the required shared library with the following commands:

```
mkdir -p /nix/var/nix/ext/nss/lib
ln -s /lib/x86_64-linux-gnu/libnss_sss.so.2 /nix/var/nix/ext/nss/lib/
```

Then add this following line in your `~/.profile`:

```
export NSS_LIB_PATH=/nix/var/nix/ext/nss/lib
```

# LICENSE

MIT License. See [LICENSE](./LICENSE) file for more information
