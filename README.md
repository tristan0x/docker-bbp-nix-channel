# Docker Nginx BBP NIX Channel

This repository is used by the following Docker Hub 
[automated build repository](https://hub.docker.com/r/tristan0x/bbp-nix-channel).

It constructs a Docker image providing:

* a NIX channel of Blue Brain Project packages over a NGINX web server
* a background process that keep the published channel synchronized when the GitHub repository
  hosting the [BBP NIX expressions](https://github.com/BlueBrain/bbp-nixpkgs) is updated.

# Usage

```
docker run -p 8080:80 tristan0x/bbp_nix_channel
```

Then you can visit the channel at: http://localhost:8080

# LICENSE

MIT License. See [LICENSE](./LICENSE) file for more information
