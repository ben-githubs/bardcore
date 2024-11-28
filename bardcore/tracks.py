"""Code for representing each musical track."""

from abc import ABC, abstractmethod
from pathlib import Path
import logging
import random
import threading

from pygame import mixer

from . import util

# Initialize the pygame sound mixer
mixer.init(channels=10)

# store sound objects; useful to prevent duplicate sound files being loaded
_sound_objects: dict[Path, mixer.Sound] = {}


def get_sound(path: Path) -> mixer.Sound:
    """Loads a Sound object from disk."""
    # First, check if it's already loaded
    path = path.expanduser().absolute()
    if sound := _sound_objects.get(path):
        return sound
    # Else, load it
    sound = mixer.Sound(file=path)
    _sound_objects[path] = sound
    return sound


class Track:
    """Tracks represent single sound files."""

    def __init__(self, name: str, path: Path):
        """Creates a Track.

        Args:
            name (str): Title for the mode.
            path (Path): Path to the sound file.
        """
        self.name = name
        self.path = path

        # Store for the pygame Sound object; only initialized if we pre-load the song.
        #   This is to prevent memory issues from lots of long tracks.
        self.sound: mixer.Sound = None

    def load(self):
        """Load the music from the sound file."""
        logging.debug(f"Loading sound '{self.path.name}' from filesystem...")
        self.sound = get_sound(self.path)
        logging.debug(f"Finished loading '{self.path.name}'.")

    def play(self, initial_volume: float = 1, loops: int = 0):
        """Start playing the track.

        Args:
            initial_volume (float): How loud the track should start. Range: [0-1]
            loops (int): How many times to loop the track. 0 indicates endless loops.
        """
        # Load sound, if we haven't already
        if not self.sound:
            self.load()
        self.sound.set_volume(min(1, max(0, initial_volume)))
        # Our loops is 'number of complete iterations', but pygame loops is 'number of repeats', so
        #   we adjust by one.
        self.sound.play(loops - 1)


class Playable(ABC):
    """Playable objects act as managers and containers for groups of tracks."""

    def __init__(self, name: str, tracks: list[Track]):
        self.name = name

        # Use a dict to store tracks so we can easilty reference them by name
        self.tracks = {track.name: track for track in tracks}

        # Is this Playable currently platying something?
        self.is_playing: bool = False
        # Reference to the track currently being played
        self.current_track: Track | None = None

        # Preload tracks
        for track in tracks:
            track.load()

    @abstractmethod
    def play(self, track_name: str, vol: float = 1) -> None:
        """This function should begin playing the track list, starting with 'track_name'. If the
        track list is already playing, and another track is currently playing, then it should
        should switch to playing the new track. It should also be able to set the initial volume of
        the target track."""
        pass

    @abstractmethod
    def stop(self, fade_dur: float) -> None:
        """This function should stop the currently-playing track, and set self.is_playing to
        false. it should also accept a 'fade_dur' paramater, defining how long the fade out
        transition should be."""
        pass


class CompTrack(Playable):
    """A CompTrack object represent a "composite track", where multiple tracks are kept in sync,
    and you can swap out which one is playing at any given time."""

    def __init__(self, name: str, tracks: list[Track]) -> None:
        """Create a new CompTrack object.

        Args:
            name (str): The name of the track to use when registering to a Player object.
            tracks (list [Track]): Which tracks to play in sync and switch between.
        """
        super().__init__(name, tracks)

    def play(self, track_name: str = None, vol: float = 1):
        """Starts playtng this track. If a track name is provided, we play that track. Otherwise
        we start playing all tracks, but at zero volume.

        Args:
            track_name (str): Name of the track to play. If unspecified, all tracks begin playing,
                but with zero volume. If an empty string, a default mode is chosen. If specified
                and no mode exists with that name, raises a KeyError.
            vol (float): Volume to play at. Range: [0-1]

        Raises:
            KeyError if there is no track with this name.
        """
        target_track = (
            self.tracks[track_name] if track_name else list(self.tracks.values())[0]
        )

        # If different mode is already playing, switch to it
        if self.is_playing:
            # If target mode is already playing, just exit
            if target_track == self.current_track:
                # TODO: Edit this to allow users to change volume of currently-playing track
                logging.debug("This track is already playing. Skipping.")
                return
            if target_track:
                logging.debug("Switing tracks")
                util.fade_sounds(self.current_track.sound, target_track.sound)
            else:
                logging.debug("Fading down")
                util.fade_sounds(self.current_track.sound, None, 2.5)

        # If no sounds are playing
        else:
            logging.debug(f"Playing CompTrack '{self.name}'")
            # Play modes
            for track in self.tracks.values():
                # Play the other modes with volume = 0, so they're all in sync
                volume = vol if track == target_track else 0
                track.play(volume)

        self.is_playing = True
        self.current_track = (
            target_track or self.current_track or list(self.tracks.values())[0]
        )

    def stop(self, fade_dur: float = -1):
        """Stop the current track. Optionally fade out over a given duration."""
        self.is_playing = False
        util.fade_sounds(self.current_track.sound, None, fade_dur)
        for track in self.tracks.values():
            track.sound.stop()


class TrackList(Playable):
    def __init__(self, name: str, tracks: list[Track]):
        # Thread that manages playing the next song in the playlist
        self.thread: threading.Thread = None
        self.stop_event: threading.Event = threading.Event()

        super().__init__(name, tracks)

    def play(
        self,
        track_name: str = None,
        vol: float = 1,
        loop: bool = True,
        shuffle: bool = True,
    ):
        kwargs = {
            "track_name": track_name,
            "loop": loop,
            "shuffle": shuffle,
            "vol": vol,
        }
        if self.is_playing:
            if track_name != self.current_track.name:
                # TODO: Adjust this to trigger an event to swap the currently-playing track
                logging.warning(
                    "Switching tracks of a track list is not currently supported."
                )
            else:
                logging.info(
                    "Cannot start TrackList '{self.name}' because it is already playing"
                )
            return
        self.thread = threading.Thread(target=self.play_async, kwargs=kwargs)
        self.thread.start()
        # NOTE: It might be possible (though I haven't seen it) that the thread could start, but
        #   control returns to the console before the async thread sets the current_track variable.
        #   if this becomes an issue, we should set up an Event indicating that the thread has
        #   finished setting up, and only return from this function once the event is triggered.

    def play_async(
        self,
        track_name: str = None,
        vol: int = 1,
        loop: bool = False,
        shuffle: bool = False,
    ):
        # Make a copy of the list, so we can shuffle it and not alter the original
        songs: list[Track] = [t for t in self.tracks.values()]
        if shuffle:
            random.shuffle(songs)

        # If a track name is specified, put it at the start of the list
        if track_name:
            track = self.tracks.get(track_name)
            if not track:
                logging.error(
                    f"TrackList '{self.name}' has no track named '{track_name}'"
                )
                self.thread = None
                return
            songs.insert(0, songs.pop(songs.index(track)))

        # Play songs
        n_iter = 0
        while n_iter < 1 or loop:  # Play at least once, or loop it
            n_iter += 1
            for song in songs:
                song.play(initial_volume=vol)
                self.current_track = song
                # Wait for a stop event, or until the song is finished
                self.stop_event.wait(timeout=song.sound.get_length())
                # Check if we actually stopped
                if self.stop_event.is_set():
                    util.fade_sounds(song.sound, None, tspan=self.stop_event.fade_dur)
                    self.stop_event.clear()
                    song.sound.stop()
                    return
                else:
                    song.sound.stop()

    def stop(self, fade_dur: float = 2.5):
        logging.info(f"Stopping playlist '{self.name}'...")
        if self.is_playing:
            logging.debug("Sending STOP event to '{self.name}'")
            self.stop_event.fade_dur = (
                fade_dur  # Feels like this is bad practice but meh
            )
            self.stop_event.set()
            logging.debug(f"Waiting for {self.name}'s thread to join...")
            self.thread.join()
            logging.debug(f"{self.name}'s thread joined successfully!")
            self.thread = None

    @property
    def is_playing(self):
        return self.thread is not None

    @is_playing.setter
    def is_playing(self, val):
        if not val:
            self.stop()
        else:
            self.play()
