import mailmanclient
from lib import IUpdateProvider

class Mailman3Provider(IUpdateProvider):
    def __init__(self, config):
        super().__init__("Mailman3", config)
        self.attrs = [config["mail_attr"], self.config["name_attr"]]
        self.name_cache = {} # This is a ugly solution to a problem when adding a member
        self.client = mailmanclient.Client(self.config["url"], self.config["admin_user"], self.config["admin_password"])

    def getGroups(self):
        groups = self.getMappings()
        for group in groups:
            group["name"] = group["id"]
            group["members"] = []
            for member in self.client.get_list(group["id"]).members:
                group["members"].append(member.address.email)
            # We need this hardcoded, since quietschie is a regular account, but we don't want him added to the mitglieder list.
            if group["id"] == "mitglieder@fsinfo.fim.uni-passau.de":
                group["members"].append("admins+enton-quietschie@fsinfo.fim.uni-passau.de")
        return groups

    def getMemberId(self, member):
        mail_attr = self.config["mail_attr"]
        if not mail_attr in member:
            return None
        mail_addr = member[mail_attr]
        if isinstance(mail_addr, list):
            for email in mail_addr:
                if email.endswith('@fim.uni-passau.de'):
                    mail_addr = email
                    break
            if isinstance(mail_addr, list):
                mail_addr = mail_addr[0]
        self.name_cache[mail_addr] = member[self.config["name_attr"]]
        return mail_addr
    
    def getProcessedMembers(self, processedGroups, group):
        return []

    def addMember(self, group, memberId):
        mailingList = self.client.get_list(group["id"])
        mailingList.subscribe(memberId, self.name_cache[memberId] if memberId in self.name_cache else "", pre_verified=True, pre_confirmed=True, pre_approved=True)
        return True

    def removeMember(self, group, memberId):
        mailingList = self.client.get_list(group["id"])
        mailingList.unsubscribe(memberId, pre_confirmed=True, pre_approved=True)
        return True