#!/bin/python3
import configparser, argparse, ldap
from lib.user import User
from lib.mapper import Mapper

parser = argparse.ArgumentParser(description="Sync (primarly) user groups between ldap and other services.")
parser.add_argument("--verbose", "-v", help="Print debug information about what the script is doing. (-v only changes, -vv everything)", action="count", default=0)
parser.add_argument("--dry-run", "-d", help="Do not actaully sync anything. Just pretend to. Useful with --verbose", action="count", default=0)
parser.add_argument("--config", "-c", help="The location of the config file", default="app.conf")
args = parser.parse_args()
DRY_RUN = args.dry_run

config = configparser.ConfigParser()
config.read(args.config)

ldap_connection = ldap.initialize(config["ldap"]["uri"])
ldap_connection.simple_bind_s(who=config["ldap"]["bind_dn"], cred=config["ldap"]["bind_pw"])

# Put all active services into this array
services = []

def get_attr(user_data, attr):
    return user_data[config["user"][attr + "_attr"]][0].decode()

def get_group(group_dn):
    if not group_dn.endswith(config["group"]["base"]):
        return None
    group_dn = group_dn[0:len(group_dn) - (len(config["group"]["base"]) + 1)]
    if not group_dn.startswith(config["group"]["uid_attr"] + "="):
        return None
    group_dn = group_dn[len(config["group"]["uid_attr"]) + 1:]
    if "=" in group_dn or "," in group_dn:
        return None    
    return group_dn

attrs = []
for attr in ["uid", "first_name", "last_name", "display_name", "email", "memberof"]:
    attrs.append(config["user"][attr + "_attr"])

users = []
for user_data in ldap_connection.search_s(config["user"]["base"], ldap.SCOPE_SUBTREE, config["user"]["filter"], attrs):
    user_data = user_data[1]
    groups = []
    if config["user"]["memberof_attr"] in user_data:
        for group in user_data[config["user"]["memberof_attr"]]:
            group = get_group(group.decode())
            if group is not None:
                groups.append(group)
    user = User(uid=get_attr(user_data, "uid"),
                first_name=get_attr(user_data, "first_name"),
                last_name=get_attr(user_data, "last_name"),
                display_name=get_attr(user_data, "display_name"),
                email=get_attr(user_data, "email"),
                groups=groups)
    users.append(user)
    for service in services:
        if not service.enforce:
            service.synchronize(user)

for service in services:
    if service.enforce:
        service.synchronize_all(users)