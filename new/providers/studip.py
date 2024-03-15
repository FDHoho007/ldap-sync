# This is only to update members of an institute
import re, requests, lxml.html, urllib.parse, time, os
from lib import IUpdateProvider

class StudIPProvider(IUpdateProvider):
    def __init__(self, config):
        super().__init__("StudIP", config)
        self.attrs = [config["username_attr"]]
        self.seminarSession = None
        self.lastSessionUpdate = 0
        self.studip_uid_cache = {}

    def api(self, method, url, data = None):
        if self.seminarSession is None or self.lastSessionUpdate + 6*60*60 < time.time():
            self.seminarSession = self.getSession()
            self.lastSessionUpdate = time.time()
        headers = {"Cookie": "Seminar_Session=" + self.seminarSession, "Content-Type": "application/x-www-form-urlencoded"}
        url = self.config["url"] + url
        if method == "GET":
            return requests.get(url, headers=headers)
        elif method == "POST":
            return requests.post(url, data=data, headers=headers)
        
    def getSession(self):
        loginPage = requests.get(self.config["url"] + "/index.php?again=yes&adminlogin=1")
        session = None
        for cookie in loginPage.headers["Set-Cookie"].split("; "):
            if cookie.startswith("Seminar_Session="):
                session = cookie[16:]
        doc = lxml.html.document_fromstring(loginPage.text)
        ticket = doc.cssselect("input[name=login_ticket]")[0].value
        token = doc.cssselect("input[name=security_token]")[0].value
        response = requests.post(self.config["url"] + "/index.php?again=yes&adminlogin=1", allow_redirects=False, data={"loginname": self.config["username"], "password": self.config["password"], "security_token": urllib.parse.quote(token), "login_ticket": ticket, "resolution": "1920x1080", "device_pixel_ratio": "1", "Login": "1"}, headers={"Cookie": "Seminar_Session=" + session})
        for cookie in response.headers["Set-Cookie"].split("; "):
            if cookie.startswith("Seminar_Session="):
                session = cookie[16:]
        return session

    def getGroups(self):
        groups = self.getMappings()
        members = {}
        for group in groups:
            if not group["id"] in members:
                members[group["id"]] = {}
                parser = lxml.etree.HTMLParser(recover=True)
                doc = lxml.etree.fromstring(self.api("GET", "/dispatch.php/admin/statusgroups?cid=" + group["id"]).text, parser=parser)
                for table in doc.cssselect("#layout_content table"):
                    members[group["id"]][table.attrib["id"]] = []
                    for user in table.cssselect("tbody tr"):
                        members[group["id"]][table.attrib["id"]].append(user.attrib["data-userid"])
            group["members"] = members[group["id"]][group["role_id"]] if group["role_id"] in members[group["id"]] else []
        return groups

    def getMemberId(self, member):
        username_attr = self.config["username_attr"]
        if not username_attr in member:
            return None
        username = member[username_attr]
        if username not in self.studip_uid_cache:
            self.api("GET", "/dispatch.php/messages/write")
            data = self.api("GET", "/dispatch.php/multipersonsearch/ajax_search/add_adressees?s=" + username)
            for user in data.json():
                if re.fullmatch(r"^.+ \(" + username + "\)$", user["text"]):
                    self.studip_uid_cache[username] = user["user_id"]
                    return user["user_id"]
        else:
            return self.studip_uid_cache[username]

    def getProcessedMembers(self, processedGroups, group):
        processedMembers = []
        for processedGroup in processedGroups:
            if processedGroup["id"] == group["id"]:
                processedMembers.extend(processedGroup["mapped_members"])
        return processedMembers

    def getSecurityToken(self, cid):
        doc = lxml.html.document_fromstring(self.api("GET", "/dispatch.php/admin/statusgroups?cid=" + cid).text)
        for script in doc.cssselect("script"):
            match = re.search(r"name:\s*'security_token',\s*value:\s*'([^']+)'", script.text_content())
            if match:
                return match.group(1)
    
    def addMember(self, group, memberId):
        securityToken = self.getSecurityToken(group["id"])
        name = "add_statusgroup" + group["role_id"]
        os.system("curl --location --request POST '" + self.config["url"] + "/dispatch.php/multipersonsearch/js_form_exec/?cid=" + group["id"] + "&name=" + name + "' --header 'Cookie: Seminar_Session=" + self.seminarSession + "' --header 'Content-Type: application/x-www-form-urlencoded' --data-raw '" + name + "_selectbox[]=" + memberId + "&security_token=" + urllib.parse.quote(securityToken) + "&confirm=' > /dev/null")
        #print(self.seminarSession)
        #print("/dispatch.php/multipersonsearch/js_form_exec/?cid=" + group["id"] + "&name=" + name)
        #print(name + "_selectbox[]=" + memberId + "&security_token=" + urllib.parse.quote(securityToken) + "&confirm=")
        #print({name + "_selectbox": [memberId], "security_token": securityToken, "confirm": ""})
        #self.api("POST", "/dispatch.php/multipersonsearch/js_form_exec/?cid=" + group["id"] + "&name=" + name, {name + "_selectbox[]": [memberId], "security_token": securityToken, "confirm": ""})
        #self.api("POST", "/dispatch.php/multipersonsearch/js_form_exec/?cid=" + group["id"] + "&name=" + name, name + "_selectbox[]=" + memberId + "&security_token=" + urllib.parse.quote(securityToken) + "&confirm=")

    def removeMember(self, group, memberId):
        securityToken = self.getSecurityToken(group["id"])
        self.api("POST", "/dispatch.php/admin/statusgroups/delete/" + group["role_id"] + "/" + memberId + "?cid=" + group["id"], {"security_token": securityToken, "confirm": ""})