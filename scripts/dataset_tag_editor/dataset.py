from typing import Set, Dict

class Data:
    def __init__(self, imgpath: str, caption: str):
        self.imgpath = imgpath
        self.tags = [t.strip() for t in caption.split(',')]
        self.tagset = set(self.tags)

    def tag_contains_allof(self, tags: Set[str]):
        return self.tagset.issuperset(tags)
    
    def tag_contains_anyof(self, tags: Set[str]):
        return not self.tagset.isdisjoint(tags)


class Dataset:
    def __init__(self):
        self.datas: Dict[str, Data] = dict()
    
    def __len__(self):
        return len(self.datas)
    
    def clear(self):
        self.datas.clear()

    def merge(self, dataset, overwrite: bool = True):
        if type(dataset) is Dataset:
            for path in dataset.datas.keys():
                if overwrite or path not in self.datas.keys():
                    self.datas[path] = dataset[path]
        return self

    def append_data(self, data: Data):
        self.datas[data.imgpath] = data
    
    def remove(self, dataset):
        if type(dataset) is Dataset:
            for path in dataset.datas.keys():
                if path in self.datas.keys():
                    del self.datas[path]    
        return self

    def remove_by_path(self, path: str):
        if path in self.datas.keys():
            del self.datas[path]

    def copy(self):
        res = Dataset()
        res.datas = self.datas.copy()
        return res

    def filter(self, filter):
        return filter.apply(self)

    def get_data(self, path: str):
        return self.datas.get(path)
    
    def get_data_tags(self, path: str):
        data = self.get_data(path)
        if data:
            return data.tags
        else:
            return []
    
    def get_data_tagset(self, path: str):
        data = self.get_data(path)
        if data:
            return data.tagset
        else:
            return {}

    def get_tagset(self):
        tags = set()
        for data in self.datas.values():
            tags |= data.tagset
        return tags

    def get_taglist(self):
        return [t for t in self.get_tagset()]

