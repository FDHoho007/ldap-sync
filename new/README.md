# LDAP Sync

This tool is inteded to sync group memberships from a ldap server to serveral different external providers.
To use this tool, you first need to decide which providers you want to synchronize to.
These need to be defined in the `app.py` in the `providers` array and given their section of the config.
Next you need to create and fill out the app.conf. The different configuration options will be explained later or in the respective provider section.
All thats left is to define mappings for each provider in `mappings/<provider>.json`. The mapping scheme is defined in the respective provider section. A mapping file always consists of an array of mappings. It is generally advised to define higher privileged mappings before others for the same provider group. Example given: First define the admin mapping and then the user mapping for a certain GitHub organization.

## General configuration options

The `ldap` section contains the `uri`, the `bind_dn` and the `bind_pw` used to connect to the ldap server.
The `member` and `group` section contain information about the ldap scheme of the server. 
They both have a `base` and `filter` attribute used to query for groups and users.
They also both have a `uid_attr` which defines the attribute holding the "name" of the group or user.
Additionally the `group` section conatins the `owner_attr` which holds one or more group admins and the `member_attr` which holds the members of this group (including their owners).

## GitHub Provider

The GitHub provider can be used to sync users to GitHub organizations with either member or admin role.

**Configuration Options**:  
In the `github` configuration section you need to provide an `api_token` that has write access to the members of your GitHub organizations.
It is recommended to create a new GitHub account for this to not bind this token to an active user. You do need to provide a `bot_user_login`.
This username will be ignored during sync and should therefore be the username or your new account.
The GitHub username of a user will be read out of a messenger attribute. A user can have multiple messenger attributes with their value being the messenger name followed by a colon and the actual username.
Example given: messenger: "GitHub:FDHoho007" The messenger must be spelled exactly `GitHub`. The name of this messenger attribute is defined in the `messenger_attr`.

**Mapping Scheme**:
The `mappings/github.json` must contain an array of mappings. A mapping is a simple object holding these four attributes 
* `id`: The id of the GitHub organization.
* `name`: A display name for this mapping, shown in the logs.
* `role`: Either `member` or `admin` defining the user status for the mapped users.
* `ldap_groups`: An array of ldap groups which should be mapped to this GitHub organization.

## GitLab Provider

The GitLab provider can be used to sync users to GitLab groups with different permission levels.

**Configuration Options**:  
Since GitLab can be self-hosted you need to provide the `url` of your GitLab instance as well as an `api_token` with write access to your GitLab groups. Finally you need to define the ldap attribute defining the GitLab username of a user in `username_attr`.

**Mapping Scheme**:  
The `mappings/gitlab.json` must contain an array of mappings. A mapping is a simple object holding these four attributes:
* `id`: The id of either the project or group. Not the numerical id but the url part containing letters and slashes.
* `is_project`: Either `true` or `false` defining wether id is a project or a group.
* `access_level`: The access level for the mapped users. See https://docs.gitlab.com/ee/api/access_requests.html#valid-access-levels
* `ldap_groups`: An array of ldap groups which should be mapped to this GitLab project or group.

## Mailman3 Provider

The Mailman3 provider can be used to sync users to mailing lists.

**Configuration Options**:  
This provider needs access tothe internal admin rest api. The address needs to be set in `url` field. The url has the scheme `http://<hostname>:<port>/<api_version>`. You also need to set the `admin_user` and `admin_password`. These information can be found in `/etc/mailman3/mailman.cfg` under the `webservice` section. Mailman also needs the email address and full name of users. The attribute names for these values are defined in `mail_attr` and `name_attr`.

**Mapping Scheme**:  
The `mappings/mailman3.json` must contain an array of mappings. A mapping is a simple object holding these two attributes:
* `id`: The id or address of the mailing list.
* `ldap_groups`: An array of ldap groups which should be mapped to this mailing list.

## Mattermost Provider

The Mattermost provider can be used to sync users to Mattermost teams.

**Configuration Options**:  
For this provider you need to create a bot account for your mattermost instance (`url` field) who is team administrator in the teams to manage. Set the `api_token` and `bot_user_id` as well as the `username_attr` which contains the Mattermost username of a user.

**Mapping Scheme**:  
The `mappings/mattermost.json` must contain an array of mappings. A mapping is a simple object holding these four attributes:
* `id`: The id of the mattermost team.
* `name`: A display name for this mapping, shown in the logs.
* `roles`: Either `team_user` or `team_user team_admin` defining the roles of mapped users.
* `ldap_groups`: An array of ldap groups which should be mapped to this Mattermost team.

## Redmine Provider

The Redmine provider is very specific. It's designed to update a single redmine page with group memberships from the LDAP.

**Configuration Options**:  
You need to provide the `url` of the page in your redmine instance as well as an `api_token` with write access to this page. The full names of users will be read from the `name_attr`.

**Mapping Scheme**:  
The `mappings/redmine.json` must contain an array of mappings. A mapping is a simple object holding these two attributes:
* `id`: The name of the redmine entry.
* `ldap_groups`: An array of ldap groups which should be mapped to this redmine entry.

## StudIP Provider

The StudIP provider can be used to sync users to a StudIP institution.

**Configuration Options**:  
You need to provide the `url` of your StudIP instance as wells as the credentials of an admin account for your institution in `username` and `password`. The StudIP username will be read from `username_attr`.

**Mapping Scheme**:  
The `mappings/studip.json` must contain an array of mappings. A mapping is a simple object holding these four attributes:
* `id`: The id of your StudIP institution.
* `role_id`: The id of the member role/group.
* `name`: A display name for this mapping, shown in the logs.
* `ldap_groups`: An array of ldap groups which should be mapped to this StudIP institution.

## Possible future providers

* Mattermost channel mappings
* StudIP Dozentenrechte