"""Code for loading config files."""

import logging
from pathlib import Path

from ruamel.yaml import YAML

from .errors import ConfigError
from .player import Player
from .tracks import Playable, Track, CompTrack, TrackList

yaml = YAML(typ="safe")


def load_config(path) -> Player:
    logging.debug(f"Loading config from file '{path}'")
    with path.open("r") as f:
        config = yaml.load(f)

    # Load named sound files
    #   We allow users to give names to sound files to make referencing them easier elsewhere in
    #   the config file.
    named_sounds: dict[str, Path] = {}
    if sounds_config := config.get("sounds"):
        # sounds_config should be a dict with sound aliases mapped to paths
        for alias, soundpath in sounds_config.items():
            named_sounds[alias] = Path(soundpath)
    logging.debug(f"Loaded {len(named_sounds)} sounds from config.")

    # Load CompTracks & TrackLists
    playables: dict[str, Playable] = {}

    def load_config_tracks(config: dict) -> list[Track]:
        # Load tracks
        track_defns: dict[str, str] = config.get("tracks", {})
        tracks: list[Track] = []
        for track_name, track_path in track_defns.items():
            if track_path in named_sounds:
                track_path = named_sounds[track_path]
            tracks.append(Track(track_name, track_path))
        return tracks

    for name, defn in config.get("comp tracks", {}).items():
        if name in playables:
            raise ConfigError(f"Multiple playables in config with name '{name}'")
        playables[name] = CompTrack(name, load_config_tracks(defn))

    for name, defn in config.get("tracklists", {}).items():
        if name in playables:
            raise ConfigError(f"Multiple playables in config with name '{name}'")
        playables[name] = TrackList(name, load_config_tracks(defn))

    logging.debug(f"Loaded {len(playables)} playable items")

    # Load other config items
    master_volume = config.get("master volume", 100)
    if not (0 <= master_volume <= 100):
        logging.warning(
            "Volume must be between 0 and 100! "
            f"Ignoring value of '{master_volume}' and using 100 instead."
        )
        master_volume = 100
    # Convert to percentage
    master_volume /= 100

    player = Player(master_volume=master_volume)
    for item in playables.values():
        logging.debug(f"Registering playable from config: {item.name}")
        player.register_playable(item)

    logging.info("Finished loading config.")
    return player
