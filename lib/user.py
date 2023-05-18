class User:

    def __init__(self, uid: str, first_name: str, last_name: str, display_name: str, email: str, groups: list):
        self.uid = uid
        self.first_name = first_name
        self.last_name = last_name
        self.display_name = display_name
        self.email = email
        self.groups = groups
    
    def __delitem__(self, key):
        self.__delattr__(key)

    def __getitem__(self, key):
        return self.__getattribute__(key)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def is_in_group(self, group: str) -> bool:
        return group in self.groups