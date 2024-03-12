# This is only to update members of an institute
import re, requests, lxml.html, urllib.parse
from lib import IUpdateProvider

class StudIPProvider(IUpdateProvider):
    def __init__(self, config):
        super().__init__("StudIP", config)
        self.attrs = [config["username_attr"]]
        self.seminarSession = None

    def api(self, method, url, data = None):
        if self.seminarSession is None:
            self.seminarSession = self.getSession()
        headers = {"Cookie": "Seminar_Session=" + self.seminarSession}
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
                doc = lxml.html.document_fromstring(self.api("GET", "/dispatch.php/institute/members?cid=" + group["id"]).text)
                for tbody in doc.cssselect("#list_institute_members tbody"):
                    id = None
                    users = []
                    for tr in tbody.cssselect("tr"):
                        if id is None:
                            a = tr.cssselect("th:last-child a")
                            if len(a) == 0:
                                break
                            id = re.search(r"&group_id=([a-z0-9]+)", a[0].attrib["href"]).group(1)
                        else:
                            users.append(re.search(r"&username=([a-z0-9]+)", tr.cssselect("td:first-child a")[0].attrib["href"]).group(1))
                    if id is not None:
                        members[group["id"]][id] = users
            group["members"] = members[group["id"]][group["role_id"]] if group["role_id"] in members[group["id"]] else []
        return groups

    def getMemberId(self, member):
        username_attr = self.config["username_attr"]
        if not username_attr in member:
            return None
        return member[username_attr]

    def getProcessedMembers(self, processedGroups, group):
        processedMembers = []
        for processedGroup in processedGroups:
            if processedGroup["id"] == group["id"]:
                processedMembers.extend(processedGroup["mapped_members"])
        return processedMembers

    def getTicket(self, cid, username):
        doc = lxml.html.document_fromstring(self.api("GET", "/dispatch.php/settings/statusgruppen?cid=" + cid + "&username=" + username).text)
        return (doc.cssselect("input[name=studip_ticket]")[0].value, doc.cssselect("input[name=security_token]")[0].value)
    
    def addMember(self, group, memberId):
        ticket = self.getTicket(group["id"], memberId)
        self.api("POST", "/dispatch.php/settings/statusgruppen/assign?cid=" + group["id"] + "&username=" + memberId, "studip_ticket=" + ticket[0] + "&security_token=" + urllib.parse.quote(ticket[1]) + "&role_id=" + group["role_id"] + "&assign")

    def removeMember(self, group, memberId):
        ticket = self.getTicket(group["id"], memberId)
        self.api("POST", "/dispatch.php/settings/statusgruppen/delete/" + group["role_id"] + "/1?cid=" + group["id"] + "&username=" + memberId, "studip_ticket=" + ticket[0] + "&security_token=" + urllib.parse.quote(ticket[1]) + "&cid=" + group["id"] + "&username=" + memberId + "&yes")