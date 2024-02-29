import requests, json
from lib import ISetProvider

class RedmineProvider(ISetProvider):
    def __init__(self, config):
        super().__init__("Redmine", config)
        self.attrs = [config["name_attr"]]
        self.headers = {"X-Redmine-API-Key": self.config["api_token"], "Content-Type": "application/json"}
        self.url = self.config["url"] + ".json"

    def getPageContent(self):
        return requests.get(self.url, headers=self.headers).json()["wiki_page"]["text"]

    def getGroups(self):
        groupMembers = {}
        for line in self.getPageContent().split("\n"):
            if line.startswith("|"):
                line_data = line.split("|")
                title, persons = line_data[1].strip(), line_data[2].strip()
                groupMembers[title] = [x.replace("**", "") for x in persons.split(", ")]
        groups = self.getMappings()
        for group in groups:
            group["name"] = group["id"]
            group["members"] = groupMembers[group["id"]] if group["id"] in groupMembers else []
        return groups

    def getMemberId(self, member):
        name_attr = self.config["name_attr"]
        if not name_attr in member:
            return None
        return member[name_attr]

    def setMembers(self, group, memberIds):
        memberIds = sorted(memberIds, key=lambda member: not member in group["owners"])
        page_content_new = ""
        for line in self.getPageContent().split("\n"):
            if line.startswith("|"):
                line_data = line.split("|")
                title = line_data[1].strip()
                if title == group["id"]:
                    page_content_new += "| " + title + " | " + ", ".join([("**" + member + "**" if member in group["owners"] else member) for member in memberIds]) + " |\n"
                    continue
            page_content_new += line + "\n"
        requests.put(self.url, headers=self.headers, data=json.dumps({"wiki_page": {"text": page_content_new, "comments": "Update Aufgabenbereich " + group["id"]}}))