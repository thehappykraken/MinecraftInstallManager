import os
def test_list_paper_servers(paper_repository):
    servers = paper_repository.list()
    assert len(servers) > 0
    for server in servers:
        assert server.repository == paper_repository
        assert server.name.startswith('Paper')
        assert server.server_version is not None
        assert server.minecraft_version is not None

def test_paper_repository_install(paper_repository, tmp_path):
    servers = paper_repository.list()
    paper_server = servers[0]
    file = paper_repository.install(paper_server, tmp_path)
    assert file is not None
    assert os.path.isfile(file)
