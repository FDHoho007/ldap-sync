import lib
from lib import IUpdateProvider

class GitHubProvider(IUpdateProvider):
    def __init__(self, config):
        super().__init__("GitHub", config)
        self.attrs = [config["messenger_attr"]]

    def api(self, method, url, data = None, json = False):
        return lib.api(method, "https://api.github.com" + url, self.config["api_token"], data, json)
    
    def api_group(self, group, method, url, data = None):
        return self.api(method, "/orgs/" + str(group["id"]) + url, data, True)

    def getGroups(self):
        groups = self.getMappings()
        for group in groups:
            group["members"] = []
            for m in self.api_group(group, "GET", "/members?per_page=100&role=" + group["role"]):
                if m["login"] != self.config["bot_user_login"]:
                    group["members"].append(m["login"])
            invRole = "direct_member" if group["role"] == "member" else group["role"]
            for m in self.api_group(group, "GET", "/invitations?per_page=100&role=" + invRole):
                group["members"].append(m["login"])
        return groups

    def getMemberId(self, member):
        messenger_attr = self.config["messenger_attr"]
        if not messenger_attr in member:
            return None
        for messenger in member[messenger_attr] if isinstance(member[messenger_attr], list) else [member[messenger_attr]]:
            if messenger.startswith("GitHub:"):
                return messenger[7:]
        return None
    
    def getProcessedMembers(self, processedGroups, group):
        processedMembers = []
        for processedGroup in processedGroups:
            if processedGroup["id"] == group["id"]:
                processedMembers.extend(processedGroup["mapped_members"])
        return processedMembers

    def addMember(self, group, memberId):
        self.api_group(group, "PUT", "/memberships/" + memberId, {"role": group["role"]})
        return True

    def removeMember(self, group, memberId):
        # GitHub users will be removed manually as decided by the admin team
        # self.api_group(group, "DELETE", "/memberships/" + memberId)
        return False