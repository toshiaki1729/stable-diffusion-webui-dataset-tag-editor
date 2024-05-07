import sys
from pathlib import Path
import importlib.util
from types import ModuleType

from scripts import logger
from scripts.paths import paths


class CustomScripts:
    def _load_module_from(self, path:Path):
        module_spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module
    
    def _load_derived_classes(self, module:ModuleType, base_class:type):
        derived_classes = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, base_class) and obj is not base_class:
                derived_classes.append(obj)
        
        return derived_classes

    def __init__(self, scripts_dir:Path) -> None:
        self.scripts = dict()
        self.scripts_dir = scripts_dir.absolute()

    def load_derived_classes(self, baseclass:type):
        back_syspath = sys.path
        if not self.scripts_dir.is_dir():
            logger.warn(f"NOT A DIRECTORY: {self.scripts_dir}")
            return []
          
        classes = []
        try:
            sys.path = [str(paths.base_path)] + sys.path
            for path in self.scripts_dir.glob("*.py"):
                self.scripts[path.stem] = self._load_module_from(path)
            for module in self.scripts.values():
                classes.extend(self._load_derived_classes(module, baseclass))
        except Exception as e:
            tb = sys.exc_info()[2]
            logger.error(f"Error on loading {path}")
            logger.error(e.with_traceback(tb))
        finally:
            sys.path = back_syspath
        
        return classes