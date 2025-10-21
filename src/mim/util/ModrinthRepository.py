from mim.util.Repository import *
import requests
import os

class ModrinthRepository(PluginRepository):
    """A default repository implementation for Modrinth plugins
    """

    def __init__(self):
        super().__init__(
            name='Modrinth',
            description='A repository for Modrinth Minecraft plugins',
            api_url='https://api.modrinth.com/v2/',
            homepage_url='https://modrinth.com/'
        )
    
    def search(self, plugin:Plugin) -> list[PluginVersion]|None:
        response = requests.get(f'{self.api}search?query={plugin.name}').json()
        versions: list[PluginVersion] = []
        for project in response['hits']:
            if project['title'].lower() == plugin.name.lower() or project['slug'].lower() == plugin.name.lower():
                project_id = project['project_id']
                version_response = requests.get(f'{self.api}project/{project_id}/version').json()
                for version in version_response:
                    if version.get('version_type') == 'release':
                        game_versions = version['game_versions']
                        loaders = version['loaders']
                        compatibility: list[Server] = []
                        for gv in game_versions:
                            servers = ServerRepository.searchAll(gv)
                            compatibility.extend([server for server in servers if server.name.lower() in loaders])
                        if compatibility:
                            versions.append(PluginVersion(plugin=plugin, version=version['version_number'], repository=self,compatibility=compatibility,metadata=version))
        return versions
    
    def listAssets(self, plugin_version:PluginVersion) -> list[PluginAsset]:
        assets = []
        for file in plugin_version.metadata['files']:
            filename = file['filename']
            if plugin_version.version not in filename:
                filename = filename.replace('.jar', f'-{plugin_version.version}.jar')
            asset = PluginAsset(filename=filename, plugin_version=plugin_version, metadata=file)
            assets.append(asset)
        return assets
    
    def install(self, plugin_asset:PluginAsset, destination:str) -> list[str]|None:
        if plugin_asset.repository != self:
            raise ValueError(f'Plugin version {plugin_asset.plugin.name} does not belong to Modrinth repository')
        
        install_url = plugin_asset.metadata['url']
        destination = os.path.join(destination, plugin_asset.filename)

        try:
            with requests.get(install_url, stream=True) as r:
                r.raise_for_status()
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return destination
        except requests.exceptions.RequestException as e:
            raise Exception(f'Error installing Modrinth plugin {plugin_asset.plugin.name} version {plugin_asset.version}: {e}')