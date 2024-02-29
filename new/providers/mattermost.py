# We need a Mattermost bot account for this one
import lib
from lib import IUpdateProvider

class MattermostProvider(IUpdateProvider):
    def __init__(self, config):
        super().__init__("Mattermost", config)
        self.attrs = [config["username_attr"]]
        self.mattermost_uid_cache = {} # Th uid cache could probably even be stored on disk, since they won't change

    def api(self, method, url, data = None):
        return lib.api(method, self.config["url"] + url, self.config["api_token"], data)
    
    def api_group(self, group, method, url, data = None):
        return self.api(method, "/teams/" + str(group["id"]) + "/members" + url, data)

    def getGroups(self):
        groups = self.getMappings()
        for group in groups:
            group["members"] = []
            for m in self.api_group(group, "GET", "?per_page=100"):
                group["members"].append(m["id"])
        return groups

    def getMemberId(self, member):
        username_attr = self.config["username_attr"]
        if not username_attr in member:
            return None
        username = member[username_attr]
        if username not in self.mattermost_uid_cache:
            data = self.api("GET", "/users/usernames", [username])
            if len(data) == 0:
                return None
            self.mattermost_uid_cache[username] = data[0]["id"]
        return self.mattermost_uid_cache[username]

    def addMember(self, group, memberId):
        self.api_group(group, "POST", "", "user_id=" + str(memberId) + "&team_id=" + str(group["id"]))

    def removeMember(self, group, memberId):
        self.api_group(group, "DELETE", "/" + str(memberId))