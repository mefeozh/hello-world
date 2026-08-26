"""
VocalRemover Pro - CLI Batch Runner
Usage:
    python vocal_remover.py "lil uzi vert" --limit 10
    python vocal_remover.py "https://youtu.be/..." --download-only
    python vocal_remover.py "kanye" --fast --limit 5
"""
import os
import sys
import shutil
import argparse
import tempfile
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("cli")


def main():
    parser = argparse.ArgumentParser(
        description="VocalRemover Pro CLI — batch acapella extraction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query",          help="Artist name, song name, YouTube URL, or Spotify URL")
    parser.add_argument("-l", "--library", default="library", help="Library output directory (default: library/)")
    parser.add_argument("-n", "--limit",   type=int, default=15, help="Top songs to fetch per artist (default: 15)")
    parser.add_argument("-d", "--download-only", action="store_true", help="Download audio only, skip UVR separation")
    parser.add_argument("--fast",          action="store_true", help="Enable fast separation mode (2-3× speedup)")
    parser.add_argument("--no-stage1",     action="store_true", help="Skip Stage 1 (Raw Vocal extraction)")
    parser.add_argument("--no-stage2",     action="store_true", help="Skip Stage 2 (De-Reverb)")
    parser.add_argument("--no-stage3",     action="store_true", help="Skip Stage 3 (De-Noise)")
    args = parser.parse_args()

    from src.config import MDX_DIR, VR_DIR, MDX_KIM_VOCAL_2, VR_DEECHO, VR_DENOISE, LIBRARY_DIR
    from src.core.resolver import detect_input_type, resolve_spotify_url, resolve_youtube_url, search_artists, get_top_tracks
    from src.core.downloader import download_audio
    from src.core.separator import run_stage, get_engine_description
    from src.utils.normalizer import normalize_artist_name, sanitize_filename, artist_library_paths

    library = os.path.abspath(args.library)
    os.makedirs(library, exist_ok=True)

    print(f"\n🎙️  VocalRemover Pro CLI")
    print(f"   Engine : {get_engine_description()}")
    print(f"   Library: {library}\n")

    kind = detect_input_type(args.query)
    tracks = []

    if kind == "spotify":
        meta = resolve_spotify_url(args.query)
        if meta:
            tracks = [{"artist": meta["artist"], "title": meta["title"], "full_title": meta["query"]}]
        else:
            sys.exit("Could not resolve Spotify URL.")
    elif kind == "youtube":
        meta = resolve_youtube_url(args.query)
        tracks = [{"artist": "YouTube Import", "title": "Direct Audio", "full_title": args.query}]
    else:
        artists = search_artists(args.query, limit=5)
        if not artists:
            sys.exit(f"No artists found for '{args.query}'")
        artist = artists[0]
        print(f"   Artist : {artist['name']} (via {artist['source']})")
        raw_tracks = get_top_tracks(artist, limit=args.limit)
        for t in raw_tracks:
            tracks.append({
                "artist":     normalize_artist_name(t["artist"]),
                "title":      t["title"],
                "full_title": t["full_title"],
            })

    print(f"   Queue  : {len(tracks)} track(s)\n{'─'*50}")

    error_count = 0
    for i, track in enumerate(tracks, 1):
        artist = normalize_artist_name(track["artist"])
        title  = track["title"]
        query  = track["full_title"]
        lib    = artist_library_paths(library, artist)
        safe   = sanitize_filename(title)

        print(f"\n[{i}/{len(tracks)}] {artist} — {title}")
        tmp = tempfile.mkdtemp(prefix="uvr_cli_")

        try:
            dl_dest_base = os.path.join(lib["downloaded"], f"{safe}")
            # Check if there is any cached file starting with safe title
            import glob
            cached_files = glob.glob(f"{dl_dest_base}*.wav")
            
            if cached_files and os.path.getsize(cached_files[0]) > 0:
                source = cached_files[0]
                print(f"  ✓ Download: cached ({os.path.basename(source)})")
                
                # Extract key & bpm from filename if present, or detect it
                from src.utils.music_analysis import detect_key_bpm
                base_name = os.path.splitext(os.path.basename(source))[0]
                if "BPM" in base_name:
                    safe = base_name
                else:
                    key_str, bpm_int = detect_key_bpm(source)
                    safe = f"{safe}_{bpm_int}BPM_{key_str}"
                    new_dl_dest = os.path.join(lib["downloaded"], f"{safe}.wav")
                    os.rename(source, new_dl_dest)
                    source = new_dl_dest
            else:
                source, _ = download_audio(query, tmp, artist_name=artist)
                from src.utils.music_analysis import detect_key_bpm
                key_str, bpm_int = detect_key_bpm(source)
                safe = f"{safe}_{bpm_int}BPM_{key_str}"
                dl_dest = os.path.join(lib["downloaded"], f"{safe}.wav")
                shutil.copyfile(source, dl_dest)
                source = dl_dest
                print(f"  ✓ Download: {dl_dest}")

            if args.download_only:
                continue

            last = source

            if not args.no_stage1:
                d1 = os.path.join(lib["raw_vocal"], f"{safe}_Vocals_Raw.wav")
                if not (os.path.isfile(d1) and os.path.getsize(d1) > 0):
                    stem = run_stage(MDX_DIR, MDX_KIM_VOCAL_2, source, tmp, "Stage 1", fast_mode=args.fast)
                    shutil.copyfile(stem, d1)
                last = d1
                print(f"  ✓ Stage 1: {d1}")

            if not args.no_stage2 and last:
                d2 = os.path.join(lib["dereverbed"], f"{safe}_Vocals_Dry.wav")
                if not (os.path.isfile(d2) and os.path.getsize(d2) > 0):
                    stem = run_stage(VR_DIR, VR_DEECHO, last, tmp, "Stage 2", fast_mode=args.fast)
                    shutil.copyfile(stem, d2)
                last = d2
                print(f"  ✓ Stage 2: {d2}")

            if not args.no_stage3 and last:
                d3 = os.path.join(lib["final_acapella"], f"{safe} (Acapella).wav")
                if not (os.path.isfile(d3) and os.path.getsize(d3) > 0):
                    stem = run_stage(VR_DIR, VR_DENOISE, last, tmp, "Stage 3", fast_mode=args.fast)
                    shutil.move(stem, d3)
                print(f"  ★ Final  : {d3}")

        except Exception as exc:
            print(f"  ✗ Error: {exc}")
            error_count += 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'─'*50}\n✅ Done — library at: {library}\n")
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
