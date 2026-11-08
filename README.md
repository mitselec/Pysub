# PySub

Python YouTube subtitle downloader

This script downloads the subtitles of a YouTube video and saves
them as a standard SRT file, named after the video.

Python 3.9+

Dimitris Dimopoulos 2017-2026

## Requirements

- Python 3.9 or newer
- [youtube-transcript-api](https://pypi.org/project/youtube-transcript-api/) 1.0+

    pip install -r requirements.txt

## How to use:

- Find a video of your preference that has subtitles and copy the url

- Run the program, either as the distributable binary or from the script by
  passing the link as an argument or pasting it into the prompt:

    dist\subfetch.exe                                # Windows
    ./dist/subfetch                                  # Linux
    python subfetch.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
    python subfetch.py                          # prompts for the link

- Choose the subtitle language you want by pressing the corresponding number
  (just pressing Enter picks English, or the first manual track if there
  is no English one)

- The subtitle is going to be saved into your working directory, named after
  the video title with a ".srt" extension. You can rename it if you want to.

- Enjoy!

## Supported link forms

`youtube.com/watch?v=VIDEOID`, `youtu.be/VIDEOID`, `youtube.com/shorts/VIDEOID`,
`youtube.com/embed/VIDEOID`, `youtube.com/live/VIDEOID`, or a bare video ID.
Extra parameters in the link (e.g. `&list=...`, `?si=...`) do not matter.

## Notes

The original 2017 version used the `video.google.com/timedtext` endpoint,
which YouTube shut down (it now returns empty responses), and did not run
on Python 3. This version uses the InnerTube get_transcript API through
the youtube-transcript-api package, which is maintained against YouTube's
changes.

## Distributable binaries

PyInstaller builds are only ever produced for the OS the build machine runs
on, so there is one build per platform:

- `dist\subfetch.exe` — Windows (also committed here for convenience)
- `dist/subfetch` — Linux (no extension; run `chmod +x dist/subfetch` and
  start it with `./dist/subfetch`)

Both are self-contained (~10 MB, no Python installation required on the
target machine) and embed the youtube-transcript-api package, so the only
prerequisite to run them is an internet connection.

Both artifacts are built on every CI run and can be downloaded from the
workflow run's "Artifacts" section (`subfetch-exe-windows` and
`subfetch-exe-linux`).

To rebuild locally for your platform after code changes:

    pip install pyinstaller
    python -m PyInstaller --onefile --console --name subfetch subfetch.py

On Linux this produces `dist/subfetch`; on Windows `dist\subfetch.exe`
(which is why the same command works everywhere). If you are on Windows and
want the Linux binary, either let CI build it or run the same command under
WSL — a WSL build yields a working Linux executable.

The binaries are always built from the current source, so rebuild them
whenever you change `subfetch.py` or update the youtube-transcript-api
dependency.
