from pathlib import Path

from scripts.singleton import Singleton

def base_dir_path():
    return Path(__file__).parents[1].absolute()

def base_dir():
    return str(base_dir_path())

class Paths(Singleton):
    def __init__(self):
        self.base_path:Path = base_dir_path()
        self.script_path: Path = self.base_path / "scripts"
        self.userscript_path: Path = self.base_path / "userscripts"
        self.model_path = self.base_path / "models"

paths = Paths()