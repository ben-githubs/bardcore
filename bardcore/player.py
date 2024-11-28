import logging

from .tracks import Playable
from .errors import NoTrackPlayingError
from . import util


class Player:
    def __init__(self, master_volume: float = 1.0):
        """ Creates a new Player object.
        
        Args:
            master_volume (float): Adjust the volume of all sounds played. Must be between 0 and 1.
        """
        self.playables: dict[str, Playable] = {}
        self.current_playable: Playable = None
        self.master_volume = master_volume
    

    def switch_track(self, track_name: str):
        """ Switch the track of the current Playable. """
        if not self.current_playable:
            raise NoTrackPlayingError("Unable to switch tracks; nothing is currently playing")
        self.current_playable.play(track_name)
    

    def list_tracks(self) -> list[str]:
        """ Returns a list of track names for the currently-playing Playable. """
        if not self.current_playable:
            raise NoTrackPlayingError("Unable to list tracks; nothing is currently playing")
        return list(self.current_playable.tracks.keys())
    

    def get_track(self) -> str:
        """ Returns the name of the track currently playing. """
        if not self.current_playable:
            raise NoTrackPlayingError("Unable to fetch track; nothing is currently playing")
        return self.current_playable.current_track.name
    

    def get_playable(self) -> str:
        """ Returns the name of the Playable currently playing. """
        if not self.current_playable:
            return ""
        return self.current_playable.name
    

    def list_playables(self) -> list[str]:
        """ Returns a list of all the available Playable names. """
        return list(self.playables.keys())
    

    def stop(self, fade_dur: float = 2.5):
        """ Stops the currently playing Playable. """
        # If nothing is playing, just exit
        if not self.current_playable:
            logging.debug("Nothing to stop. Skipping.")
            return
        playable = self.current_playable
        logging.debug(f"Stopping track '{playable.name}'...")
        playable.stop(fade_dur)
        self.current_playable = None
        logging.debug(f"Track '{playable.name}' stopped.")
    

    def play(self, playable_name: str, track_name: str = "", fade_dur: float = 2.5):
        """ Play a specific Playable and Track.
        
        Args:
            playable_name (str): Name of the Playable to play.
            track_name (str): Name of the track to play. If unspecified, uses a default track.
            fade_dur (float): Duration of fade-in effect for switching Playables.
        """
        target_playable = self.playables[playable_name]
        # If nothing is currently playing
        if not self.current_playable:
            target_playable.play(track_name, vol=self.master_volume)
        # If something is playing:
        else:
            # Start playing the other track, but explicitly set all modes to 0 volume
            target_track = None
            target_playable.play(track_name, vol=0)
            target_track = target_playable.current_track
            current_track = None
            current_track = self.current_playable.current_track
            util.fade_sounds(
                current_track.sound,
                target_track.sound,
                fade_dur,
                self.master_volume
            )
            self.current_playable.stop()
        self.current_playable = target_playable
    

    def register_playable(self, playable: Playable):
        self.playables[playable.name] = playable
    

    def set_volume(self, volume: float = 1.0):
        """ Sets the master volume of the player, affecting any sounds played. """
        self.master_volume = volume
        if self.current_playable:
            if track := self.current_playable.current_track:
                track.sound.set_volume(volume)