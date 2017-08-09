# Docker Nginx BBP NIX Channel

This repository is used by the following Docker Hub 
[automated build repository](https://hub.docker.com/r/tristan0x/bbp-nix-channel).

It constructs a Docker image providing:

* a NIX channel of Blue Brain Project packages over a NGINX web server
* a background process that keep the published channel synchronized when the GitHub repository
  hosting the [BBP NIX expressions](https://github.com/BlueBrain/bbp-pkgs) is updated.

# Usage

## Start the container

```
docker run -d -p 80:80 tristan0x/bbp-nix-channel
```

Then you can visit the channel at: http://localhost

## Configure your NIX environment to use this channel

### One timer

```
nix-channel --add http://localhost/channels/bbp-pkgs-unstable
nix-channel --update
```

### Add the following line to ~/.profile

```shell
# setup SSH for gerrit access
if [[ "${NIX_PATH}"  != *"ssh-config-file"* ]]; then
        export NIX_PATH="ssh-config-file=$HOME/.ssh/config:$NIX_PATH"
fi
# setup SSH agent forwarding
if [[ "${SSH_AUTH_SOCK}x" != "x" ]]; then
        export NIX_PATH="ssh-auth-sock=${SSH_AUTH_SOCK}:${NIX_PATH}"
fi

export NIX_PATH="bbp=$HOME/.nix-defexpr/channels/bbp-pkgs:${NIX_PATH}"
```

# Register the NIX channel

Once the container is started:

```
nix-channel --add http://localhost/channels/bbp-pkgs-unstable
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

# Swift synchronization

This Docker image is also able to synchronize a Swift object store with the NIX expressions GitHub
repository. To do so, you have to write `swift.env` text file with the following environment variables
and pass the file to Docker when starting the container:

```
SWIFT_SYNC=on
OS_AUTH_URL=https://bbpopenstack.epfl.ch:5000/v3
OS_IDENTITY_API_VERSION=3
OS_INTERFACE=public
OS_USERNAME=YOUR-USERNAME
OS_PASSWORD=**********
OS_PROJECT_ID=7b31f31637944288b319cd6fa00a5701
OS_PROJECT_NAME=bbp-ou-hpc
OS_REGION_NAME=geneva
OS_USER_DOMAIN_NAME=bbp
```

docker run -d -p 80:80 --env-file=swift.env tristan0x/bbp-nix-channel

# LICENSE

MIT License. See [LICENSE](./LICENSE) file for more information
