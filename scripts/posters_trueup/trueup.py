"""True up Movie_posters_tmdb.yml with the Plex Movies library.

Runs inside the Kometa container (docker exec -i Kometa python - < trueup.py).
- Adds a commented-out placeholder for each Plex movie whose TMDb id is not in
  the file, in its alphabetical place (title as written, case-insensitive,
  then year, then edition).
- Removes commented-out placeholders whose movie is no longer in Plex. Live
  entries (with a poster) are never touched.
- Writes only when something changed, after a dated backup; keeps the last 7.
"""
import glob, json, os, re, shutil, sys, time, urllib.request
import ruamel.yaml

PATH = sys.argv[1] if len(sys.argv) > 1 else "/config/Movie_posters_tmdb.yml"
KEEP_BACKUPS = 7
MAX_REMOVALS = 25  # more than this looks like a Plex problem, not real removals
PLACEHOLDER = "  #   url_poster: https://theposterdb.com/api/assets/replaceMe/view"

y = ruamel.yaml.YAML(typ="safe")
cfg = y.load(open("/config/config.yml"))
req = urllib.request.Request(
    f"http://192.168.1.168:32400/library/sections/2/all?includeGuids=1&X-Plex-Token={cfg['plex']['token']}",
    headers={"Accept": "application/json"})
movies = json.load(urllib.request.urlopen(req, timeout=120))["MediaContainer"].get("Metadata", [])
if len(movies) < 1000:
    sys.exit(f"Plex returned only {len(movies)} movies; not changing anything")
plex = {}
for m in movies:
    for g in m.get("Guid", []):
        if g["id"].startswith("tmdb://"):
            plex.setdefault(int(g["id"][7:]), m)

text = open(PATH).read()
before = y.load(text)["metadata"]
lines = text.rstrip("\n").split("\n")
start = lines.index("metadata:") + 1
header, rest = lines[:start], lines[start:]

entry = re.compile(r"^  (# )?([0-9]+)[^:]*: # (.*) \((\d{4}|\?{4})\)(.*)$")
note, blocks = [], []  # block: [sort key, tmdb id, commented?, lines]
for l in rest:
    m = entry.match(l)
    if m:
        blocks.append([(m.group(3).lower(), m.group(4), m.group(5)), int(m.group(2)), bool(m.group(1)), [l]])
    elif not blocks:
        if l.strip():
            note.append(l)
    elif l.strip():
        blocks[-1][3].append(l)

present = {b[1] for b in blocks}
gone = [b for b in blocks if b[2] and b[1] not in plex]
if len(gone) > MAX_REMOVALS:
    print(f"{len(gone)} placeholders would be removed; skipping removals (check Plex)")
    gone = []
gone_ids = {id(b) for b in gone}
blocks = [b for b in blocks if id(b) not in gone_ids]

added = []
for tid, m in plex.items():
    if tid not in present:
        year = m.get("year", "????")
        blocks.append([(m["title"].lower(), str(year), ""), tid, True,
                       [f"  # {tid}: # {m['title']} ({year})", PLACEHOLDER]])
        added.append(f"{m['title']} ({year})")

if not added and not gone:
    print(f"No changes: {len(plex)} Plex movies, {len(blocks)} entries")
    sys.exit(0)

blocks.sort(key=lambda b: b[0])
new = "\n".join(header + note + [l for b in blocks for l in b[3]]) + "\n"
if y.load(new)["metadata"] != before:
    sys.exit("Live entries would change; not writing")

stamp = time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(PATH, f"{PATH}.bak-{stamp}")
with open(PATH, "w") as f:
    f.write(new)
for old in sorted(glob.glob(f"{PATH}.bak-*"))[:-KEEP_BACKUPS]:
    os.remove(old)

print(f"Added {len(added)}, removed {len(gone)} placeholders ({len(blocks)} entries)")
for t in sorted(added, key=str.lower):
    print(f"  + {t}")
for b in gone:
    print(f"  - {b[3][0].split('# ', 2)[-1]}")
