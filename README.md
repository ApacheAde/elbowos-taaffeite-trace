# Taaffeite Trace

Full-colour Python 3 neon light-cycle arcade for ElbowOS.

A lilac blade cuts a vertical grid. Trails linger, then fade. Amber sparks score. Saffron and aqua rivals share the same walls. Crash, flash, respawn.

This is an original light-cycle. It is not a Nintendo ROM, not an emulator, and not a clone of the platformer, card, or slots packs.

Featured account: https://x.com/ElbowOS

Drive reel: https://drive.google.com/file/d/1ZGfFD1VVB2TrXa8-eMhFxDj3uuiMvU8N/view?usp=drivesdk

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 taaffeite_trace.py --play
```

Arrows or WASD turn. R restarts. You cannot reverse into your own blade.

## Record a 9:16 reel

```bash
python3 taaffeite_trace.py --record
```

Headless path uses `SDL_VIDEODRIVER=dummy`, draws 1080x1920 at 30fps for 15 seconds, and pipes RGB frames to ffmpeg (`libx264`, `yuv420p`, CRF 20, `+faststart`).

Overlay on every frame: title, score, and `x.com/ElbowOS`.
