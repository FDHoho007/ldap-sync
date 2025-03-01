import lib
from lib import IUpdateProvider

class IMattermostProvider(IUpdateProvider):
    def __init__(self, name, config, url_part):
        super().__init__(name, config)
        self.attrs = [config["username_attr"]]
        self.mattermost_uid_cache = {} # The uid cache could probably even be stored on disk, since they won't change
        self.url_part = url_part

    def api(self, method, url, data = None):
        return lib.api(method, self.config["url"] + url, self.config["api_token"], data, True)
    
    def api_group(self, group, method, url, data = None):
        return self.api(method, "/" + self.url_part + "/" + group["id"] + "/members" + url, data)

    def getGroups(self):
        groups = self.getMappings()
        for group in groups:
            group["members"] = []
            for m in self.api_group(group, "GET", "?per_page=100"):
                if m["roles"] == group["roles"] and m["user_id"] != self.config["bot_user_id"]:
                    group["members"].append(m["user_id"])
        return groups

    def getMemberId(self, member):
        username_attr = self.config["username_attr"]
        if not username_attr in member:
            return None
        username = member[username_attr]
        if username not in self.mattermost_uid_cache:
            data = self.api("POST", "/users/usernames", [username])
            if len(data) == 0:
                return None
            self.mattermost_uid_cache[username] = data[0]["id"]
        return self.mattermost_uid_cache[username]

    def getProcessedMembers(self, processedGroups, group):
        processedMembers = []
        for processedGroup in processedGroups:
            if processedGroup["id"] == group["id"]:
                processedMembers.extend(processedGroup["mapped_members"])
        return processedMembers

    def addMember(self, group, memberId):
        user_data = {"user_id": memberId}
        if self.url_part == "teams":
            user_data["team_id"] = group["id"]
        self.api_group(group, "POST", "", user_data)
        self.api_group(group, "PUT", "/" + memberId + "/roles", {"roles": group["roles"]})
        return True

    def removeMember(self, group, memberId):
        self.api_group(group, "DELETE", "/" + memberId)
        return True