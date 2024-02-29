import lib
from lib import IUpdateProvider

class Mailman3Provider(IUpdateProvider):
    def __init__(self, config):
        super().__init__("Mailman3", config)
        self.attrs = [config["mail_attr"], self.config["name_attr"]]
        self.name_cache = {} # This is a ugly solution to a problem when adding a member

    def api(self, method, url, data = None):
        return lib.api(method, self.config["url"] + url, [self.config["admin_user"], self.config["admin_password"]], data)

    def getGroups(self):
        groups = self.getMappings()
        for group in groups:
            group["name"] = group["id"]
            group["members"] = []
            subscriptions = self.api("POST", "/members/find", {"list_id": group["id"].replace("@", "."), "role": "member"})
            if subscriptions["total_size"] > 0:
                for subscription in subscriptions["entries"]:
                    group["members"].append(subscription["email"])
        return groups

    def getMemberId(self, member):
        mail_attr = self.config["mail_attr"]
        if not mail_attr in member:
            return None
        self.name_cache[member[mail_attr]] = member[self.config["name_attr"]]
        return member[mail_attr]
    
    def getProcessedMembers(self, processedGroups, group):
        return []

    def addMember(self, group, memberId):
        self.api("POST", "/members", {
            "list_id": group["id"].replace("@", "."),
            "subscriber": memberId,
            # We don't know the name, only the email. Hence we take the name that was converted to this email before.
            "display_name": self.name_cache[memberId] if memberId in self.name_cache else "",
            "pre_verified": True,
            "pre_confirmed": True,
            "pre_approved": True,
            "send_welcome_message": True
        })

    def removeMember(self, group, memberId):
        self.api("DELETE", "/lists/" + group["id"].replace("@", ".") + "/roster/member", {"emails": [memberId]})