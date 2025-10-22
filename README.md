# MinecraftPluginManager
[![Python CI](https://github.com/thehappykraken/MinecraftInstallManager/actions/workflows/python-ci.yml/badge.svg)](https://github.com/thehappykraken/MinecraftInstallManager/actions/workflows/python-ci.yml)

Python utility to query, download, and install Minecraft servers and plugins

## Features
- Search for server versions across multiple server repositories (e.g. PaperMC, Fabric, or Vanilla)
- Download Minecraft server files
- Search for plugins across multiple plugin repositories
    - Filter searches by server version compatibility
- List available plugin versions
- Download plugin files
- Define a server configuration with a JSON file. Use `mim` to install or update the configuration
    - Define the server type and version or range of versions
    - Define the required plugins. `mim` will install only compatible servers and plugins
    - `mim` will discover existing server and plugin files and clean up old versions upon install

## Installation
`pip install thehappykraken/minecraft-install-manager`

## Usage
Use `mim --help` to view the help documentation

### YAML Format
```
# loader - The name of the plugin loader such as paper, fabric, or vanilla
loader: "plugin loader"

# server - The plugin loader version such as 1.20.1
# x may be used to indicate a don't care value. e.g. 1.x.x or 1.20.x
server: "1.x.x"

# plugins - A list of plugins
plugins:
    # name - The name of the plugin. For Modrinth, this must match the plugin name in Modrinth
    # version - The plugin version. If omitted, the highest version which meets compatibility
    #           requirements will be used. If included, compatibility requirements are evaluated
    #           but not enforced
    # id - Repository ID to identify the plugin.
    #      For Spiget, this is the resource ID. e.g. 101066
    #      For GitHub, this is the repository name. e.g. MyOwner/MyRepository
    # assets - A list of asset files to include in the install
    #          If omitted, all assets are downloaded
    #          Accepts regex inputs
  - name: MyPlugin
    #
    version: "1.2.3"
    id: "Plugin ID"
    assets:
      - "pluginfile-A-.*.jar"
      - "pluginfile-B-.*.jar"
```

### Repositories

MinecraftInstallManager is configured to search for plugins from
- Spiget: https://spigetmc.com
- Modrinth: https://modrinth.com
- GitHub: https://github.com

MinecraftInstallManager is configured to search for servers from
- Paper: https://papermc.io
