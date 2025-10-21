
import mim.mim as mim
import os
import json
import glob

def test_main_help_and_exit_codes(monkeypatch, capsys):
    # When no func provided (empty argv) -> return 1
    code = mim.main([])
    assert code == 1

    # When func runs normally -> return 0
    def fake_list_versions(args):
        print("ran-list")
    monkeypatch.setattr(mim, 'list_versions', fake_list_versions)
    code = mim.main(['versions', '--name', 'x'])
    out = capsys.readouterr().out
    assert code == 0
    assert 'ran-list' in out

    # When func raises -> return 2 and stderr includes the error
    def bad_list_versions(args):
        raise Exception("boom")
    monkeypatch.setattr(mim, 'list_versions', bad_list_versions)
    code = mim.main(['versions', '--name', 'x'])
    captured = capsys.readouterr()
    assert code == 2
    assert 'Error: boom' in captured.err

def test_main_versions_list():
    args = ['versions', '--name', 'WorldEdit', '--loader', 'paper', '--server','1.20.x']
    result = mim.main(args)
    assert result == 0  # Ensure the command executed successfully

def test_main_assets_list():
    args = ['assets', '--name', 'WorldEdit', '--version', '7.3.9']
    result = mim.main(args)
    assert result == 0  # Ensure the command executed successfully

def test_main_download(tmp_path):
    args = ['download', '--name', 'QuickShop-Hikari', '--version', '3.3.0.0', '--asset', 'QuickShop.*', '.*WorldEdit.*', '--destination', tmp_path]
    result = mim.main(args)
    assert result == 0  # Ensure the command executed successfully
    file1 = os.path.join(tmp_path, 'QuickShop-Hikari-3.3.0.0.jar')
    file2 = os.path.join(tmp_path, 'Compat-WorldEdit-3.3.0.0.jar')
    assert os.path.isfile(file1)
    assert os.path.isfile(file2)

def test_main_install(tmp_path):
    # Prepare an install JSON that targets a plugin known to be available in tests
    data = {
        "version": "1.21.1",
        "loader": "paper",
        "plugins": [
            {
                "name": "QuickShop-Hikari",
                "assets": ["QuickShop.*", ".*WorldEdit.*"]
            },
            {
                "name": "WorldEdit",
                "version": "7.3.9"
            },
            {
            "name": "DeathChest",
            "id": "DevCyntrix/death-chest"
            },
        ]
    }
    json_file = os.path.join(tmp_path, "install.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    # Run the install command
    result = mim.main(['install', '--file', json_file, '--destination', tmp_path])
    assert result == 0

    # Run the install command
    result = mim.main(['install', '--file', json_file, '--destination', tmp_path])
    assert result == 0

    # Verify server was installed
    qs_matches = glob.glob(os.path.join(tmp_path, f"*{data['version']}*"))
    assert qs_matches and os.path.isfile(qs_matches[0])

    # Verify at least one expected asset was installed into the destination
    qs_matches = glob.glob(os.path.join(tmp_path, 'plugins', "*QuickShop*"))
    assert qs_matches and os.path.isfile(qs_matches[0])
    # assert qs_matches and qs_matches[0].is_file()

def test_main_install_dryrun(tmp_path):
    # Prepare an install JSON that targets a plugin known to be available in tests
    data = {
        "version": "1.21.1",
        "loader": "paper",
        "plugins": [
            {
                "name": "QuickShop-Hikari",
                "assets": ["QuickShop.*", ".*WorldEdit.*"]
            },
            {
                "name": "WorldEdit",
                "version": "7.3.9"
            }
        ]
    }
    json_file = os.path.join(tmp_path, "install.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    # Run the install command
    result = mim.main(['install', '--file', json_file, '--destination', tmp_path, '--dryrun'])
    assert result == 0

    # Verify at least one expected asset was installed into the destination
    qs_matches = glob.glob(os.path.join(tmp_path, "*QuickShop*"))
    assert not qs_matches
    # assert qs_matches and qs_matches[0].is_file()