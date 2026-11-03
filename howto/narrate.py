#!/usr/bin/env python3
"""narrate.py SCRIPT.md OUT.mp3 [--voice ID] [--model eleven_v3]

Reads a narration script (plain text or markdown; lines starting with '#'
and blank lines are kept as pauses, fenced code blocks are skipped because
they are shown on screen, not read aloud) and renders it with ElevenLabs.
Prints the character count before spending quota. Key: ELEVENLABS_API_KEY
."""
import argparse, os, pathlib, re, sys, json, urllib.request

def load_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if k: return k
    sys.exit("set ELEVENLABS_API_KEY")

def narration_text(md: str) -> str:
    out, in_code = [], False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code; continue
        if in_code: continue
        if line.startswith("#"):            # heading = a longer pause
            out.append(""); continue
        out.append(line)
    text = "\n".join(out)
    text = re.sub(r"`([^`]*)`", r"\1", text)          # drop backticks, keep words
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

ap = argparse.ArgumentParser()
ap.add_argument("script"); ap.add_argument("out")
ap.add_argument("--voice", default="SAz9YHcvj6GT2YYXdXww")   # River: relaxed, neutral, informative
ap.add_argument("--model", default="eleven_v3")
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
text = narration_text(pathlib.Path(a.script).read_text())
print(f"{len(text)} characters to render from {a.script}", file=sys.stderr)
if a.dry_run:
    print(text); sys.exit(0)
req = urllib.request.Request(
    f"https://api.elevenlabs.io/v1/text-to-speech/{a.voice}?output_format=mp3_44100_128",
    data=json.dumps({"text": text, "model_id": a.model,
                     "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.2, "speed": 0.95}}).encode(),
    headers={"xi-api-key": load_key(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
with urllib.request.urlopen(req, timeout=300) as r, open(a.out, "wb") as f:
    f.write(r.read())
print(f"wrote {a.out} ({os.path.getsize(a.out)} bytes)", file=sys.stderr)
