from mim.util.Repository import *
import requests
import os

class GithubRepository(PluginRepository):
    """A default repository implementation for GitHub-hosted plugins
    """

    def __init__(self):
        super().__init__(
            name='GitHub',
            description='A repository for GitHub-hosted Minecraft plugins',
            api_url='https://api.github.com/repos/',
            homepage_url='https://github.com'
        )

    def search(self, plugin:Plugin) -> list[PluginVersion]|None:
        if not plugin.id:
            return None
        response = requests.get(f'{self.api}{plugin.id}/releases')
        if response.status_code != 200:
            return None
        
        versions: list[PluginVersion] = []
        for release in response.json():
            versions.append(PluginVersion(plugin=plugin, version=release['tag_name'], repository=self, metadata=release))
        return versions
    
    def listAssets(self, plugin_version:PluginVersion) -> list[PluginAsset]:
        assets = []
        for asset in plugin_version.metadata['assets']:
            filename = asset['name']
            if plugin_version.version not in filename:
                filename = filename.replace('.jar', f'-{plugin_version.version}.jar')
            plugin_asset = PluginAsset(filename=filename, plugin_version=plugin_version, metadata=asset)
            assets.append(plugin_asset)
        return assets
    
    def install(self, plugin_asset:PluginAsset, destination:str) -> list[str]|None:
        if plugin_asset.repository != self:
            raise ValueError(f'Plugin version {plugin_asset.plugin.name} does not belong to GitHub repository')
        
        install_url = plugin_asset.metadata['browser_download_url']
        destination = os.path.join(destination, plugin_asset.filename)

        try:
            with requests.get(install_url, stream=True) as r:
                r.raise_for_status()
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return destination
        except requests.exceptions.RequestException as e:
            raise Exception(f'Error installing GitHub plugin {plugin_asset.plugin.name} version {plugin_asset.version}: {e}')
        