from providers.mattermost import IMattermostProvider

class MattermostChannelProvider(IMattermostProvider):
    def __init__(self, config):
        super().__init__("Mattermost-Channels", config, "channels")

    def removeMember(self, group, memberId):
        channel_info = self.api("GET", "/" + self.url_part + "/" + group["id"])
        # Dont remove members from public channels
        if channel_info["type"] == "P":
            self.api_group(group, "DELETE", "/" + memberId)
            return True
        return False