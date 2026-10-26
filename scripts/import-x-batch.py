"""Import a list of X posts into the local Null library.

Each post keeps the largest MP4 Twitter stored, then a constant-frame-rate
H.264 copy with no B-frames so the browser does not stutter. The library
groups by the day the post was published.
"""
import argparse
import json
import re
import shutil
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / ".local-media"
REF = ROOT / "public" / "references"
UA = "Mozilla/5.0"
URLS = """
https://x.com/rajzmotion/status/2096940191579808210
https://x.com/rajzmotion/status/2093230990630289874
https://x.com/rajzmotion/status/2096257757737607343
https://x.com/rajzmotion/status/2093942396975501785
https://x.com/rajzmotion/status/2091906585362940174
https://x.com/rajzmotion/status/2092260430681161874
https://x.com/rajzmotion/status/2092497049057173816
https://x.com/rajzmotion/status/2096526574782906837
https://x.com/creatoroly/status/2037144525441839239
https://x.com/creatoroly/status/1998369891402068394
https://x.com/creatoroly/status/2029962830833651983
https://x.com/creatoroly/status/2079900676922949772
https://x.com/creatoroly/status/2012531097901375723
https://x.com/shapelayer/status/2093769644083454114
https://x.com/shapelayer/status/2101289932652200366
https://x.com/shapelayer/status/2104208224933347400
https://x.com/shapelayer/status/2096585382758420807
https://x.com/shapelayer/status/2094417742258434323
https://x.com/aftermagics/status/2096902971095458214
https://x.com/aftermagics/status/2101214838164992428
https://x.com/aftermagics/status/2100441131989516740
https://x.com/krocits/status/1986090549255041452
https://x.com/krocits/status/2001320319890620500
https://x.com/krocits/status/1964305080556847194
https://x.com/krocits/status/1990473988448113128
https://x.com/krocits/status/1962942877409128939
https://x.com/krocits/status/1975207288270119229
https://x.com/bohdanmotion/status/2099558248642728252
https://x.com/bohdanmotion/status/2086463736412299268
https://x.com/bohdanmotion/status/2094413431520555496
https://x.com/bohdanmotion/status/2061880508460540379
https://x.com/bohdanmotion/status/2060131741193429387
https://x.com/bohdanmotion/status/2062980467939307696
https://x.com/titouangillet_/status/2099861579453841845
https://x.com/titouangillet_/status/2096989481081417836
https://x.com/titouangillet_/status/2103491987915632981
https://x.com/titouangillet_/status/2103511092013957138
https://x.com/sanzxcreates/status/2086553470514151819
https://x.com/sanzxcreates/status/2091049204940783846
https://x.com/sanzxcreates/status/2101959683993137435
https://x.com/sanzxcreates/status/2093420483719168317
https://x.com/sanzxcreates/status/2091418413050761224
https://x.com/abdinmotion/status/2076334604437332328
https://x.com/abdinmotion/status/2101753294641078579
https://x.com/abdinmotion/status/2096547585011908762
https://x.com/abdinmotion/status/2095893171590848684
https://x.com/abdinmotion/status/2072958650360984055
https://x.com/leomeethewoo/status/2098033411000828007
https://x.com/leomeethewoo/status/2088978487101243899
https://x.com/leomeethewoo/status/2102412626278113486
https://x.com/leomeethewoo/status/2103605417171681430
https://x.com/levimotions/status/2101216618458071286
https://x.com/levimotions/status/2098018759139082523
https://x.com/levimotions/status/2093592341978186189
https://x.com/levimotions/status/2100914669842006114
https://x.com/levimotions/status/2095135140770959767
https://x.com/tomjullienvfx/status/2012595240180269376
https://x.com/tomjullienvfx/status/2091216635948318949
https://x.com/tomjullienvfx/status/2002045207924060594
https://x.com/GreySaurabh/status/2103361522705838475
https://x.com/GreySaurabh/status/2102999522108739714
https://x.com/GreySaurabh/status/2103861664525570375
https://x.com/GreySaurabh/status/2095841988268699742
https://x.com/vedu_boi/status/2083563586279064023
https://x.com/vedu_boi/status/2077834999735476291
https://x.com/vedu_boi/status/2085759947758068072
https://x.com/kirtanlb/status/2069452123524514243
https://x.com/kirtanlb/status/2071890767996649939
https://x.com/kirtanlb/status/2080299345140953231
https://x.com/kirtanlb/status/2066155306934251658
https://x.com/Rayanvisuals/status/2085015599810502923
https://x.com/Rayanvisuals/status/2088636088013525369
https://x.com/Rayanvisuals/status/2093711404662423732
https://x.com/Rayanvisuals/status/2093470794534040028
https://x.com/MotionBlahomyr/status/2079537409570533468
https://x.com/MotionBlahomyr/status/2080626297923867034
https://x.com/MotionBlahomyr/status/2090442574532059205
https://x.com/MotionBlahomyr/status/2071815662826123544
https://x.com/Editwhiz_Editor/status/2085012015689740416
https://x.com/Editwhiz_Editor/status/2042609789449179360
https://x.com/Editwhiz_Editor/status/2084277895476990183
https://x.com/Editwhiz_Editor/status/2035102222460362867
https://x.com/hlibtrazanov/status/2055217358260613262
https://x.com/hlibtrazanov/status/2084696469794091485
https://x.com/hlibtrazanov/status/2082045879049949419
https://x.com/hlibtrazanov/status/2062840781325455618
https://x.com/aizal_mp4/status/2028707434865340923
https://x.com/aizal_mp4/status/2103862408074985492
https://x.com/aizal_mp4/status/2047501220105920578
https://x.com/aizal_mp4/status/2024451395152220354
https://x.com/404ishan/status/2020383080251552248
https://x.com/404ishan/status/2010555733381906795
https://x.com/404ishan/status/2066698773930119395
https://x.com/404ishan/status/2015594399674069390
https://x.com/Jakubantalik/status/2079609095079047494
https://x.com/Jakubantalik/status/2084674723934318901
https://x.com/Jakubantalik/status/2087211438926348769
https://x.com/Jakubantalik/status/2069445373765239184
https://x.com/pranav_ae/status/2077791120311074921
https://x.com/pranav_ae/status/2084339997562618180
https://x.com/pranav_ae/status/2076326895386558600
https://x.com/sakshamfifth/status/2078742070915915948
https://x.com/sakshamfifth/status/2078036266655101324
https://x.com/sakshamfifth/status/2080638392203972965
https://x.com/BuffetDesigns/status/2091520125983957058
https://x.com/BuffetDesigns/status/2094060525605031945
https://x.com/BuffetDesigns/status/2091173375964229919
https://x.com/drylipz879/status/2098032109801910703
https://x.com/drylipz879/status/2099284876885361134
https://x.com/drylipz879/status/2093756124193521959
https://x.com/ezistu/status/2091957439104958470
https://x.com/ezistu/status/2101813483545260083
https://x.com/ezistu/status/2086525535132221938
https://x.com/Graphicsdaniel1/status/2094359776767402122
https://x.com/Graphicsdaniel1/status/2056455143235690657
https://x.com/Graphicsdaniel1/status/2048740570915295412
https://x.com/KnownasFahim/status/2011816538530333032
https://x.com/KnownasFahim/status/2093739495267131550
https://x.com/KnownasFahim/status/2090857679514423581
https://x.com/motionbyamine/status/2087826669700514157
https://x.com/motionbyamine/status/2095656255549223348
https://x.com/motionbyamine/status/2089017275344900298
https://x.com/Kendel4204k/status/2052300451379601492
https://x.com/Kendel4204k/status/2049075172666425838
https://x.com/Kendel4204k/status/2051965552386838934
https://x.com/Orbis_Studio/status/2089130363427627244
https://x.com/Orbis_Studio/status/2088776569896480905
https://x.com/Orbis_Studio/status/2080321475794317822
https://x.com/SkaleSolutions/status/2007081771054387521
https://x.com/SkaleSolutions/status/2103797412133584991
https://x.com/SkaleSolutions/status/2100210137093075131
https://x.com/Hazene_Edit/status/2088294581758779840
https://x.com/Hazene_Edit/status/2072711908369781202
https://x.com/Hazene_Edit/status/2001612527034069477
https://x.com/1zakariahq/status/2055980404075614290
https://x.com/1zakariahq/status/2043749293538857150
https://x.com/1zakariahq/status/2044801432117772570
https://x.com/mokshLNQ/status/2097374061018177733
https://x.com/mokshLNQ/status/2101571000714555666
https://x.com/mokshLNQ/status/2100645974503010611
https://x.com/bitmapstudioco/status/2086154831258087536
https://x.com/bitmapstudioco/status/2094424971376308536
https://x.com/bitmapstudioco/status/2096599297995440348
https://x.com/Jerrythe2d/status/2021619192961913191
https://x.com/Jerrythe2d/status/2070165763378598368
https://x.com/Jerrythe2d/status/2078865084009595062
https://x.com/nishvisualz/status/2102033455639052470
https://x.com/nishvisualz/status/2097695105985745350
https://x.com/nishvisualz/status/2100607863328850021
https://x.com/jamiesmotion/status/1967287800526667957
https://x.com/jamiesmotion/status/1996678678311587966
https://x.com/jamiesmotion/status/1976734758584340946
https://x.com/acevisuals0/status/2077702257110372613
https://x.com/acevisuals0/status/1996923419162493171
https://x.com/acevisuals0/status/1986058257916416063
https://x.com/privetavdey/status/2051961667068793167
https://x.com/privetavdey/status/2067234791297352030
https://x.com/privetavdey/status/2060370212734812621
https://x.com/valthvisuals/status/2100189262285287559
https://x.com/valthvisuals/status/2088353925963333850
https://x.com/valthvisuals/status/2077217732433482060
https://x.com/debxdesign/status/2077007492140405007
https://x.com/debxdesign/status/2095863345824018513
https://x.com/debxdesign/status/2096610808793116998
https://x.com/ramotion/status/1976307622820155502
https://x.com/ramotion/status/2087462441353396374
https://x.com/ramotion/status/1986378235211399221
https://x.com/1600Agency/status/2091230488287441111
https://x.com/1600Agency/status/2092063895275888661
https://x.com/1600Agency/status/2094213693730861453
https://x.com/mikididthis/status/2097007043823685999
https://x.com/mikididthis/status/2091860962034786329
https://x.com/mikididthis/status/2101385871559962956
https://x.com/Varcyyyy/status/2069925766222209119
https://x.com/Varcyyyy/status/2078913185646871006
https://x.com/Varcyyyy/status/2095238812020650017
https://x.com/gadzinski_/status/2041156092789399729
https://x.com/gadzinski_/status/2041597140636479980
https://x.com/gadzinski_/status/2064322041147248729
https://x.com/Y0uView/status/2011716649460908105
https://x.com/Y0uView/status/2081029698692546642
https://x.com/Y0uView/status/2015174096678703370
https://x.com/adrianinmotion/status/2092296842658943090
https://x.com/adrianinmotion/status/2093038309362540700
https://x.com/adrianinmotion/status/2099490214129349094
https://x.com/FlowMiv/status/2087297145238130690
https://x.com/FlowMiv/status/2102726816431566958
https://x.com/FlowMiv/status/2103435985283362895
https://x.com/yungsiege_/status/2099224724127830240
https://x.com/yungsiege_/status/2103465541558235266
https://x.com/yungsiege_/status/2101405132483330069
https://x.com/fifthrender/status/2101242227364352037
https://x.com/fifthrender/status/2102745734693183991
https://x.com/JohnSchnei99310/status/2103167869328732274
https://x.com/JohnSchnei99310/status/2079316082095980939
https://x.com/montrevee/status/2097062647774462210
https://x.com/nizarbouzeliffa/status/2060671878856094074
https://x.com/motionimo/status/2101252113544175847
https://x.com/motionimo/status/2091194570788806689
https://x.com/motionimo/status/2092099678032568673
https://x.com/LordyVisuals/status/2101996301067968815
https://x.com/LordyVisuals/status/2101264935552442418
https://x.com/bestdesignsonx/status/2092764028955242795
https://x.com/bestdesignsonx/status/2102065326582284550
https://x.com/bestdesignsonx/status/2098441436157067580
https://x.com/Motionlogstudio/status/2077467231689097558
https://x.com/Motionlogstudio/status/2080567320842469432
https://x.com/Motionlogstudio/status/2062625439386910778
"""


def status_of(url):
    handle = url.split("/")[3]
    return handle, url.rstrip("/").split("/")[-1]


def fetch(identifier):
    request = urllib.request.Request(
        f"https://cdn.syndication.twimg.com/tweet-result?id={identifier}&token=0",
        headers={"User-Agent": UA},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def best_mp4(tweet):
    details = tweet.get("mediaDetails") or []
    video = next((item for item in details if item.get("type") == "video" or (item.get("video_info") or {}).get("variants")), None)
    if not video:
        raise RuntimeError("no video")
    ranked = []
    for variant in (video.get("video_info") or {}).get("variants") or []:
        url = (variant.get("url") or "").split("?")[0]
        match = re.search(r"/(\d+)x(\d+)/", url)
        if "video/mp4" not in (variant.get("content_type") or "") and not match:
            continue
        area = int(match.group(1)) * int(match.group(2)) if match else 0
        ranked.append((area, int(variant.get("bitrate") or 0), url))
    if not ranked:
        raise RuntimeError("no mp4")
    ranked.sort(reverse=True)
    created = tweet["created_at"]
    made = created[:10] if "T" in created else datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y").date().isoformat()
    text = re.sub(r"https://t\.co/\S+", "", tweet.get("text") or "").strip()
    text = re.sub(r"\s+", " ", text)
    return ranked[0][2], made, text or "Motion study"


def download(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def probe(path):
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate",
        "-show_entries", "format=duration", "-of", "json", str(path),
    ], text=True)
    data = json.loads(raw)
    stream = data["streams"][0]
    num, den = stream["avg_frame_rate"].split("/")
    fps = float(num) / max(1.0, float(den))
    return int(stream["width"]), int(stream["height"]), float(data["format"]["duration"]), max(12, min(60, round(fps or 30)))


def smooth(source, dest, fps):
    subprocess.check_call([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
        "-map", "0:v:0", "-map", "0:a:0?",
        "-vf", "scale=trunc(iw*sar/2)*2:ih,setsar=1,pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-fps_mode", "cfr", "-r", str(fps),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-bf", "0",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(dest),
    ])


def scene_cuts(path):
    proc = subprocess.run([
        "ffmpeg", "-hide_banner", "-i", str(path), "-an",
        "-vf", "scale=320:-2,select='gt(scene,0.18)',showinfo", "-f", "null", "-",
    ], capture_output=True, text=True)
    return [float(item) for item in re.findall(r"pts_time:([\d.]+)", proc.stderr)]


def plan(duration, cuts):
    count = max(3, min(8, round(duration / 4.5)))
    if duration < 6:
        count = 3 if duration >= 3 else 2
    bounds = [0.0]
    for index in range(1, count):
        ideal = duration * index / count
        previous = bounds[-1]
        near = [cut for cut in cuts if previous + 0.8 < cut < duration - 0.8 and abs(cut - ideal) < duration / count * 0.45]
        bounds.append(round(min(near, key=lambda cut: abs(cut - ideal)) if near else ideal, 2))
    return [{"start": start, "end": round(bounds[i + 1] if i + 1 < len(bounds) else duration, 3)} for i, start in enumerate(bounds)]


def clock(seconds):
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


def draft_for(video, rid, sections):
    steps = 4
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    beats = []
    for index, section in enumerate(sections):
        length = max(0.24, section["end"] - section["start"])
        frames = []
        for step in range(steps):
            at = min(section["end"] - 0.05, section["start"] + length * (step + 0.5) / steps)
            dest = REF / f"{rid}-s{index}-{step}.jpg"
            frames.append(f"/references/{rid}-s{index}-{step}.jpg")
            command += [
                "-ss", f"{max(0, at):.2f}", "-i", str(video), "-frames:v", "1",
                "-vf", "scale=640:360:force_original_aspect_ratio=increase,crop=640:360,format=gray,eq=contrast=1.35:brightness=0.02",
                "-q:v", "4", str(dest),
            ]
        beats.append({"name": clock(section["start"]), "beats": [["still", frames[0], {"frames": frames}]]})
    subprocess.check_call(command)
    return {"palette": {"bg": "#111111", "fg": "#f4f4f4", "accent": "#ffffff"}, "sections": beats}


def load(name):
    return json.loads((REF / name).read_text(encoding="utf-8"))


def save(name, data, indent):
    (REF / name).write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def free_gb():
    usage = shutil.disk_usage(ROOT)
    return usage.free / 1024 ** 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--redraw", action="store_true")
    args = parser.parse_args()
    if args.redraw:
        sections = load("sections.json")
        drafts = load("drafts.json")
        count = 0
        order = list(sections)
        first = "x-2103605417171681430"
        if first in order:
            order.remove(first)
            order.insert(0, first)
        for rid in order:
            spans = sections[rid]
            if not rid.startswith("x-") or rid == "x-2062625439386910778" or not spans or drafts["drafts"].get(rid, {}).get("hand"):
                continue
            video = MEDIA / f"{rid}.mp4"
            if not video.exists():
                continue
            drafts["drafts"][rid] = draft_for(video, rid, spans)
            count += 1
            print(f"rough {count} {rid} {len(spans)}", flush=True)
            if count % 8 == 0:
                save("drafts.json", drafts, 1)
        save("drafts.json", drafts, 1)
        print(f"redrew {count}", flush=True)
        return
    MEDIA.mkdir(exist_ok=True)
    REF.mkdir(exist_ok=True)
    catalog = load("catalog.json")
    sections = load("sections.json")
    cuts = load("cuts.json")
    drafts = load("drafts.json")
    have = {item["id"] for item in catalog["references"]}
    jobs = []
    for line in URLS.splitlines():
        line = line.strip()
        if line.startswith("https://"):
            handle, identifier = status_of(line)
            jobs.append((handle, identifier, line))
    done = skipped = failed = 0
    print(f"queue {len(jobs)}", flush=True)
    for handle, identifier, url in jobs:
        rid = f"x-{identifier}"
        if rid in have and (MEDIA / f"{rid}.mp4").exists():
            skipped += 1
            continue
        if args.limit and done >= args.limit:
            break
        if free_gb() < 8:
            print("STOP disk under 8 GB", flush=True)
            break
        try:
            tweet = fetch(identifier)
            video_url, made, title = best_mp4(tweet)
            raw = MEDIA / f"{rid}.source.mp4"
            play = MEDIA / f"{rid}.mp4"
            if not raw.exists() or raw.stat().st_size < 10000:
                download(video_url, raw)
            width, height, duration, fps = probe(raw)
            if not play.exists() or play.stat().st_size < 10000:
                smooth(raw, play, fps)
            width, height, duration, _fps = probe(play)
            found = scene_cuts(play)
            spans = plan(duration, found)
            poster = REF / f"{rid}-0.jpg"
            subprocess.check_call([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-ss", str(round(duration * 0.3, 2)), "-i", str(play),
                "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "3", str(poster),
            ])
            entry = {
                "id": rid, "name": f"{handle} · {title[:64]}", "originalName": title[:200],
                "made": made, "duration": round(duration, 3), "width": width, "height": height,
                "src": f"/media/references/{rid}.mp4", "poster": f"/references/{rid}-0.jpg",
                "segments": [{"ref": rid, "in": 0.0, "out": round(duration, 3), "part": 1, "poster": f"/references/{rid}-0.jpg"}],
            }
            catalog["references"] = [item for item in catalog["references"] if item["id"] != rid] + [entry]
            sections[rid] = spans
            cuts[rid] = [round(cut, 2) for cut in found[:40]]
            drafts["drafts"][rid] = draft_for(play, rid, spans)
            save("catalog.json", catalog, 2)
            save("sections.json", sections, 1)
            save("cuts.json", cuts, None)
            save("drafts.json", drafts, 1)
            have.add(rid)
            done += 1
            print(f"OK {done} {rid} {made} {width}x{height} {duration:.1f}s {title[:48]}", flush=True)
        except Exception as error:
            failed += 1
            print(f"FAIL {rid} {url} {error}", flush=True)
    print(f"finished added {done} skipped {skipped} failed {failed}", flush=True)


if __name__ == "__main__":
    main()
