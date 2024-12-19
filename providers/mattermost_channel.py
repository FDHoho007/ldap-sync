from providers.mattermost import IMattermostProvider

class MattermostChannelProvider(IMattermostProvider):
    def __init__(self, config):
        super().__init__("Mattermost-Channels", config, "channels")