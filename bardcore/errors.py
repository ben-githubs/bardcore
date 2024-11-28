class PlayerError(BaseException):
    pass


class NoTrackPlayingError(PlayerError):
    pass


class ConfigError(PlayerError):
    pass