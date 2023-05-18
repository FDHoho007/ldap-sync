import json, ldap
from lib.user import User

class Mapping:
    def __init__(self, data: object, config, ldap_connection):
        self.data = data
        if "ldap_groups" in data:
            self.ldap_groups = data["ldap_groups"]
            self.owners = []
            for ldap_group in self.ldap_groups:
                query = ldap_connection.search_s(config["group"]["base"], ldap.SCOPE_SUBTREE, "(" + config["group"]["uid_attr"] + "=" + ldap_group + ")", ["owner"])[0][1]
                if "owner" in query:
                    uid = query["owner"][0].decode()
                    if uid.startswith(config["user"]["uid_attr"]) and uid.endswith(config["user"]["base"]):
                         uid = uid[len(config["user"]["uid_attr"])+1:len(uid) - (len(config["user"]["base"]) + 1)]
                    self.owners.append(uid)


    def __contains__(self, key):
        return self.data.__contains__(key)

    def __getitem__(self, key):
        return self.data.__getitem__(key)

    def applies_to_user(self, user: User) -> bool:
        for ldap_group in self.ldap_groups:
            if user.is_in_group(ldap_group):
                return True
        return False

class Mapper:
    def __init__(self, mappings: list, config, ldap_connection):
        self.mappings = []
        for mapping in mappings:
            self.mappings.append(Mapping(mapping, config, ldap_connection))

    @staticmethod
    def from_file(file: str, config, ldap_connection):
        f = open("mappings/" + file + ".json")
        data = json.load(f)
        f.close()
        return Mapper(data, config, ldap_connection)
    
    def get_mappings(self) -> list:
        return self.mappings
    
    def get_mapping_by_attr(self, attr: str, value: str) -> Mapping:
        for mapping in self.mappings:
            if attr in mapping and mapping[attr] == value:
                return mapping
        return None