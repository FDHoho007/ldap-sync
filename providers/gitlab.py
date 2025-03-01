import lib, re
from lib import IUpdateProvider
from urllib.parse import quote_plus

class GitLabProvider(IUpdateProvider):
    def __init__(self, config):
        super().__init__("GitLab", config)
        self.attrs = [config["username_attr"]]
        self.gitlab_uid_cache = {} # The uid cache could probably even be stored on disk, since they won't change

    def api(self, method, url, data = None):
        return lib.api(method, self.config["url"] + url, self.config["api_token"], data)
    
    def api_group(self, group, method, url, data = None):
        return self.api(method, "/" + ("projects" if group["is_project"] else "groups") + "/" + quote_plus(group["id"]) + "/members" + url, data)

    def getGroups(self):
        groups = self.getMappings()
        for group in groups:
            group["name"] = group["id"]
            group["members"] = []
            for m in self.api_group(group, "GET", "?per_page=100"):
                if m["access_level"] == group["access_level"] and not re.match("^group_\d+_bot_[a-z0-9]+$", m["username"]):
                    group["members"].append(m["id"])
        return groups

    def getMemberId(self, member):
        username_attr = self.config["username_attr"]
        if not username_attr in member:
            return None
        username = member[username_attr]
        if username not in self.gitlab_uid_cache:
            data = self.api("GET", "/users?username=" + username)
            if len(data) == 0:
                return None
            self.gitlab_uid_cache[username] = data[0]["id"]
        return self.gitlab_uid_cache[username]
    
    def getProcessedMembers(self, processedGroups, group):
        processedMembers = []
        for processedGroup in processedGroups:
            if processedGroup["id"] == group["id"] or (group["id"].startswith(processedGroup["id"] + "/") and processedGroup["access_level"] >= group["access_level"]):
                processedMembers.extend(processedGroup["mapped_members"])
        return processedMembers

    def addMember(self, group, memberId):
        self.api_group(group, "POST", "", {"user_id": str(memberId), "access_level": str(group["access_level"])})
        return True

    def removeMember(self, group, memberId):
        self.api_group(group, "DELETE", "/" + str(memberId))
        return True