from lib.mapper import Mapper
from lib.service import IService
import urllib.parse
import requests

class GitLabService(IService):
    def __init__(self, config, mapper: Mapper, verbose_level: int, dry_run: bool):
        self.name = "gitlab"
        super().__init__(config, mapper, verbose_level, dry_run)
        self.members = {}
        for mapping in self.mapper.get_mappings():
            id, is_project = self.mapping_id(mapping)
            self.members[id] = {}
            for membership in self.get_memberships(id, is_project):
                self.members[id][membership["id"]] = membership["access_level"]

    def api(self, method, url, data = None):
        final_url = self.config["url"] + url
        if method == "GET" or not self.dry_run:
            self.debug(method + " " + final_url + " " + (data if data is not None else ""))
            headers = {"Authorization": "Bearer " + self.config["api_token"]}
            if method == "GET":
                return requests.get(final_url, headers=headers).json()
            elif method == "POST":
                return requests.post(final_url, data=data, headers=headers).json()
            elif method == "PUT":
                return requests.put(final_url, data=data, headers=headers).json()
            elif method == "DELETE":
                requests.delete(final_url, headers=headers).json()

    def get_user_id(self, username: str):
        data = self.api("GET", "/users?username=" + username)
        if len(data) == 0:
            return None
        else:
            return data[0]["id"]

    def get_memberships(self, id: str, is_project: bool):
        url = "/" + ("projects" if is_project else "groups")
        url += "/" + urllib.parse.quote_plus(id) + "/members"
        return self.api("GET",  url)
    
    def add_membership(self, id: str, user_id: int, access_level: int, is_project: bool):
        url = "/" + ("projects" if is_project else "groups")
        url += "/" + urllib.parse.quote_plus(id) + "/members"
        self.api("POST",  url, "user_id=" + str(user_id) + "&access_level=" + str(access_level))

    def edit_membership(self, id: str, user_id: int, access_level: int, is_project: bool):
        url = "/" + ("projects" if is_project else "groups")
        url += "/" + urllib.parse.quote_plus(id) + "/members"
        url += "/" + str(user_id) + "?access_level=" + str(access_level)
        self.api("POST",  url)

    def remove_membership(self, id: str, user_id: int, is_project: bool):
        url = "/" + ("projects" if is_project else "groups")
        url += "/" + urllib.parse.quote_plus(id) + "/members"
        url += "/" + str(user_id)
        self.api("DELETE",  url)

    def mapping_id(self, mapping: object):
        if "gitlab_group" in mapping:
            return mapping["gitlab_group"], False
        elif "gitlab_project" in mapping:
            return mapping["gitlab_project"], True

    def synchronize_all(self, users: list):
        for user in users:
            user_id = self.get_user_id(user[self.config["uid_attr"]])
            if user_id is None:
                self.error("Failed to sync user " + user[self.config["uid_attr"]] + " because we couldn't find this account on " + self.config["url"])
                return
            self.debug("Sync GitLab User " + user[self.config["uid_attr"]] + " on " + self.config["url"])
            for mapping in self.mapper.get_mappings():
                matches = mapping.applies_to_user(user)
                id, is_project = self.mapping_id(mapping)
                access_level = (self.members[id][user_id] if user_id in self.members[id] else 0)
                if matches:
                    if access_level == 0:
                        self.add_membership(id, user_id, mapping["access_level"], is_project)
                        self.info("Added " + user.uid + " to group/project " + id)
                    elif access_level != mapping["access_level"]:
                        self.edit_membership(id, user_id, mapping["access_level"], is_project)
                        self.info("Changed role for " + user.uid + " in group/project " + id)
                else:
                    if access_level != 0:
                        self.remove_membership(id, user_id, is_project)
                        self.info("Removed " + user.uid + " from group/project " + id)