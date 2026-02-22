from mim.util.Repository import Plugin
import pytest
import os

jenkins_plugins = [
    # ('GlobalEffects','saro476/GlobalEffects'),
    ('EssentialsX','https://ci.ender.zone/job/EssentialsX')
]

@pytest.mark.parametrize("plugin_name,plugin_id", jenkins_plugins)
def test_search_jenkins_plugins(jenkins_repository, plugin_name, plugin_id):
    versions = jenkins_repository.search(plugin=Plugin(plugin_name, plugin_id))
    assert versions is not None
    assert len(versions) > 0
    for version in versions:
        assert version.repository == jenkins_repository
        assert version.version is not None

@pytest.mark.parametrize("plugin_name,plugin_id", jenkins_plugins)
def test_searchall_jenkins_plugins(jenkins_repository, plugin_name, plugin_id):
    versions = jenkins_repository.searchAll(plugin=Plugin(plugin_name, plugin_id))
    assert versions is not None
    assert len(versions) > 0
    assert any(version.repository == jenkins_repository for version in versions)
    assert all(version.version is not None for version in versions)

@pytest.mark.parametrize("plugin_name,plugin_id", jenkins_plugins)
def test_jenkins_repository_install(jenkins_repository, plugin_name, plugin_id, tmp_path):
    plugin = Plugin(plugin_name, plugin_id)
    versions = jenkins_repository.search(plugin=plugin)
    files = versions[0].install(tmp_path)
    assert files
    for file in files:
        assert file is not None
        assert os.path.isfile(file)

@pytest.mark.parametrize("plugin_name,plugin_id", jenkins_plugins)
def test_jenkins_plugin_installed_versions(plugin_name, plugin_id, tmp_path):
    plugin = Plugin(plugin_name,plugin_id)
    versions = plugin.versions
    assert versions is not None
    assert len(versions) > 0
    files = versions[-1].install(tmp_path)
    installed_versions = plugin.installedVersions(tmp_path)
    assert len(installed_versions) == 1
    assert installed_versions[0] == versions[-1]
    for file in files:
        assert file is not None
        assert os.path.isfile(file)

