import abc
from lib.user import User
from lib.mapper import Mapper

# Interface implementations are expected to set self.name before calling the super constructor.
# Interface implementations should be idempotent.
class IService(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'synchronize') and 
                callable(subclass.synchronize))
                
    def __init__(self, config, mapper: Mapper, verbose_level: int, dry_run: bool):
        self.config = config[self.name]
        self.mapper = mapper
        self.verbose_level = verbose_level
        self.dry_run = dry_run

    def synchronize_all(self, users: list):
        pass

    def debug(self, message):
        if self.verbose_level >= 2:
            print("[DEBUG | " + self.name + "] " + message)

    def info(self, message):
        if self.verbose_level >= 1:
            print("[INFO | " + self.name + "] " + message)

    def error(self, message):
        print("[ERROR | " + self.name + "] " + message)