# media

Public media hosting for scheduled social posts (images in `img/`, videos in `vid/`).

`tools/` holds the generators:
- `gen.py` + `make_all.py`: kinetic-text TikTok videos (720x1280, ffmpeg, PIL, numpy). Beats are defined in `make_all.py`.
- `memes.py`: 1200x675 meme-format images for X.

Naming for new files: `vid/tNN.mp4`, `img/xNN.png` (NN = next number).
