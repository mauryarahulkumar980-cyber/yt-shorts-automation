import os, json, random, asyncio, subprocess, textwrap, tempfile
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import edge_tts
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

W, H = 1080, 1920
OUT = Path("output")
OUT.mkdir(exist_ok=True)

# Original short-form scripts. Add your own entries to expand the rotation.
VIDEOS = [
    {"category":"SCIENCE","title":"Why does the Moon follow you? 🌙","hook":"Ever noticed the Moon seems to follow your car?","body":"It is not actually following you. The Moon is extremely far away, so its position barely changes as you move. Nearby trees and buildings rush past, making the Moon look like it is moving with you.","end":"Try watching it on your next evening drive.","tags":["science","space","facts"]},
    {"category":"PSYCHOLOGY","title":"Why do songs get stuck in your head? 🎵","hook":"Why does one song keep playing inside your head?","body":"Your brain sometimes repeats a catchy musical pattern because it is easy to remember. This is often called an earworm. Repeating the song, listening to its ending, or switching to another activity may help.","end":"What song is stuck in your head today?","tags":["psychology","music","facts"]},
    {"category":"ANIMALS","title":"Octopuses have three hearts 🐙","hook":"An octopus has three hearts. Seriously!","body":"Two hearts pump blood toward the gills. The third sends blood around the rest of the body. Their blood is blue because it uses a copper-containing protein to carry oxygen.","end":"Nature is full of surprises.","tags":["animals","ocean","facts"]},
    {"category":"HISTORY","title":"The first computer bug was an actual bug","hook":"The word computer bug has a surprising history.","body":"In 1947, engineers found a moth trapped in a relay of the Harvard Mark Two computer. They taped it into their logbook. The word bug was already used for technical faults, but the moth became a famous example.","end":"A tiny insect made computing history.","tags":["history","technology","facts"]},
    {"category":"SPACE","title":"A day on Venus is longer than its year","hook":"On Venus, one day is longer than one year.","body":"Venus rotates very slowly. It takes about 243 Earth days to spin once, but only about 225 Earth days to orbit the Sun. That means its rotation takes longer than its year.","end":"Space never stops being strange.","tags":["space","astronomy","facts"]},
    {"category":"MOTIVATION","title":"The two-minute rule for starting tasks","hook":"Struggling to start something important? Try two minutes.","body":"Make the first step so small that it feels easy. Read one page. Write one sentence. Do two minutes of practice. Starting reduces the mental resistance that often keeps you stuck.","end":"Start small. Build momentum.","tags":["motivation","productivity","habits"]},
    {"category":"GAMING","title":"Why do games use loading screens? 🎮","hook":"Why do games sometimes need loading screens?","body":"A game may need to move data from storage into memory, prepare textures, load sound, and build the next area. A loading screen gives the system time to prepare what you are about to see.","end":"Next time you load a game, you know what is happening.","tags":["gaming","technology","games"]},
    {"category":"NATURE","title":"Why is the sky blue?","hook":"Why does the sky look blue during the day?","body":"Sunlight contains many colours. Air molecules scatter shorter blue wavelengths more strongly than longer red wavelengths. That scattered blue light reaches your eyes from across the sky.","end":"A beautiful effect of our atmosphere.","tags":["science","nature","facts"]},
    {"category":"ANIMALS","title":"Butterflies taste with their feet 🦋","hook":"Butterflies can taste with their feet!","body":"Their feet have special chemical sensors. When a butterfly lands on a leaf, these sensors help it check whether the plant is suitable for laying eggs or feeding.","end":"Imagine tasting the world just by standing on it.","tags":["animals","nature","facts"]},
    {"category":"TECHNOLOGY","title":"How does airplane mode help? ✈️","hook":"What does airplane mode actually switch off?","body":"It disables your phone's cellular radio connections. On many phones, you can turn Wi-Fi and Bluetooth back on separately. The exact behaviour depends on your device and settings.","end":"A small setting with a practical purpose.","tags":["technology","phones","explained"]},
    {"category":"SCIENCE","title":"Why do we see lightning before thunder?","hook":"Lightning and thunder happen together. So why do you see one first?","body":"Light travels vastly faster than sound. The flash reaches your eyes almost instantly, while the sound takes longer to travel through the air to your ears.","end":"The sky is showing you a speed difference.","tags":["science","weather","facts"]},
    {"category":"HISTORY","title":"Why are keyboards not alphabetical?","hook":"Why isn't your keyboard arranged alphabetically?","body":"The familiar QWERTY layout developed during the era of mechanical typewriters. Its history is more complicated than the popular story that it was simply designed to slow typists down.","end":"Everyday technology has a long history.","tags":["history","technology","facts"]},
]

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, fnt, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if draw.textbbox((0,0), trial, font=fnt)[2] <= max_width:
            current = trial
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines

def make_card(text, category, index, total):
    img = Image.new("RGB", (W,H))
    px = img.load()
    top = (10 + index*13 % 35, 18 + index*7 % 30, 48 + index*9 % 60)
    bottom = (55 + index*11 % 65, 25 + index*5 % 35, 85 + index*7 % 70)
    for y in range(H):
        t = y / H
        c = tuple(int(top[k]*(1-t) + bottom[k]*t) for k in range(3))
        for x in range(W):
            px[x,y] = c
    d = ImageDraw.Draw(img)
    # Decorative circles
    d.ellipse((760,-160,1260,340), outline=(110,120,180), width=8)
    d.ellipse((-220,1420,330,1970), outline=(110,120,180), width=8)
    d.rounded_rectangle((70,100,1010,190), radius=35, fill=(245,190,70))
    d.text((105,119), category, font=font(38,True), fill=(20,20,35))
    d.text((80,300), f"{index+1:02d} / {total:02d}", font=font(34,True), fill=(205,210,230))
    f = font(76, True)
    lines = wrap(d, text, f, 900)
    y = 610
    for line in lines:
        bbox = d.textbbox((0,0), line, font=f)
        d.text(((W-(bbox[2]-bbox[0]))/2,y), line, font=f, fill="white", stroke_width=3, stroke_fill=(15,15,35))
        y += 105
    d.rounded_rectangle((90,1510,990,1650), radius=35, fill=(255,255,255))
    d.text((145,1550), "FOLLOW FOR MORE", font=font(48,True), fill=(20,20,35))
    d.text((85,1790), "Original short • Learn something new", font=font(29), fill=(220,220,235))
    return img

def make_video(item):
    # Divide narration into short visual cards; voice is generated as one continuous track.
    narration = " ".join([item["hook"], item["body"], item["end"]])
    chunks = textwrap.wrap(narration, width=72)
    # Group wrapped lines into 5-7 readable cards.
    cards = []
    words = narration.split()
    n = min(7, max(4, len(words)//13))
    chunk_size = max(1, (len(words)+n-1)//n)
    for i in range(0, len(words), chunk_size):
        cards.append(" ".join(words[i:i+chunk_size]))
    card_paths = []
    for i, sentence in enumerate(cards):
        p = OUT / f"card_{i:02d}.png"
        make_card(sentence, item["category"], i, len(cards)).save(p)
        card_paths.append(p)

    audio_path = OUT / "voice.mp3"
    async def tts():
        communicate = edge_tts.Communicate(narration, "en-US-AriaNeural", rate="+4%")
        await communicate.save(str(audio_path))
    asyncio.run(tts())

    # Create slideshow from cards, then mux narration. Duration is divided evenly.
    duration = max(18, min(42, len(words) * 0.42))
    per = duration / len(card_paths)
    concat = OUT / "slides.txt"
    with concat.open("w", encoding="utf-8") as f:
        for p in card_paths:
            f.write(f"file '{p.resolve()}'\n")
            f.write(f"duration {per:.3f}\n")
        f.write(f"file '{card_paths[-1].resolve()}'\n")
    silent = OUT / "silent.mp4"
    final = OUT / "short.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-vf","fps=30,format=yuv420p","-t",str(duration),"-an",str(silent)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg","-y","-i",str(silent),"-i",str(audio_path),"-c:v","copy","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(final)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return final

def upload(path, item):
    client_id = os.environ["YT_CLIENT_ID"]
    client_secret = os.environ["YT_CLIENT_SECRET"]
    refresh_token = os.environ["YT_REFRESH_TOKEN"]
    creds = Credentials(
        None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id, client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    creds.refresh(Request())
    youtube = build("youtube","v3",credentials=creds)
    description = (
        "A quick original explainer. Follow for more mixed-topic Shorts!\n\n"
        "Background visuals are original text-based graphics. Narration generated with text-to-speech.\n"
        "#Shorts #Facts #LearnSomethingNew " + " ".join("#"+t for t in item["tags"]) 
    )
    body = {
        "snippet": {"title": item["title"][:100], "description": description[:5000], "tags": item["tags"] + ["Shorts"], "categoryId":"27"},
        "status": {"privacyStatus": os.getenv("YT_PRIVACY","public"), "selfDeclaredMadeForKids": False}
    }
    media = MediaFileUpload(str(path), mimetype="video/mp4", chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    print("Uploaded:", "https://youtu.be/" + response["id"])

def main():
    # Rotate through the original library by day, so scheduled runs do not repeat yesterday's entry.
    day_number = datetime.now(timezone.utc).timetuple().tm_yday
    item = VIDEOS[(day_number - 1) % len(VIDEOS)]
    video = make_video(item)
    upload(video, item)

if __name__ == "__main__":
    main()
