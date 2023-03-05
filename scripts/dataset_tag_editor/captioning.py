import modules.shared as shared

from .interrogator import Interrogator
from .interrogators import GITLargeCaptioning
    

class Captioning(Interrogator):
    def start(self):
        pass
    def stop(self):
        pass
    def predict(self, image):
        raise NotImplementedError()
    def name(self):
        raise NotImplementedError()


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
    def __init__(self):
        self.interrogator = GITLargeCaptioning()
    def start(self):
         self.interrogator.load()
    
    def stop(self):
         self.interrogator.unload()
    
    def predict(self, image):
        tags = self.interrogator.apply(image).split(',')
        return [t for t in tags if t]
    
    def name(self):
        return 'GIT-large-COCO'