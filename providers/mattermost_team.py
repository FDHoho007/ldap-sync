from providers.mattermost import IMattermostProvider

class MattermostTeamProvider(IMattermostProvider):
    def __init__(self, config):
        super().__init__("Mattermost-Teams", config, "teams")