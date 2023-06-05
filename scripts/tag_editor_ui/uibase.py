from scripts.singleton import Singleton

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