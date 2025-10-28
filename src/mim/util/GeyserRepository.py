from mim.util.Repository import *
import requests
import os

class GeyserRepository(PluginRepository):
    """A default repository implementation for Geyser plugins
    """

    def __init__(self):
        super().__init__(
            name='Geyser',
            description='A repository for GeyserMC Minecraft plugins',
            api_url='https://download.geysermc.org/v2/',
            homepage_url='https://geysermc.org/'
        )
    
    def search(self, plugin:Plugin) -> list[PluginVersion]|None:
        project_response = requests.get(f'{self.api}projects/{plugin.name.lower()}').json()
        if not 'versions' in project_response:
            return []
        project_versions = project_response['versions']

        versions: list[PluginVersion] = []
        for pv in project_versions:
            build_response = requests.get(f'{self.api}projects/{plugin.name.lower()}/versions/{pv}/builds').json()
            version_builds=build_response['builds']
            for vb in version_builds:
                build = vb['build']
                channel = vb['channel']
                downloads = vb['downloads']

                if channel.lower() == 'default':
                    servers = ServerRepository.searchAll('1.x.x')
                    for loader,download in downloads.items():
                        file = download['name']
                        compatibility = [server for server in servers if server.name.lower() == loader or server.name.lower() == 'paper' and loader == 'spigot']
                        metadata = {
                            'project': plugin.name.lower(),
                            'version': pv,
                            'loader': loader,
                            'build': build,
                            'file': file
                        }
                        if compatibility:
                            versions.append(PluginVersion(plugin=plugin, version=f'{pv}.{build}', repository=self, compatibility=compatibility, metadata=metadata))
        return versions
    
    def listAssets(self, plugin_version:PluginVersion) -> list[PluginAsset]:
        assets = []
        filename = plugin_version.metadata['file']
        if plugin_version.version not in filename:
            filename = filename.replace('.jar', f'-{plugin_version.version}.jar')
        asset = PluginAsset(filename=filename, plugin_version=plugin_version, metadata=plugin_version.metadata.copy())
        assets.append(asset)
        return assets
    
    def install(self, plugin_asset:PluginAsset, destination:str) -> list[str]|None:
        if plugin_asset.repository != self:
            raise ValueError(f'Plugin version {plugin_asset.plugin.name} does not belong to Geyser repository')
        
        project = plugin_asset.metadata['project']
        version = plugin_asset.metadata['version']
        build = plugin_asset.metadata['build']
        loader = plugin_asset.metadata['loader']
        install_url = f'{self.api}projects/{project}/versions/{version}/builds/{build}/downloads/{loader}'
        destination = os.path.join(destination, plugin_asset.filename)

        try:
            with requests.get(install_url, stream=True) as r:
                r.raise_for_status()
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return destination
        except requests.exceptions.RequestException as e:
            raise Exception(f'Error installing Geyser plugin {plugin_asset.plugin.name} version {plugin_asset.version}: {e}')