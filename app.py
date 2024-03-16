#!/bin/python3
import configparser, argparse, ldap, time
from lib import ISetProvider, IUpdateProvider
from providers.github import GitHubProvider
from providers.gitlab import GitLabProvider
from providers.mailman3 import Mailman3Provider
from providers.mattermost import MattermostProvider
from providers.redmine import RedmineProvider
from providers.studip import StudIPProvider

parser = argparse.ArgumentParser(description="Sync (primarly) user groups between ldap and other services.")
parser.add_argument("--verbose", "-v", help="Print debug information about what the script is doing. (-v only changes, -vv everything)", action="count", default=0)
parser.add_argument("--dry-run", "-d", help="Do not actaully sync anything. Just pretend to. Useful with --verbose", action="count", default=0)
parser.add_argument("--config", "-c", help="The location of the config file", default="app.conf")
parser.add_argument("--loop", "-l", help="Run sync tool continuosly till terminated and wait x seconds in between", default=0)
args = parser.parse_args()
verbose_level = args.verbose
DRY_RUN = args.dry_run > 0
def debug(provider, message):
    if verbose_level >= 2:
        print("[DEBUG | " + provider + "] " + message)
def info(provider, message):
    if verbose_level >= 1:
        print("[INFO | " + provider + "] " + message)
def error(provider, message):
    print("[ERROR | " + provider + "] " + message)

config = configparser.ConfigParser()
config.read(args.config)

ldap_connection = ldap.initialize(config["ldap"]["uri"])
ldap_connection.simple_bind_s(who=config["ldap"]["bind_dn"], cred=config["ldap"]["bind_pw"])

# Put all active providers into this array
providers = [GitHubProvider(config["github"]), GitLabProvider(config["gitlab"]), Mailman3Provider(config["mailman3"]), MattermostProvider(config["mattermost"]), RedmineProvider(config["redmine"]), StudIPProvider(config["studip"])]

attrs = [config["member"]["uid_attr"]]
for provider in providers:
    attrs.extend(provider.attrs)
attrs = set(attrs)

def sync():
    ldap_members = {}
    ldap_groups = {}
    def getLDAPMember(ldap_member):
        if ldap_member in ldap_members:
            return ldap_members[ldap_member]
        return None
    def getLDAPGroupMembers(ldap_group):
        if ldap_group in ldap_groups:
            return ldap_groups[ldap_group]
        return {"owners": [], "members": []}

    for member_data in ldap_connection.search_s(config["member"]["base"], ldap.SCOPE_SUBTREE, config["member"]["filter"], attrs):
        member_data = member_data[1]
        member = {}
        for attr in attrs:
            if attr in member_data:
                value = member_data[attr]
                member[attr] = value[0].decode() if len(value) == 1 else [x.decode() for x in value]
        ldap_members[member[config["member"]["uid_attr"]]] = member
    for group_data in ldap_connection.search_s(config["group"]["base"], ldap.SCOPE_SUBTREE, config["group"]["filter"], [config["group"]["uid_attr"], config["group"]["owner_attr"], config["group"]["member_attr"]]):
        group = group_data[1][config["group"]["uid_attr"]][0].decode()
        ldap_groups[group] = {"owners": [], "members": []}
        for index in ["owner", "member"]:
            if config["group"][index + "_attr"] in group_data[1]:
                for member in group_data[1][config["group"][index + "_attr"]]:
                    member = getLDAPMember(member.decode().split(",")[0].split("=")[1]) # This is probably some guessing. We try to extract the uid from the dn
                    if member is not None:
                        ldap_groups[group][index + "s"].append(member)

    for provider in providers:
        provider_name = provider.name
        ldap_members = {}
        names = {}
        processed_groups = []
        for group in provider.getGroups():
            group_name = group["name"]
            current_members = group["members"] # member ids for provider
            mapped_members = [] # member ids for provider
            group["owners"] = []
            for ldap_group in group["ldap_groups"]:
                if not ldap_group in ldap_members:
                    members = getLDAPGroupMembers(ldap_group)
                    ldap_members[ldap_group] = {}
                    for index in ["owners", "members"]:
                        ldap_members[ldap_group][index] = []
                        for ldap_member in members[index]:
                            member_id = provider.getMemberId(ldap_member)
                            if member_id is not None:
                                ldap_members[ldap_group][index].append(member_id)
                                names[member_id] = ldap_member[config["member"]["uid_attr"]]
                mapped_members.extend(ldap_members[ldap_group]["members"])
                group["owners"].extend(ldap_members[ldap_group]["owners"])
            group["mapped_members"] = mapped_members
            current_members = set(current_members)
            mapped_members = set(mapped_members)
            processed_members = set(provider.getProcessedMembers(processed_groups, group))
            if isinstance(provider, ISetProvider):
                if current_members == mapped_members:
                    debug(provider_name, "Group " + group_name + " is already up-to-date.")
                else:
                    if not DRY_RUN:
                        provider.setMembers(group, list(mapped_members))
                    info(provider_name, "Synced all members of group " + group_name + ".")
            elif isinstance(provider, IUpdateProvider):
                updated = False
                for member in current_members - mapped_members - processed_members:
                    if not DRY_RUN:
                        provider.removeMember(group, member)
                    if provider_name != "GitHub": # We dont remove GitHub users, dont spam logs.
                        info(provider_name, "Removed member " + str(member) + " from group " + group_name + ".")
                    updated = True
                for member in mapped_members - current_members - processed_members:
                    if not DRY_RUN:
                        provider.addMember(group, member)
                    info(provider_name, "Added member " + names[member] + "(" + str(member) + ") to group " + group_name + ".")
                    updated = True
                if not updated:
                    debug(provider_name, "Group " + group_name + " is already up-to-date.")
            processed_groups.append(group)

sync()
loop = int(args.loop)
while loop > 0:
    debug("Sleep", "Sleeping for " + str(args.loop) + " seconds.")
    time.sleep(loop)
    sync()