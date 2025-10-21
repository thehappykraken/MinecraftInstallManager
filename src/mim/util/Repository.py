from __future__ import annotations
import os

class Server:
    def __init__(self, name:str, server_version:str, minecraft_version:str, repository:ServerRepository):
        self.name = name
        self.server_version = server_version
        self.minecraft_version = minecraft_version
        self.repository = repository

    @property
    def asset(self):
        return f'{self.name}-{self.server_version}.jar'

    def install(self, destination:str) -> str:
        return self.repository.install(self,destination)

    def uninstall(self, destination:str) -> str:
        return self.repository.uninstall(self,destination)
        
    def installedVersions(self, directory:str) -> list[Server]:
        """Checks the specified directory for installed versions of this plugin

        Parameters
        ----------
        directory : str
            The directory to check for installed versions

        Returns
        -------
        list[str]
            A list of installed version strings
        """
        installed_versions = []
        for server in self.repository.list():
            filepath = os.path.join(directory, server.asset)
            if os.path.isfile(filepath):
                installed_versions.append(server)
                break
        return installed_versions

class ServerRepository:
    """This class defines an interface for working with repositories
    """
    _registry: dict[str, ServerRepository] = {}

    def __init__(self,name:str,description:str|None=None,api_url:str|None=None,homepage_url:str|None=None):
        """Initializes a repository object

        Parameters
        ----------
        name : str
            The name of the repository
        description : str, optional
            A description of the repository, by default None
        api_url : str, optional
            The API URL, by default None
        homepage_url : str, optional
            The home page URL, by default None
        """

        self.name = name
        self.description = description
        self.api = api_url
        self.homepage = homepage_url

        self._registry[name.lower()] = self

    def search(self, minecraft_version:str) -> list[Server]|None:
        """Searches for a server in the repository that meets the minecraft version requirement

        Parameters
        ----------
        version : str
            The minecraft version to search for

        Returns
        -------
        list[Server]
            If located, returns a list of Server objects
        """
        raise NotImplementedError('search is not implemented for the default ServerRepository class')
    
    def list(self) -> list[Server]:
        raise NotImplementedError('list is not implemented for the default ServerRepository class')
    
    def install(self, server:Server, destination:str) -> str:
        raise NotImplementedError('install is not implemented for the default ServerRepository class')
        
    def uninstall(self, server:Server, destination:str) -> str|None:
        
        destination = os.path.join(destination, server.asset)
        if os.path.exists(destination):
            os.remove(destination)

        if os.path.exists(destination):
            return None
        else:
            return destination
    
    @staticmethod
    def searchAll(minecraft_version:str) -> list[Server]:
        results = []
        for repo in ServerRepository._registry.values():
            server = repo.search(minecraft_version)
            if server:
                results.extend(server)
        return results

class PluginAsset:
    def __init__(self, filename:str, plugin_version:PluginVersion, metadata:dict|None=None):
        self.filename = filename
        self.plugin_version = plugin_version
        self.metadata = metadata
    
    @property
    def plugin(self) -> Plugin:
        return self.plugin_version.plugin
    
    @property
    def repository(self) -> PluginRepository:
        return self.plugin_version.repository
    
    @property
    def compatibility(self) -> list[Server]|None:
        return self.plugin_version.compatibility
    
    @property
    def version(self) -> str:
        return self.plugin_version.version

    def install(self, destination:str) -> str|None:
        return self.repository.install(self, destination)
    
    def uninstall(self, destination:str) -> str|None:
        return self.repository.uninstall(self, destination)

class PluginVersion:
    def __init__(self, plugin:Plugin, version:str, repository:PluginRepository, compatibility:list[Server]|None=None, metadata:dict|None=None):
        self.plugin = plugin
        self.version = version
        self.repository = repository
        self.compatibility = compatibility
        self.metadata = metadata
        self._assets: list[PluginAsset]|None = None

    @property
    def assets(self) -> list[PluginAsset]:
        if not self._assets:
            self._assets = self.repository.listAssets(self)
        return self._assets

    def install(self, destination:str) -> str|None:
        return [asset.install(destination) for asset in self.assets]
    
    def uninstall(self, destination:str) -> str|None:
        return [asset.uninstall(destination) for asset in self.assets]

class Plugin:
    def __init__(self, name:str, id:str|None=None):
        self.name = name
        self.id = id
        self._versions: list[PluginVersion]|None = None

    @property
    def versions(self) -> list[PluginVersion]:
        if self._versions is not None:
            return self._versions
        else:
            self._versions = PluginRepository.searchAll(self)
            return self._versions
        
    def installedVersions(self, directory:str) -> list[PluginVersion]:
        """Checks the specified directory for installed versions of this plugin

        Parameters
        ----------
        directory : str
            The directory to check for installed versions

        Returns
        -------
        list[str]
            A list of installed version strings
        """
        installed_versions = []
        for version in self.versions:
            for asset in version.assets:
                filepath = os.path.join(directory, asset.filename)
                if os.path.isfile(filepath):
                    installed_versions.append(version)
                    break
        return installed_versions

class PluginRepository:
    """This class defines an interface for working with repositories
    """
    _registry: dict[str, PluginRepository] = {}

    def __init__(self,name:str,description:str|None=None,api_url:str|None=None,homepage_url:str|None=None):
        """Initializes a repository object

        Parameters
        ----------
        name : str
            The name of the repository
        description : str, optional
            A description of the repository, by default None
        api_url : str, optional
            The API URL, by default None
        homepage_url : str, optional
            The home page URL, by default None
        """

        self.name = name
        self.description = description
        self.api = api_url
        self.homepage = homepage_url
        PluginRepository._registry[name.lower()] = self

    def search(self, plugin:Plugin) -> list[PluginVersion]|None:
        """Searches for a plugin in the repository

        Parameters
        ----------
        plugin : str
            The name of the plugin to search for

        Returns
        -------
        list[PluginVersion]
            If located, returns a list of PluginVersion objects
        """
        raise NotImplementedError('search is not implemented for the default Repository class')
    
    def listAssets(self, plugin_version:PluginVersion) -> list[PluginAsset]:
        raise NotImplementedError('listAssets is not implemented for the default Repository class')
    
    def install(self, plugin_asset:PluginAsset, destination:str) -> str|None:
        raise NotImplementedError('install is not implemented for the default Repository class')
    
    def uninstall(self, plugin_asset:PluginAsset, destination:str) -> list[str]|None:
        
        destination = os.path.join(destination, plugin_asset.filename)
        if os.path.exists(destination):
            os.remove(destination)

        if os.path.exists(destination):
            return None
        else:
            return destination
    
    @staticmethod
    def searchAll(plugin:Plugin) -> list[PluginVersion]:
        results = []
        for repo in PluginRepository._registry.values():
            pluginVersion = repo.search(plugin)
            if pluginVersion:
                results.extend(pluginVersion)
        return results