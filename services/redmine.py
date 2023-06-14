from lib.mapper import Mapper
from lib.service import IService
import requests, json

class RedmineService(IService):
    def __init__(self, config, mapper: Mapper, verbose_level: int, dry_run: bool):
        self.name = "redmine"
        super().__init__(config, mapper, verbose_level, dry_run)

    def synchronize_all(self, users: list):
        project_id, page_id = self.config["page"].split("/")
        url = self.config["url"] + "/projects/" + project_id + "/wiki/" + page_id + ".json"
        headers = {"X-Redmine-API-Key": self.config["api_token"], "Content-Type": "application/json"}
        page_content = requests.get(url, headers=headers).json()["wiki_page"]["text"]
        page_content_new = ""
        needs_update = False
        for line in page_content.split("\n"):
            if line.startswith("|"):
                line_data = line.split("|")
                title, persons = line_data[1].strip(), line_data[2].strip()
                mapping = self.mapper.get_mapping_by_attr("title", title)
                if mapping is not None:
                    group_users = [u for u in users if mapping.applies_to_user(u)]
                    group_users = sorted(group_users, key=lambda u: not u.uid in mapping.owners)
                    names = ", ".join([("**" + u[self.config["name_attr"]] + "**" if u.uid in mapping.owners else u[self.config["name_attr"]]) for u in group_users])
                    if names != persons:
                        needs_update = True
                        page_content_new += "| " + title + " | " + names + " |\n"
                        continue
            page_content_new += line + "\n"
        if needs_update and not self.dry_run:
            requests.put(url, headers=headers, data=json.dumps({"wiki_page":{"text":page_content_new}}))
            self.info("Updated redmine wiki page")