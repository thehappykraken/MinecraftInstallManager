from mim.util.Repository import *
import requests
import os
import re

class PaperRepository(ServerRepository):
    """A default repository implementation for PaperMC servers
    """

    def __init__(self):
        super().__init__(
            name='Paper',
            description='A repository for PaperMC Minecraft servers',
            api_url='https://fill.papermc.io/v3/',
            homepage_url='https://papermc.io/'
        )
        self.servers: list[Server]|None = None
        self.user_agent = {'User-Agent': 'MinecraftPluginManager (https://github.com/thehappykraken/MinecraftPluginManager)'}

    def search(self, minecraft_version:str) -> list[Server]|None:
        servers = self.list()
        minecraft_version = minecraft_version.replace('.x','.?\d*')
        return [server for server in servers if re.fullmatch(minecraft_version, server.minecraft_version)]

    def list(self) -> list[Server]:
        if self.servers is not None:
            return self.servers
        
        servers: list[Server] = []
        response = requests.get(self.api + 'projects/paper', headers=self.user_agent).json()
        for major_version in response['versions']:
            for minor_version in response['versions'][major_version]:
                minecraft_version = minor_version
                servers.append(Server(name=f'Paper', repository=self, server_version=minecraft_version, minecraft_version=minecraft_version))
        self.servers = servers
        return servers
    
    def install(self, server, destination) -> str|None:
        if server.repository != self:
            raise ValueError(f'Server {server.name} does not belong to Modrinth repository')
        
        minecraft_version = server.minecraft_version
        response = requests.get(f'{self.api}projects/paper/versions/{minecraft_version}/builds', headers=self.user_agent).json()
        # latest_build = [build for build in response if build['channel'] == 'STABLE'][0]
        sort_priority = {'STABLE': 'C', 'BETA': 'B', 'ALPHA': 'A'}
        response.sort(key=lambda b: sort_priority[b['channel']]+str(b['id']), reverse=True)
        latest_build = response[0]
        server_version = minecraft_version + '-' + str(latest_build['id'])
        download_url = latest_build['downloads']['server:default']['url']
        destination = os.path.join(destination, server.asset)

        try:
            with requests.get(download_url, headers=self.user_agent, stream=True) as r:
                r.raise_for_status()
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return destination
        except requests.exceptions.RequestException as e:
            raise Exception(f'Error downloading Paper server version {server_version}: {e}')
