import json, requests
from base64 import b64encode

def api(method, url, auth = None, data = None):
    #app.debug(method + " " + final_url + " " + (data if data is not None else ""))
    headers = {}
    if auth is not None:
        if isinstance(auth, list):
            headers = {"Authorization": "Basic " + b64encode((auth[0] + ":" + auth[1]).encode("utf-8")).decode()}
        else:
            headers = {"Authorization": "Bearer " + auth}
    if method == "GET":
        return requests.get(url, headers=headers).json()
    elif method == "POST":
        if isinstance(data, str):
            return requests.post(url, data=data, headers=headers).json()
        else:
            return requests.post(url, json=data, headers=headers).json()
    elif method == "PUT":
        if isinstance(data, str):
            return requests.put(url, data=data, headers=headers).json()
        else:
            return requests.put(url, json=data, headers=headers).json()
    elif method == "DELETE":
        requests.delete(url, headers=headers).json()

# Interface implementations are expected to set self.name before calling the super constructor.
# Interface implementations should be idempotent.
class IProvider():      
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.attrs = []

    def error(self, message):
        print("[ERROR | " + self.name + "] " + message)

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