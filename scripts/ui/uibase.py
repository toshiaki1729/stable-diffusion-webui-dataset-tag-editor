class Singleton(object):
    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

class UIBase(Singleton):
    def create_ui(self, *args, **kwargs):
        raise NotImplementedError()
    def set_callbacks(self, *args, **kwargs):
        raise NotImplementedError()
    def func_to_set_value(self, name, type=None):
        def func(value):
            if type is not None:
                value = type(value)
            setattr(self, name, value)
            return value
        return func