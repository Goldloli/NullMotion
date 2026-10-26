"""Save the best real file for an X status. Never re-encodes.

Twitter's bitrate labels are often wrong, so every MP4 variant is downloaded
and measured with ffprobe. The winner is the largest frame, then the highest
measured video bitrate. original_info is the size the creator uploaded. If the
best file is smaller than that, the run fails instead of quietly keeping a
worse copy.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

SYNDICATION = "https://cdn.syndication.twimg.com/tweet-result?id={id}&token=0"
UA = "Mozilla/5.0"


def status_id(value):
    digits = "".join(ch if ch.isdigit() else " " for ch in value).split()
    if not digits:
        raise SystemExit(f"No status id in {value}")
    return digits[-1]


def fetch_tweet(identifier):
    request = urllib.request.Request(SYNDICATION.format(id=identifier), headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def variants(tweet):
    details = (tweet.get("mediaDetails") or [None])[0] or {}
    info = details.get("video_info") or {}
    original = details.get("original_info") or {}
    rows = []
    for variant in info.get("variants") or []:
        url = variant.get("url") or ""
        if "video/mp4" in (variant.get("content_type") or "") or "/vid/" in url:
            rows.append(url.split("?")[0])
    if not rows:
        raise SystemExit("This post has no video.")
    return original.get("width"), original.get("height"), list(dict.fromkeys(rows))


def probe(path):
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,bit_rate",
        "-of", "json", str(path),
    ], text=True)
    stream = json.loads(raw)["streams"][0]
    return int(stream["width"]), int(stream["height"]), int(stream.get("bit_rate") or 0)


def download(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def best(identifier):
    upload_w, upload_h, urls = variants(fetch_tweet(identifier))
    measured = []
    with tempfile.TemporaryDirectory(prefix="x-video-") as temp:
        root = Path(temp)
        for index, url in enumerate(urls):
            path = root / f"{index}.mp4"
            download(url, path)
            width, height, bitrate = probe(path)
            measured.append((width * height, bitrate, path.stat().st_size, width, height, url, path.read_bytes()))
    measured.sort(reverse=True)
    _, bitrate, size, width, height, url, data = measured[0]
    if upload_w and upload_h and (width < upload_w or height < upload_h):
        raise SystemExit(
            f"Best download is {width}x{height}, but X records the upload as {upload_w}x{upload_h}."
        )
    return {
        "id": identifier,
        "upload": [upload_w, upload_h],
        "chosen": [width, height],
        "bitrate": bitrate,
        "bytes": size,
        "url": url,
        "data": data,
        "options": [[item[3], item[4], item[1]] for item in measured],
    }


def smooth(source, dest):
    """Same playback master as the other references: constant frame rate, no B-frames,
    lossless H.264. Twitter's own MP4 stutters in the browser."""
    subprocess.check_call([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
        "-map", "0:v:0", "-map", "0:a:0?",
        "-vf", "scale=trunc(iw*sar/2)*2:ih,setsar=1,pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-fps_mode", "cfr", "-r", "30",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "0", "-bf", "0",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart",
        str(dest),
    ])


def main():
    parser = argparse.ArgumentParser(description="Save the best real X video for a status.")
    parser.add_argument("status")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = best(status_id(args.status))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        raw = args.out.with_suffix(".source.mp4")
        raw.write_bytes(result["data"])
        smooth(raw, args.out)
    upload = "x".join(str(part) for part in result["upload"])
    chosen = "x".join(str(part) for part in result["chosen"])
    options = ", ".join(f"{w}x{h}@{bitrate // 1000}kbps" for w, h, bitrate in result["options"])
    print(f"upload {upload}")
    print(f"playing {chosen} at {result['bitrate'] // 1000} kbps ({result['bytes']} bytes)")
    print(f"measured {options}")
    if args.out:
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
