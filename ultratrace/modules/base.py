from abc import ABC, abstractmethod

class Module(ABC):

    @abstractmethod
    def update(*args, **kwargs):
        pass

    @abstractmethod
    def reset(*args, **kwargs):
        pass

    @abstractmethod
    def grid(*args, **kwargs):
        pass

    @abstractmethod
    def grid_remove(*args, **kwargs):
        pass

