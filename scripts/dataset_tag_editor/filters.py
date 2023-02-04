from typing import Set, Dict
from enum import Enum


class Filter:
    def apply(self, dataset):
        return dataset
    def __str__(self):
        return ''


class TagFilter(Filter):
    class Logic(Enum):
        NONE = 0
        AND = 1
        OR = 2

    class Mode(Enum):
        NONE = 0
        INCLUSIVE = 1
        EXCLUSIVE = 2
        
    def __init__(self, tags: Set[str] = set(), logic: Logic = Logic.NONE, mode: Mode = Mode.NONE):
        self.tags = tags
        self.logic = logic
        self.mode = mode
    
    def apply(self, dataset):
        if not self.tags or self.logic == TagFilter.Logic.NONE or self.mode == TagFilter.Mode.NONE:
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
        if len(self.tags) == 0:
            return ''
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
        
        
        
class PathFilter(Filter):
    class Mode(Enum):
        NONE = 0
        INCLUSIVE = 1
        EXCLUSIVE = 2

    def __init__(self, paths: Set[str] = {}, mode: Mode = Mode.NONE):
        self.paths = paths
        self.mode = mode
    
    def apply(self, dataset):
        if self.mode == PathFilter.Mode.NONE:
            return dataset
        
        paths_remove = self.paths
        if self.mode == PathFilter.Mode.INCLUSIVE:
            paths_remove = {path for path in dataset.datas.keys()} - paths_remove
        
        for path in paths_remove:
            dataset.remove_by_path(path)
        
        return dataset

    
class TagScoreFilter(Filter):
    class Mode(Enum):
        NONE = 0
        LESS_THAN = 1
        GREATER_THAN = 2

    def __init__(self, scores: Dict[str, Dict[str, float]], tag: str, threshold: float, mode: Mode = Mode.NONE):
        self.scores = scores
        self.mode = mode
        self.tag = tag
        self.threshold = threshold
    
    def apply(self, dataset):
        if self.mode == TagScoreFilter.Mode.NONE:
            return dataset
        
        paths_remove = {path for path, scores in self.scores.items() if (scores.get(self.tag) or 0) > self.threshold}
        
        if self.mode == TagScoreFilter.Mode.GREATER_THAN:
            paths_remove = {path for path in dataset.datas.keys()} - paths_remove
        
        for path in paths_remove:
            dataset.remove_by_path(path)
        
        return dataset