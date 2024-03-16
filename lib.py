import json, requests
from base64 import b64encode

def api(method, url, auth = None, data = None, json = False):
    headers = {}
    if auth is not None:
        if isinstance(auth, list):
            headers = {"Authorization": "Basic " + b64encode((auth[0] + ":" + auth[1]).encode("utf-8")).decode()}
        else:
            headers = {"Authorization": "Bearer " + auth}
    headers["User-Agent"] = "LDAP-Sync/1.0"
    if method == "GET":
        return requests.get(url, headers=headers).json()
    elif method == "POST":
        if json:
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.post(url, data=data, headers=headers)
        if response.text != "":
            return response.json()
    elif method == "PUT":
        if json:
            response = requests.put(url, json=data, headers=headers)
        else:
            response = requests.put(url, data=data, headers=headers)
        if response.text != "":
            return response.json()
    elif method == "DELETE":
        if json:
            requests.delete(url, json=data, headers=headers)
        else:
            requests.delete(url, data=data, headers=headers)

# Interface implementations are expected to set self.name before calling the super constructor.
# Interface implementations should be idempotent.
class IProvider():      
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.attrs = []

    def getMappings(self):
        with open("mappings/" + self.name.lower() + ".json") as f:
            return json.load(f)

    def getGroups(self):
        pass

    def getMemberId(self, member):
        pass

    def getProcessedMembers(self, processedGroups, group):
        pass

class ISetProvider(IProvider):
    def __init__(self, name, config):
        super().__init__(name, config)

    def getProcessedMembers(self, processedGroups, group):
        return []

    def setMembers(self, group, memberIds):
        pass

class IUpdateProvider(IProvider):
    def __init__(self, name, config):
        super().__init__(name, config)

    def addMember(self, group, memberId):
        pass

    def removeMember(self, group, memberId):
        pass