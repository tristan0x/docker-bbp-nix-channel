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

Then you can visit the channel at: http://localhost:8080

# Register the NIX channel

Once the container is started:

```
nix-channel --add http://localhost/channels/bbp-nixpkgs-unstable
nix-channel --update
```

# LICENSE

MIT License. See [LICENSE](./LICENSE) file for more information
