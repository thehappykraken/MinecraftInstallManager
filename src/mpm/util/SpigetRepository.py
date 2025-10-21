from mpm.util.Repository import *
import requests
import os

class SpigetRepository(PluginRepository):
    """A default repository implementation for Spiget plugins
    """

    def __init__(self):
        super().__init__(
            name='Spiget',
            description='A repository for Spiget Minecraft plugins',
            api_url='https://api.spiget.org/v2/',
            homepage_url='https://spiget.org/'
        )

    def search(self, plugin:Plugin) -> list[PluginVersion]|None:
        if not plugin.id:
            return None
        response = requests.get(f'{self.api}resources/{plugin.id}')
        if response.status_code != 200:
            return None
        
        tested_versions = response.json()['testedVersions']
        versions: list[PluginVersion] = []
        
        version_response = requests.get(f'{self.api}resources/{plugin.id}/versions?size=50&sort=-id').json()
        
        compatibility: list[Server] = []
        for tv in tested_versions:
            if len(tv.split('.')) == 2:
                tv += '.x'
            loaders = ['bukkit', 'spigot', 'paper']
            servers = [server for server in ServerRepository.searchAll(tv) if server.name.lower() in loaders]
            compatibility.extend(servers)

        for version in version_response:
            versions.append(PluginVersion(plugin=plugin, version=version['name'], repository=self, compatibility=compatibility.copy(), metadata=version))
        return versions
    
    def listAssets(self, plugin_version:PluginVersion) -> list[PluginAsset]:
        filename = f'{plugin_version.plugin.name}-{plugin_version.plugin.id}-{plugin_version.version}.jar'
        asset = PluginAsset(filename=filename, plugin_version=plugin_version, metadata=plugin_version.metadata)
        return [asset]
    
    def install(self, plugin_asset:PluginAsset, destination:str) -> list[str]|None:
        if plugin_asset.repository != self:
            raise ValueError(f'Plugin version {plugin_asset.plugin.name} does not belong to Spiget repository')
        
        install_url = f'{self.api}resources/{plugin_asset.plugin.id}/download?release={plugin_asset.metadata["id"]}'
        destination = os.path.join(destination, plugin_asset.filename)

        try:
            with requests.get(install_url, stream=True) as r:
                r.raise_for_status()
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return destination
        except requests.exceptions.RequestException as e:
            raise Exception(f'Error installing Spiget plugin {plugin_asset.plugin.name} version {plugin_asset.version}: {e}')
