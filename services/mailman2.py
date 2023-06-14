from lib.mapper import Mapper
from lib.service import IService
from lib.user import User
import urllib.parse, requests, re
import lxml.html as lh

class Mailman2Service(IService):
    def __init__(self, config, mapper: Mapper, verbose_level: int, dry_run: bool):
        self.name = "mailman2"
        super().__init__(config, mapper, verbose_level, dry_run)
        self.headers = {}

    def list(self, list_id: str):
        payload = "adminpw=" + urllib.parse.quote_plus(self.config["adminpw"]) + "&adminlogin=Let%20me%20in%20..."
        html = requests.post(self.config["url"] + "/admin/" + list_id + "/members/list", data=payload, headers=self.headers).text
        members = []
        addresses = []
        for member_raw in lh.fromstring(html).cssselect("form center table tr:not(:nth-child(2)) td:nth-child(2)"):
            email = member_raw.getchildren()[0].text_content()
            addresses.append(email)
            name = re.search("(.+) (.+) \((.+)\)", member_raw.getchildren()[2].value)
            if name is not None:
                members.append({
                    "uid": name.group(3),
                    "first_name": name.group(1),
                    "last_name": name.group(2),
                    "email": email
                })
        return members, addresses

    def add(self, list_id: str, user):
        payload = "adminpw=" + urllib.parse.quote_plus(self.config["adminpw"]) + "&adminlogin=Let%20me%20in%20..."
        payload += "&subscribe_or_invite=0&send_welcome_msg_to_this_batch=" + self.config["notify_user"]
        payload += "&send_notofications_to_list_owner=" + self.config["notify_owner"]
        payload += "&subscribees=" + urllib.parse.quote_plus(user["first_name"] + " " + user["last_name"] + " (" + user["uid"] + ") <" + user["email"] + ">")
        requests.post(self.config["url"] + "/admin/" + list_id + "/members/add", data=payload, headers=self.headers)
        self.info("Add " + user["uid"] + " to list " + list_id)

    def edit(self, list_id: str, member):
        payload = "adminpw=" + urllib.parse.quote_plus(self.config["adminpw"]) + "&adminlogin=Let%20me%20in%20..."
        payload += "&user=" + urllib.parse.quote_plus(member["email"])
        email = urllib.parse.quote_plus(urllib.parse.quote_plus(member["email"]))
        payload += "&" + email + "_realname=" + urllib.parse.quote_plus(member["first_name"] + " " + member["last_name"] + " (" + member["uid"] + ")")
        payload += "&" + email + "_nodupes=on"
        payload += "&" + email + "_plain=on"
        payload += "&" + email + "_language=en"
        payload += "&setmemberopts_btn=Submit%20Your%20Changes"
        requests.post(self.config["url"] + "/admin/" + list_id + "/members/list", data=payload, headers=self.headers)
        self.info("Edit " + member["uid"] + "'s membership in list " + list_id)

    def remove(self, list_id: str, email: str, uid: str):
        payload = "adminpw=" + urllib.parse.quote_plus(self.config["adminpw"]) + "&adminlogin=Let%20me%20in..."
        payload += "&" + urllib.parse.quote_plus(urllib.parse.quote_plus(email)) + "_unsub=off"
        payload += "&user=" + urllib.parse.quote_plus(email)
        payload += "&setmemberopts_btn=Submit%20Your%20Changes"
        requests.post(self.config["url"] + "/admin/" + list_id + "/members/list", data=payload, headers=self.headers)
        self.info("Remove " + uid + " from list " + list_id)

    def synchronize_all(self, users: list):
        for mapping in self.mapper.get_mappings():
            current_members, current_addresses = self.list(mapping["list_id"])
            expected_members = [u for u in users if mapping.applies_to_user(u)]
            for member in current_members:
                if not member["uid"] in [m["uid"] for m in expected_members]:
                    self.remove(mapping["list_id"], member["email"], member["uid"])
            for member in expected_members:
                membership = [m for m in current_members if m["uid"] == member["uid"]]
                if len(membership) == 0:
                    if member["email"] in current_addresses:
                        self.edit(mapping["list_id"], member)
                    else:
                        self.add(mapping["list_id"], member)
                elif member["first_name"] != membership[0]["first_name"] or member["last_name"] != membership[0]["last_name"]:
                    self.edit(mapping["list_id"], member)
                elif member["email"] != membership[0]["email"]:
                    self.remove(mapping["list_id"], membership["email"])
                    self.add(mapping["list_id"], member)