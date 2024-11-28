from pathlib import Path
import sys
import logging

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter, FuzzyCompleter

from . import config
from .player import Player
from .tracks import Playable
from ._logging import configure_logging

player: Player = None
session = PromptSession()


def help():
    helptxt = (
        "Bardore is a background-music management app intended for use in D&D sessions.",
        "",
        "The following commands are availale for use.",
        "/help, /h:    Displays this help text.",
        "/quit, /q:    Exits the progam.",
        "/list, /l:    List the available tracks for the currently playing item.",
        "/stop, /s:    Stop playing the current item.",
        "/play, /p [playable] [track?]:    Starts playing the specified track list or composite",
        "                                  track. Optionally provide a substract to start.",
        "/track, /t [track]:               Switch the currently playing track to a different one.",
    )
    print("/n".join(helptxt))


def switch_track(track_name: str = None):
    if track_name:
        player.switch_track(track_name)
    else:
        print("The following tracks are available to switch to:")
        list_tracks(player)


def play(track_name: str, mode_name: str = None):
    player.play(track_name, mode_name)


def list_tracks(player: Player):
    for track in player.current_playable.tracks.values():
        suffix = ""
        if track == player.current_playable.current_track.name:
            suffix = " (CURRENTLY PLAYING)"
        print("  * " + track + suffix)


def build_completer():
    """Builds a map for auto completions when prompting the user for input."""
    logging.debug("Building auto-completion")
    completer_dict = {
        "/help": None,
        "/track": None,
        "/stop": None,
        "/quit": None,
        "/list": None,
        "/vol": None,
        "/play": {},
    }
    for playable in player.playables.values():
        completer_dict["/play"][playable.name] = {
            "- " + track: None for track in playable.tracks.keys()
        }

    if player.current_playable and isinstance(player.current_playable, Playable):
        completer_dict["/track"] = {track for track in player.list_tracks()}

    completer_dict["/h"] = completer_dict["/help"]
    completer_dict["/t"] = completer_dict["/track"]
    completer_dict["/s"] = completer_dict["/stop"]
    completer_dict["/q"] = completer_dict["/quit"]
    completer_dict["/l"] = completer_dict["/list"]
    completer_dict["/v"] = completer_dict["/vol"]
    completer_dict["/p"] = completer_dict["/play"]

    completer = FuzzyCompleter(NestedCompleter.from_nested_dict(completer_dict))
    logging.debug("Finished building autocompleter.")
    return completer


def volume(vol: str) -> None:
    # If no value is provided, just print out the current value.
    if not vol:
        vol_str = round(player.master_volume * 100)
        print(f"Volume is currently set at {vol_str}%")
        return

    # Else, set the volume to the new value
    vol = int(vol)
    if vol < 0 or vol > 100:
        logging.error("Volume must be between 0 and 100!")
        return

    player.set_volume(vol / 100)
    print(f"Volume is now set at {vol}%")


def main():
    if len(sys.argv) != 2:
        print("Bardcore only accepts 1 argument: the path to the config file.")
        exit(1)

    fname = Path(sys.argv[1])
    configure_logging(fname)
    logging.info("Starting program.")

    global player
    player = config.load_config(fname)
    print("Welcome to -- B A R D C O R E! --")
    completer = build_completer()

    # Input loop
    while True:
        prompt_text = "bardcore"
        modestr = ""
        if player.current_playable:
            modestr = f"/{player.current_playable.current_track.name})"
            prompt_text += f" ({player.current_playable.name}{modestr})"
        user_input: str = session.prompt(
            prompt_text + " > ", completer=completer, complete_while_typing=True
        )
        if not user_input:
            continue
        idx = user_input.find(" ")
        cmd = user_input[:idx].strip() if idx > 0 else user_input.strip()
        args = user_input[idx:] if idx > 0 else ""
        try:
            match cmd:
                case "/h" | "/help":
                    help()
                case "/s" | "/stop":
                    player.stop()
                case "/t" | "/track":
                    switch_track(args.strip())
                case "/p" | "/play":
                    play(*[a.strip() for a in args.split("-")])
                    completer = build_completer()
                case "/l" | "/list":
                    list_tracks(player)
                case "/v" | "/vol":
                    volume(args)
                case "/q" | "/quit":
                    player.stop(0)
                    break
        except BaseException as e:
            # logging.error(f"{e.__class__.__name__}: {e}")
            raise e
        print()
    logging.info("Exiting program.")
