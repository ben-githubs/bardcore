# Bardcore

Bardcore is a little program I wrote to help me manage playing ambient background music during D&D sessions.

It allows me to pre-compile different track sets to be played at various times during the session, with seamless transitioning. Currently, the following options are possible:

- Multiple versions of the same track, to be swapped between depending on mood. This is like Nier Automata, where the whole level has one sound track, but at varying levels of intensity depending on what's happening in-game.
- Multiple tracks played back-to-back, shuffled or looped as desired. This is more like a normal playlist, with a set of pre-selected tracks being played one after the other.
- Play a single track. This is useful for cases where you have specific music in mind for a certain encounter.

The primary way to use this script is to compile a set of sound files (ogg format), and create a playlist for ambient adventuring that's thematically relevant to your location. Then, swap over to a battle track for encounters and boss fights, and maybe set up some other tracks for certain things, like discovering a new location, or background noise for roleplay with NPCs.

## How to Use

Launch the program, specifying a config file as the argument. The config file will define what tracks are available and how to referenc them.

Once the program is running, use some console commands to manage different tracks:

- `/play`: Play a specific track or tracklist, playing it if nothing's on, or transitioning to it if something is already playing
- `/track`: If a track is playing, switch subtracks
- `/stop`: Stop the current-ly playing track
- `/list`: List the available subtracks
- `/vol`: Set the volume modifier (between 0 and 100)
- `/help`: Display help, like this
- `/quit`: Exit the program.

Each of the commands above can also be invoked with the shorthand form of using the first letter; i.e. `/q` is equivalent to calling `/quit`.

## Autocomplete

The shell supports autosuggestion and autocomplete, so feel free to use the tab key!

## Writing a Config

Config files have several sections.

### sounds

The `sounds` section is used to alias certain filenames used elsewhere in the config. This is useful for assigning short names to files that would otherwise have very long filenames.

### comp track

The `comp track` section is used to define "composite tracks", where multiple versions of the same track are played simultaneously, and you can switch between them depedning on the need.

The `tracks` parameter should be a mapping of names to sound files (or aliases).

### track list

The `track list` section defines playlists of different sound files. It should also contain a `tracks` section, the maps track names to file names (or aliases).

### Misc. Top-Level Parameters

Some miscelaneous parameters are defined at the top level of the document, not under any section.

- `master volume`: The default volume to start all tracks off at. Must be between 0 and 100. Can be altered during execution via the `/vol` command.

## Difference Between a Comp Track and a Track List

The big difference here is that a composite track keeps all versions of the track in sync, so if you play the `quiet` subtrack, then at 30 seconds in, switch to the `battle` subtrack, the `battle` subtrack will also be 30 seconds in. This requires that all the subtracks are the same length, otherwise over time, the tracks will begin to drift from being in sync. If you've played Nier Automata, that's exactly what this is for. Additionally, when a subtrack finishes playing, it starts the same subtrack over.

A track list, on the other hand, doesn't preserve progress across tracks. It plays one subtrack, completes it, and the starts a different one from the beginning. If you switch the current subtrack part-way through, it will start at the beginning. (You actually can't switch subtracks yet, haven't gotten round to adding that.)

## Issues and Shortcomings

- The biggest issue is that all the sound files have to be loaded in memory simultaneously, otherwise there's stuttering between swtiching tracks. This doesn't present a problem when relatively few files are loaded, but obviously the more you add to your config the worse it gets. For this reason, it's best to only group configs based on what tracks you imagne frequently switching between. If, for example, you have a session that spends some time in a city, and some time in the woods, and both locations have different background music, it's best to make 2 separate configs, and just restart the program when the party moves locations.
- As previously mentioned, you currently can't swap to a different song in a track list. This shouldn't be a huge issue; if you have a track you imagine needing to switch to, just make it it's own thing and not part of the track list.
