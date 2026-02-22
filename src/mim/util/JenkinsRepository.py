from mim.util.Repository import *
import requests
import os
import validators

class JenkinsRepository(PluginRepository):
    """A default repository implementation for Jenkins-hosted plugins
    """

    def __init__(self):
        super().__init__(
            name='Jenkins',
            description='A repository for Jenkins-hosted Minecraft plugins',
            api_url='https://ci.ender.zone/job/',
            homepage_url='https://ci.ender.zone/job'
        )

    def search(self, plugin:Plugin) -> list[PluginVersion]|None:
        if not plugin.id:
            return None
        
        if not validators.url(plugin.id):
            return None
            
        response = requests.get(f'{plugin.id}/api/json?depth=2')
        if response.status_code != 200:
            return None

        versions: list[PluginVersion] = []

        data = response.json()

        # Process permalinks
        build_permalinks = [
            'lastSuccessfulBuild',
            'lastStableBuild',
            'lastBuild',
            'lastCompletedBuild'
        ]
        for permalink in build_permalinks:
            release = data.get(permalink)
            if release:
                if release.get('result') == 'SUCCESS':
                    versions.append(PluginVersion(plugin=plugin, version=permalink, repository=self, metadata=release))
                
        # Process builds
        builds = data.get('builds',[])
        
        for release in builds:
            if release.get('result') == 'SUCCESS':
                versions.append(PluginVersion(plugin=plugin, version=str(release['number']), repository=self, metadata=release))
        return versions
    
    def listAssets(self, plugin_version:PluginVersion) -> list[PluginAsset]:
        assets = []
        for asset in plugin_version.metadata['artifacts']:
            filename = asset['displayPath']
            if str({plugin_version.metadata["number"]}) not in filename:
                filename = filename.replace('.jar', f'-{plugin_version.metadata["number"]}.jar')
            plugin_asset = PluginAsset(filename=filename, plugin_version=plugin_version, metadata=asset)
            assets.append(plugin_asset)
        return assets
    
    def install(self, plugin_asset:PluginAsset, destination:str) -> list[str]|None:
        if plugin_asset.repository != self:
            raise ValueError(f'Plugin version {plugin_asset.plugin.name} does not belong to Jenkins repository')
        
        install_url = plugin_asset.plugin_version.metadata['url'] + 'artifact/' + plugin_asset.metadata['relativePath']
        destination = os.path.join(destination, plugin_asset.filename)

        try:
            with requests.get(install_url, stream=True) as r:
                r.raise_for_status()
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return destination
        except requests.exceptions.RequestException as e:
            raise Exception(f'Error installing Jenkins plugin {plugin_asset.plugin.name} version {plugin_asset.version}: {e}')