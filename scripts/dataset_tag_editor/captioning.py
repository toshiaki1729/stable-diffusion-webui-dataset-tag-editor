import modules.shared as shared

from scripts.dynamic_import import dynamic_import
git_large_captioning = dynamic_import('scripts/dataset_tag_editor/interrogators/git_large_captioning.py')

class Captioning:
    def __enter__(self):
        self.start()
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()
        pass
    def start(self):
        pass
    def stop(self):
        pass
    def predict(self, image):
        raise NotImplementedError
    def name(self):
        raise NotImplementedError


class BLIP(Captioning):
    def start(self):
        shared.interrogator.load()
    
    def stop(self):
        shared.interrogator.unload()

    def predict(self, image):
        tags = shared.interrogator.generate_caption(image).split(',')
        return [t for t in tags if t]
    
    def name(self):
        return 'BLIP'


class GITLarge(Captioning):
    def start(self):
        git_large_captioning.instance.load()
    
    def stop(self):
        git_large_captioning.instance.unload()
    
    def predict(self, image):
        tags = git_large_captioning.instance.apply(image).split(',')
        return [t for t in tags if t]
    
    def name(self):
        return 'GIT-large-COCO'