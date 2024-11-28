import time
from pygame import mixer


def fade_sounds(
    down_sound: mixer.Sound, up_sound: mixer.Sound, tspan: float = 5.0, vol: float = 1.0
):
    tnow = time.time()
    frac = 0
    init_vol = down_sound.get_volume()
    while frac < 1 and tspan > 0:
        if down_sound:
            down_sound.set_volume((1 - frac) * init_vol)
        if up_sound:
            up_sound.set_volume(frac * vol)
        frac = (time.time() - tnow) / tspan
    if down_sound:
        down_sound.set_volume(0)
    if up_sound:
        up_sound.set_volume(1)
