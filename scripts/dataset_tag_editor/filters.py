from scripts.dataset_tag_editor.dataset import Dataset
from typing import Set, List
from enum import Enum

class TagFilter(Dataset.Filter):
    class Logic(Enum):
        NONE = 0
        AND = 1
        OR = 2

    class Mode(Enum):
        NONE = 0
        INCLUSIVE = 1
        EXCLUSIVE = 2
        
    def __init__(self, tags: Set[str] = {}, logic: Logic = Logic.NONE, mode: Mode = Mode.NONE):
        self.tags = tags
        self.logic = logic
        self.mode = mode
    
    def apply(self, dataset: Dataset):
        if self.logic == TagFilter.Logic.NONE or self.mode == TagFilter.Logic.NONE:
            return dataset
        
        paths_remove = []

        if self.logic == TagFilter.Logic.AND:
            if self.mode == TagFilter.Mode.INCLUSIVE:
                for path, data in dataset.datas.items():
                    if not data.tag_contains_allof(self.tags):
                        paths_remove.append(path)

            elif self.mode == TagFilter.Mode.EXCLUSIVE: 
                for path, data in dataset.datas.items():
                    if data.tag_contains_allof(self.tags):
                        paths_remove.append(path)

        elif self.logic == TagFilter.Logic.OR:
            if self.mode == TagFilter.Mode.INCLUSIVE:
                for path, data in dataset.datas.items():
                    if not data.tag_contains_anyof(self.tags):
                        paths_remove.append(path)

            elif self.mode == TagFilter.Mode.EXCLUSIVE: 
                for path, data in dataset.datas.items():
                    if data.tag_contains_anyof(self.tags):
                        paths_remove.append(path)
        
        for path in paths_remove:
            dataset.remove_by_path(path)

        return dataset
    
    def __str__(self):
        res = ''
        if self.mode == TagFilter.Mode.EXCLUSIVE:
            res += 'NOT '
        if self.logic == TagFilter.Logic.AND:
            res += 'AND'
        elif self.logic == TagFilter.Logic.OR:
            res += 'OR'
        if self.logic == TagFilter.Logic.AND or self.logic == TagFilter.Logic.OR:
            text = ', '.join([tag for tag in self.tags])
            res += f'({text})'
        return res
        
        
        
class PathFilter(Dataset.Filter):
    class Mode(Enum):
        NONE = 0
        INCLUSIVE = 1
        EXCLUSIVE = 2

    def __init__(self, paths: Set[str] = {}, mode: Mode = Mode.NONE):
        self.paths = paths
        self.mode = mode
    
    def apply(self, dataset: Dataset):
        if self.mode == PathFilter.Mode.NONE:
            return dataset
        
        paths_remove = self.paths
        if self.mode == PathFilter.Mode.INCLUSIVE:
            paths_remove = {path for path in dataset.datas.keys()} - paths_remove
        
        for path in paths_remove:
            dataset.remove_by_path(path)
        
        return dataset

    
    