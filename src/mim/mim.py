#! python
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path
from typing import List
from packaging.version import Version, InvalidVersion
import traceback


from mim.util.GithubRepository import GithubRepository
from mim.util.ModrinthRepository import ModrinthRepository
from mim.util.SpigetRepository import SpigetRepository
from mim.util.PaperRepository import PaperRepository
from mim.util.GeyserRepository import GeyserRepository
from mim.util.Repository import Plugin, PluginRepository, PluginVersion, PluginAsset, Server, ServerRepository
import re
import json
import yaml

def find_versions(name: str | None, id: str | None, loader: str|None, server: str|None) -> List[PluginVersion]:
    """Find plugin versions by name and/or id using registered repositories."""
    if not name and not id:
        raise ValueError('name or id must be provided')

    # Build Plugin object and search all repositories
    plugin = Plugin(name, id=id)
    versions = plugin.versions
    # Filter by loaders if specified
    if loader:
        versions = [v for v in versions if not v.compatibility or any(s.name.lower() == loader.lower() for s in v.compatibility)]
    # Filter by server versions if specified
    if server:
        servers = ServerRepository.searchAll(server)
        versions = [v for v in versions if not v.compatibility or any(s in servers for s in v.compatibility)]
    return versions


def list_versions(args):
    versions = find_versions(args.name, args.id, args.loader, args.server)
    if not versions:
        print('No versions found')
        return
    for v in versions:
        repo = v.repository.name if v.repository else 'unknown'
        compat = ','.join([s.minecraft_version for s in v.compatibility]) if v.compatibility else 'any'
        print(f'{v.plugin.name} {v.version} (repo={repo}, compatibility={compat})')


def list_assets(args):
    # Need plugin name/id and version
    versions = find_versions(args.name, args.id, args.loader, args.server)
    if not versions:
        print('No versions found')
        return
    
    for v in versions:
        if args.version and v.version == args.version:
            print(f'Assets for {v.plugin.name} {v.version}:')
            for a in v.assets:
                print(f' - {a.filename}')


def download(args):
    dest = Path(args.destination) if args.destination else Path.cwd()
    dest.mkdir(parents=True, exist_ok=True)

    versions = find_versions(args.name, args.id, args.loader, args.server)
    if not versions:
        print('No versions found')
        return

    if args.version:
        versions = [v for v in versions if v.version == args.version]

    if not versions:
        print('No matching versions')
        return

    for v in versions:
        print(f'Downloading version {v.version} of {v.plugin.name}...')
        assets = v.assets
        if args.asset:
            try:
                patterns = [re.compile(p) for p in args.asset]
            except re.error as e:
                print(f'Invalid regex in --asset: {e}')
                patterns = []
            assets = [a for a in assets if any(p.search(a.filename) for p in patterns)]
        if not assets:
            print(' No assets to download')
            continue
        for a in assets:
            try:
                path = a.install(str(dest))
                print(f'  - downloaded {a.filename} -> {path}')
            except Exception as e:
                print(f'  - failed to download {a.filename}: {e}')

def install(args):

    # locate input json attribute
    input_file = None
    for attr in ('file', 'json', 'input', 'yaml'):
        if hasattr(args, attr) and getattr(args, attr):
            input_file = getattr(args, attr)
            break
    if not input_file:
        raise ValueError('No input file specified (expected config.file / config.json / config.yaml / config.input)')

    in_path = Path(input_file)
    if not in_path.exists():
        raise FileNotFoundError(f'Input file not found: {in_path}')

    dest = None
    for dattr in ('destination', 'dest', 'directory'):
        if hasattr(args, dattr) and getattr(args, dattr):
            dest = Path(getattr(args, dattr))
            break
    dest = dest or Path.cwd()
    dest.mkdir(parents=True, exist_ok=True)

    try:
        data = json.loads(in_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        try:
            data = yaml.safe_load(in_path.read_text(encoding='utf-8'))
        except:
            raise Exception(f'Unable to read from {in_path}')
    except:
        raise Exception(f'Unable to read from {in_path}')


    if not isinstance(data, dict):
        raise TypeError('Input json must be a dict defining server and plugin specifications')
    
    server = data.get('version','1.x.x')
    loader = data.get('loader')
    
    if not loader:
        raise ValueError('Input json must define a "loader" field for the server loader (e.g., paper, spigot, vanilla)')
    
    servers = [server for server in ServerRepository.searchAll(server) if server.name.lower() == loader.lower()]

    if not servers:
        raise ValueError(f'No matching server found for version {server} and loader {loader}')

    unspecified_servers = servers.copy()
    specified_servers = servers.copy()

    # Process
    unspecified_plugins = []
    specified_plugins = []
    for entry in data.get('plugins', []):
        if not isinstance(entry, dict):
            print('Skipping non-dict entry in json')
            continue
        name = entry.get('name')
        version = entry.get('version')
        pid = entry.get('id')
        assets_spec = entry.get('assets')

        if not name:
            raise ValueError('Plugin entry missing "name"')

        versions = find_versions(name, pid, loader, server)

        if version:
            versions = [v for v in versions if v.version == version]

        if not versions:
            raise ValueError(f'No versions found for {name} (id={pid})')

        if assets_spec:
            try:
                patterns = [re.compile(p) for p in assets_spec]
            except re.error as e:
                raise ValueError(f'Invalid regex in assets for {name}: {e}')
            
            versions = [v for v in versions if all(any(p.search(a.filename) for a in v.assets) for p in patterns)]
            
            if not versions:
                raise ValueError(f'No versions found providing required assets for {name} {version}')
        
        if version:
            specified_plugins.append(versions)
            specified_servers = [s for s in specified_servers if any(not v.compatibility or s in v.compatibility for v in versions)]
        else:
            unspecified_plugins.append(versions)
            unspecified_servers = [s for s in unspecified_servers if any(not v.compatibility or s in v.compatibility for v in versions)]

    if not servers:
        raise ValueError(f'No server version {server} with loader {loader} found compatible with all plugins. Specify plugin versions manually to override.')
    

    # Select a server version
    if not specified_servers:
        print(f'No server version {server} with loader {loader} compatible with all plugins with unspecified versions. Continuing at risk')
        servers = unspecified_servers
    else:
        servers = [s for s in specified_servers if s in unspecified_servers]

    if not servers:
        print(f'No server version {server} with loader {loader} compatible with all plugins. Continuing at risk')
        servers = unspecified_servers

    servers.sort(key=lambda x: Version(x.server_version), reverse=True)

    server = servers[0]

    # Select versions for unspecified plugins
    plugin_versions: list[PluginVersion] = []

    for versions in unspecified_plugins:
        versions = [v for v in versions if not v.compatibility or server in v.compatibility]
        try:
            versions.sort(key=lambda x: Version(x.version), reverse=True)
        except InvalidVersion:
            versions.sort(key=lambda x: x.version, reverse=True)

        plugin_versions.append(versions[0])

    # Check for specified plugin updates
    plugin_versions.extend([v[0] for v in specified_plugins])

    # Install the minecraft server
    print(f'===== Server =====')
    current_servers = server.installedVersions(dest)
    if not current_servers or current_servers[0] != server or args.force:
        print(f'{server.name} Version: {server.server_version}' + (f' (Updated from {current_servers[0].server_version})' if current_servers else ''))
        print(f'Minecraft Version: {server.minecraft_version}' + (f' (Updated from {current_servers[0].minecraft_version})' if current_servers else ''))
        if not args.dryrun:
            file=server.install(dest)
            if not file:
                raise FileNotFoundError(f'Download failed for server version {server.server_version}')
            
            print(f'   Installed {os.path.basename(file)}')

            # Uninstall existing installations
            for s in current_servers:
                file=s.uninstall(dest)
                if not file:
                    raise Exception(f'Failed to uninstall {server.asset}')
                else:
                    print(f'   Uninstalled {os.path.basename(file)}')

    else:
        print(f'{server.name} Version: {server.server_version} (Up to date)')
        print(f'Minecraft Version: {server.minecraft_version} (Up to date)')
    
    # Install server plugins
    print(f'\n===== Plugins =====')
    plugin_dest = dest / 'plugins'
    if not args.dryrun:
        plugin_dest.mkdir(exist_ok=True)

    for version in plugin_versions:
        current_versions = version.plugin.installedVersions(plugin_dest)
        if not current_versions or current_versions[0] != version or args.force:
            print(f'{version.plugin.name} Version: {version.version}' + (f' (Updated from {current_versions[0].version})' if current_versions else ''))
            
            if not args.dryrun:
                index = [n['name'] for n in data['plugins']].index(version.plugin.name)
                assets = data['plugins'][index].get('assets')
                if assets:
                    try:
                        patterns = [re.compile(p) for p in assets]
                    except re.error as e:
                        raise ValueError(f'Invalid regex in assets for {name}: {e}')
                    
                    assets = [a for a in version.assets if any( p.search(a.filename) for p in patterns )]
                    files = []
                    for a in assets:
                        file = a.install(plugin_dest)
                        if not file:
                            raise FileNotFoundError(f'Download failed for {version.plugin.name} version {version.version} asset {a.filename}')
                        files.append(file)
                else:
                    files=version.install(plugin_dest)
                    if not files:
                        raise FileNotFoundError(f'Download failed for {version.plugin.name} version {version.version}')
                
                for file in files:
                    print(f'   Installed {os.path.basename(file)}')

                # Uninstall existing installations
                for v in current_versions:
                    files=v.uninstall(dest)
                    if not files:
                        raise Exception(f'Failed to uninstall {v.plugin.name} {v.version}')
                    else:
                        for file in files:
                            print(f'   Uninstalled {os.path.basename(file)}')
        else:
            print(f'{version.plugin.name} Version: {version.version} (Up to date)')

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='mim', description='Minecraft Install Manager CLI')
    sub = p.add_subparsers(dest='command')

    p_versions = sub.add_parser('versions', help='List plugin versions')
    p_versions.add_argument('--name', '-n', help='Plugin name')
    p_versions.add_argument('--id', '-i', help='Plugin id')
    p_versions.add_argument('--loader', '-l', help='Filter by loader (e.g., paper, spigot)')
    p_versions.add_argument('--server', '-s', help='Filter by Minecraft server version (e.g., 1.16, 1.17.x)')
    p_versions.set_defaults(func=list_versions)

    p_assets = sub.add_parser('assets', help='List assets for plugin version')
    p_assets.add_argument('--name', '-n', help='Plugin name')
    p_assets.add_argument('--id', '-i', help='Plugin id')
    p_assets.add_argument('--version', '-v', help='Plugin version to inspect')
    p_assets.add_argument('--loader', '-l', help='Filter by loader (e.g., paper, spigot)')
    p_assets.add_argument('--server', '-s', help='Filter by Minecraft server version (e.g., 1.16, 1.17.x)')
    p_assets.set_defaults(func=list_assets)

    p_download = sub.add_parser('download', help='Download plugin versions or specific assets')
    p_download.add_argument('--name', '-n', help='Plugin name')
    p_download.add_argument('--id', '-i', help='Plugin id')
    p_download.add_argument('--version', '-v', help='Specific plugin version to download')
    p_download.add_argument('--loader', '-l', help='Filter by loader (e.g., paper, spigot)')
    p_download.add_argument('--server', '-s', help='Filter by Minecraft server version (e.g., 1.16, 1.17.x)')
    p_download.add_argument('--asset', '-a', nargs='+', help='Specific asset filename(s) to download (one or more). Supports regex')
    p_download.add_argument('--destination', '-d', help='Directory to save downloads')
    p_download.set_defaults(func=download)

    p_install = sub.add_parser('install', help='Install plugins from a JSON or YAML specification file')
    p_install.add_argument('--file', '-f', required=True, help='Path to input JSON or YAML file specifying plugins to install')
    p_install.add_argument('--destination', '-d', help='Directory to install plugins to')
    p_install.add_argument('--force', action='store_true', help='Force redownload of existing installations')
    p_install.add_argument('--dryrun', action='store_true', help='Perform a dry run without actual downloads or installations')
    p_install.set_defaults(func=install)

    return p


def main(argv: List[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    try:
        GeyserRepository()
        GithubRepository()
        ModrinthRepository()
        SpigetRepository()
        PaperRepository()
        args.func(args)
        return 0
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
