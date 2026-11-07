"""
Python Subtitle downloader for YouTube videos.

Rewritten for Python 3 (tested on 3.11+) and the modern YouTube regime.
The legacy video.google.com/timedtext endpoint used by the original
2017 script was silently shut down by YouTube (it now returns an empty
body), so this version uses the InnerTube get_transcript API through
the youtube-transcript-api package, which is updated when YouTube
changes its internals.

Usage:
    pip install youtube-transcript-api
    python subfetch.py                          # prompts for the link
    python subfetch.py <youtube url or video id>

A self-contained Windows build is rebuildable with PyInstaller
(see the README "Distributable exe" section). It embeds this script
and its youtube-transcript-api dependency, so end users without
Python can run dist\\subfetch.exe directly.

Requires: Python 3.9+, youtube-transcript-api 1.0+

@author: Dimitris Dimopoulos (original, 2017-2018)
"""

import json  # parsing the oEmbed response for the video title
import re
import sys
import urllib.request

try:
    # Kept as an instance of the package's own error module so that
    # unexpected upstream changes surface as a clean message (see
    # the generic handler in main()) instead of a traceback.
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
    )
except ImportError:
    sys.exit(
        "youtube-transcript-api is not installed.\n"
        "Install it with:  pip install youtube-transcript-api"
    )

# Fallback output file, kept identical to the original program's
# behavior when the video title cannot be determined via oEmbed
OUTPUT_FILE = "subtitle.srt"


def extract_video_id(text):
    """Extract the 11-character video id from any YouTube link form.

    Handles watch?v=, youtu.be/, shorts/, embed/ and v/ links, bare video
    ids, and URLs polluted with extra parameters such as &list=... .
    """
    text = text.strip()
    if not text:
        return None
    # Standalone video id
    if re.fullmatch(r"[0-9A-Za-z_-]{11}", text):
        return text
    patterns = [
        r"(?:youtu\.be/)([0-9A-Za-z_-]{11})",
        r"(?:\?|\&|/)v=([0-9A-Za-z_-]{11})",
        r"/shorts/([0-9A-Za-z_-]{11})",
        r"/embed/([0-9A-Za-z_-]{11})",
        r"/live/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def get_transcript_list(video_id):
    """Return the list of available transcripts, or None if there are none."""
    api = YouTubeTranscriptApi()
    return api.list(video_id)


def choose_language(transcript_list):
    """Print the available transcript languages and ask the user to pick one.

    Returns the transcript object chosen by the user. Falls back to English
    if present (or to the first manual transcript) when the user just
    presses Enter.
    """
    transcripts = list(transcript_list)
    if not transcripts:
        return None

    manual = [t for t in transcripts if not t.is_generated]
    generated = [t for t in transcripts if t.is_generated]

    english = [t for t in manual if t.language_code.startswith("en")]
    default = english[0] if english else (manual[0] if manual else generated[0])

    print("Available languages:\n")
    for i, t in enumerate(transcripts):
        kind = "auto-generated" if t.is_generated else "manual"
        is_default = " [default]" if t is default else ""
        print(f"  {i + 1}. {t.language_code}  ({t.language}, {kind}){is_default}")

    choice = input(
        "\nPlease press the corresponding number "
        f"[Enter = {default.language_code}]: "
    ).strip()

    if not choice:
        return default
    try:
        index = int(choice) - 1
        if not 0 <= index < len(transcripts):
            raise ValueError
    except ValueError:
        print(f"Invalid choice, using {default.language_code}.")
    else:
        default = transcripts[index]
    return default


def fetch_transcript(transcript):
    """Fetch the transcript snippets for the chosen language."""
    return transcript.fetch()


def format_srt_time(seconds):
    """Format a float number of seconds as an SRT timestamp HH:MM:SS,mmm."""
    milliseconds = int(round(seconds * 1000))
    hours, rest = divmod(milliseconds, 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(fetched_transcript, filename=OUTPUT_FILE):
    """Convert the fetched transcript into an SRT file.

    Same matroska-style SRT layout the original script produced:
        1
        00:00:05,123 --> 00:00:10,456
        Subtitle text
        (empty line)
        2
        ...
    """
    counter = 0
    with open(filename, "w", encoding="utf-8") as fh:
        for snippet in fetched_transcript:
            counter += 1
            start = format_srt_time(snippet.start)
            end = format_srt_time(snippet.start + snippet.duration)
            fh.write(f"{counter}\n")
            fh.write(f"{start} --> {end}\n")
            fh.write(snippet.text.replace("\n", " ") + "\n")
            fh.write("\n")
    return filename, counter


def make_srt_safe_name(text):
    """Turn a video title into a safe filename."""
    cleaned = re.sub(r'[\\/:*?"<>|]+', "", text).strip()
    return cleaned or "subtitle"


def get_video_title(video_id):
    """Try to get the video title through YouTube's public oEmbed endpoint.

    Returns None on any failure (private videos, network issues, ...) so the
    caller can fall back to the generic name.
    """
    url = ("https://www.youtube.com/oembed?url=https://www.youtube.com/"
           "watch%3Fv%3D" + video_id + "&format=json")
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8")).get("title")
    except (OSError, ValueError):
        return None


def main():
    # Windows consoles default to cp1252 and crash printing characters
    # such as the ♪ notes that appear in subtitle text; don't let any
    # print kill the run when errors="replace" can handle it instead
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    if len(sys.argv) > 1:
        sub_var = " ".join(sys.argv[1:])
    else:
        sub_var = input("Please enter the youtube link: ")

    video_id = extract_video_id(sub_var)
    if not video_id:
        sys.exit("Could not extract a video id from that link!")

    print(f"Video id: {video_id}\n")

    try:
        transcript_list = get_transcript_list(video_id)
    except TranscriptsDisabled:
        sys.exit("No available subtitles found! (subtitles are disabled "
                 "for this video)")
    except VideoUnavailable:
        sys.exit("This video is unavailable or does not exist.")
    except NoTranscriptFound:
        sys.exit("No available subtitles found!")
    except Exception as exc:
        # Anything unexpected (rate limiting by YouTube, network problems,
        # a new upstream API change, ...) should not crash with a traceback
        sys.exit(f"Could not retrieve the subtitle list: {exc}")

    transcript = choose_language(transcript_list)
    if transcript is None:
        sys.exit("No available subtitles found!")

    print(f"\nFetching {transcript.language} ({transcript.language_code})...")
    fetched = fetch_transcript(transcript)

    title = get_video_title(video_id)
    if title:
        # Save with the video's name (the old "TODO: Save the subtitles
        # with the name of the video" from the 2017 script)
        filename = make_srt_safe_name(title) + ".srt"
        print(f"Video title: {title}")
    else:
        filename = OUTPUT_FILE

    filename, count = write_srt(fetched, filename)
    print(f"Saved {count} subtitle segments to: {filename}")


if __name__ == "__main__":
    main()
