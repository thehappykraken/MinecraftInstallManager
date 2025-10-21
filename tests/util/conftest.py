from src.mim.util.SpigetRepository import SpigetRepository
from src.mim.util.PaperRepository import PaperRepository
from src.mim.util.GithubRepository import GithubRepository
from src.mim.util.ModrinthRepository import ModrinthRepository
import pytest


@pytest.fixture(autouse=True,scope='session')
def spiget_repository():
    return SpigetRepository()

@pytest.fixture(autouse=True,scope='session')
def paper_repository():
    return PaperRepository()

@pytest.fixture(autouse=True,scope='session')
def github_repository():
    return GithubRepository()

@pytest.fixture(autouse=True,scope='session')
def modrinth_repository():
    return ModrinthRepository()