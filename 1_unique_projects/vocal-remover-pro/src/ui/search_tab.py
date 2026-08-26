"""
VocalRemover Pro - Smart Resolver, Single Track & Album Explorer System

Features:
  - Input: Spotify Track Links, Spotify Artist Links, YouTube Links, or Text Queries.
  - Scenario A: Single Track Search & Direct Extraction / Queue.
  - Scenario B: Full Artist Catalog, Disambiguation, Top Songs & Complete Album Explorer.
"""
import os
import uuid
import time
import shutil
import tempfile
import streamlit as st

from src.core.resolver import (
    detect_input_type,
    resolve_spotify_url,
    resolve_youtube_url,
    resolve_spotify_playlist,
    resolve_youtube_playlist,
    search_songs,
    search_artists,
    get_top_tracks,
    get_artist_albums,
    get_album_tracks,
)
from src.utils.normalizer import normalize_artist_name, sanitize_filename, artist_library_paths
from src.config import MDX_DIR, VR_DIR, MDX_KIM_VOCAL_2, VR_DEECHO, VR_DENOISE
from src.core.downloader import download_audio
from src.core.separator import run_stage
from src.ui.queue_manager import save_persisted_queue, load_persisted_queue


def render_search_tab(settings: dict):
    st.markdown("### 🔍 Smart Resolver & Music Explorer")

    query = st.text_input(
        label="Search Query",
        placeholder="Artist name, song name, Spotify/YouTube link or playlist link",
        label_visibility="collapsed",
    )

    if not query.strip():
        st.info("💡 Paste a Spotify/YouTube link, or type any artist or song name above.")
        return

    kind = detect_input_type(query.strip())

    # ── Handle Spotify / YouTube Link Direct Resolvers ────────────────────────
    if kind == "spotify":
        with st.spinner("Resolving Spotify link..."):
            meta = resolve_spotify_url(query.strip())
        if meta:
            _render_single_track_result(meta, settings)
        else:
            st.warning("Could not resolve Spotify link. Try typing artist & track name.")
        return

    if kind == "spotify_playlist":
        with st.spinner("Resolving Spotify playlist..."):
            playlist_data = resolve_spotify_playlist(query.strip())
        if playlist_data:
            _render_playlist_result(playlist_data, settings)
        else:
            st.warning("Could not resolve Spotify playlist.")
        return

    if kind == "youtube":
        meta = resolve_youtube_url(query.strip())
        _render_single_track_result(meta, settings)
        return

    if kind == "youtube_playlist":
        with st.spinner("Resolving YouTube playlist..."):
            playlist_data = resolve_youtube_playlist(query.strip())
        if playlist_data:
            _render_playlist_result(playlist_data, settings)
        else:
            st.warning("Could not resolve YouTube playlist.")
        return

    # ── Text Query Handler: Dual Resolution (Songs vs Artists) ────────────────
    st.markdown("---")

    with st.spinner("Searching music databases..."):
        direct_songs = search_songs(query, limit=5)
        matched_artists = search_artists(query, limit=10)

    # 1. Direct Song Matches Section
    if direct_songs:
        st.markdown("#### 🎵 Direct Song Matches")
        for idx, song in enumerate(direct_songs):
            _render_song_card_scenario_a(song, settings, idx=idx)
        st.markdown("<br>", unsafe_allow_html=True)

    # 2. Artist Explorer & Discography System (Scenario B)
    if matched_artists:
        st.markdown("#### 🎤 Artist Discography Explorer")

        # Disambiguation selector
        artist_options = {
            f"{a['name']} ({a['genre']}) — [{a['source']}]": a
            for a in matched_artists
        }
        chosen_label = st.selectbox(
            "Select Artist:",
            options=list(artist_options.keys()),
            key="artist_select_box"
        )
        chosen_artist = artist_options[chosen_label]

        st.success(f"Matched Artist: **{chosen_artist['name']}** ({chosen_artist['genre']})")

        # Artist Navigation Tabs: Top Songs vs Albums
        artist_tab1, artist_tab2 = st.tabs(["🔥 Top Songs", "💿 Complete Albums"])

        # Tab 1: Top Songs Slider & Selection
        with artist_tab1:
            top_limit = st.slider("Number of Top Songs to load:", 5, 25, 10, step=5, key="top_song_slider")
            
            with st.spinner(f"Loading top {top_limit} tracks for '{chosen_artist['name']}'..."):
                top_tracks = get_top_tracks(chosen_artist, limit=top_limit)

            if top_tracks:
                col_q_top, col_dummy = st.columns([3, 1])
                with col_q_top:
                    if st.button(f"⚡ Queue ALL Top {len(top_tracks)} Songs", type="primary", use_container_width=True, key=f"q_all_top_{chosen_artist['name']}"):
                        for tr in top_tracks:
                            _enqueue_track(tr, settings.get("library_dir", "library"))
                        st.success(f"Added all {len(top_tracks)} tracks from **{chosen_artist['name']}** to Queue!")

                st.markdown("---")
                for idx, tr in enumerate(top_tracks):
                    _render_song_card_scenario_a(tr, settings, idx=100+idx)
            else:
                st.warning("No top tracks found for this artist.")

        # Tab 2: Complete Album Catalog Explorer
        with artist_tab2:
            with st.spinner(f"Fetching full album catalog for '{chosen_artist['name']}'..."):
                albums = get_artist_albums(chosen_artist)

            if albums:
                st.markdown(f"**Found {len(albums)} Album(s) & EPs:**")

                # Filter Albums vs Singles
                alb_filter = st.text_input("🔎 Filter albums by title:", placeholder="Search album name...", label_visibility="collapsed")
                filtered_albums = [a for a in albums if alb_filter.lower() in a["album_name"].lower()] if alb_filter.strip() else albums

                # Display Albums Grid (3 per row)
                num_cols = 3
                for i in range(0, len(filtered_albums), num_cols):
                    cols = st.columns(num_cols)
                    for j, col in enumerate(cols):
                        if i + j < len(filtered_albums):
                            alb = filtered_albums[i + j]
                            with col:
                                with st.container():
                                    if alb.get("artwork_url"):
                                        st.image(alb["artwork_url"], use_container_width=True)
                                    st.markdown(f"**{alb['album_name']}**")
                                    st.caption(f"📅 {alb['release_year']} · 🎵 {alb['track_count']} Tracks")
                                    
                                    if st.button(f"📂 Explore Album", key=f"alb_exp_{alb['album_id']}_{i+j}"):
                                        st.session_state.selected_album = alb

                # Selected Album Tracklist View
                if "selected_album" in st.session_state:
                    selected_alb = st.session_state.selected_album
                    
                    st.divider()
                    st.markdown(f"### 💿 Tracklist: **{selected_alb['album_name']}** ({selected_alb['release_year']})")
                    
                    with st.spinner(f"Loading tracks for '{selected_alb['album_name']}'..."):
                        album_tracks = get_album_tracks(selected_alb, chosen_artist['name'])
                        
                    if album_tracks:
                        col_q_alb, col_cls = st.columns([3, 1])
                        with col_q_alb:
                            if st.button(f"⚡ Queue ALL {len(album_tracks)} Tracks from '{selected_alb['album_name']}'", type="primary", use_container_width=True, key=f"q_all_alb_{selected_alb.get('album_id')}"):
                                for tr in album_tracks:
                                    _enqueue_track(tr, settings.get("library_dir", "library"))
                                st.success(f"Added all **{len(album_tracks)}** tracks from **{selected_alb['album_name']}** to Queue!")
                        with col_cls:
                            if st.button("❌ Close Album View", use_container_width=True, key="close_alb_view"):
                                del st.session_state.selected_album
                                st.rerun()

                        st.markdown("---")
                        for idx, tr in enumerate(album_tracks):
                            _render_song_card_scenario_a(tr, settings, idx=200+idx)
                    else:
                        st.warning("Could not load tracks for this album.")
            else:
                st.warning("No official albums found for this artist.")


# ─── Helper UI Components ──────────────────────────────────────────────────────

def _render_song_card_scenario_a(track: dict, settings: dict, idx: int):
    """Render a single song card for Scenario A with 1-click Extract and Queue buttons."""
    card_key = f"scen_a_{idx}_{track['artist']}_{track['title']}"
    
    with st.container():
        col_art, col_info, col_act1, col_act2 = st.columns([1, 4, 2, 2])
        
        with col_art:
            if track.get("artwork_url"):
                st.image(track["artwork_url"], width=55)
            else:
                st.markdown("🎵")
                
        with col_info:
            st.markdown(f"**{track['artist']}** — *{track['title']}*")
            st.caption(f"Duration: {track.get('duration', 'N/A')}")
            
        with col_act1:
            if st.button("🚀 Extract Now", key=f"ex_{card_key}", type="primary", use_container_width=True):
                _execute_instant_extraction(track, settings)
                
        with col_act2:
            if st.button("➕ Add to Queue", key=f"q_{card_key}", use_container_width=True):
                _enqueue_track(track, settings.get("library_dir", "library"))
                st.toast(f"Queued **{track['artist']} - {track['title']}**!", icon="✅")

        st.markdown("<hr style='margin: 8px 0; border-color: #1f1f2e;'>", unsafe_allow_html=True)


def _render_single_track_result(meta: dict, settings: dict):
    """Render a single resolved link track with instant extract & queue options."""
    st.success(f"Resolved Track: **{meta['artist']}** — *{meta['title']}*")
    col_ex, col_q = st.columns(2)
    with col_ex:
        if st.button("🚀 Extract Acapella Now", type="primary", use_container_width=True):
            _execute_instant_extraction(meta, settings)
    with col_q:
        if st.button("➕ Add to Queue", use_container_width=True):
            _enqueue_track(meta, settings.get("library_dir", "library"))
            st.toast(f"Queued **{meta['artist']} - {meta['title']}**!", icon="✅")


def _render_playlist_result(playlist_data: dict, settings: dict):
    title = playlist_data.get("playlist_title", "Unknown Playlist")
    tracks = playlist_data.get("tracks", [])
    
    st.success(f"📜 Playlist Resolved: **{title}** - {len(tracks)} Tracks")
    
    if not tracks:
        st.warning("No tracks found in playlist.")
        return
        
    if st.button(f"⚡ Queue ALL {len(tracks)} Playlist Tracks", type="primary", use_container_width=True, key=f"q_all_pl_{title}"):
        for tr in tracks:
            _enqueue_track(tr, settings.get("library_dir", "library"))
        st.success(f"Added all {len(tracks)} tracks to Queue!")
        
    st.markdown("---")
    st.markdown("#### Tracklist")
    
    selected_tracks = []
    select_all = st.checkbox("Select All Tracks", value=True, key=f"sel_all_pl_{title}")
    
    for idx, tr in enumerate(tracks):
        col_cb, col_info = st.columns([1, 11])
        with col_cb:
            is_sel = st.checkbox(" ", value=select_all, key=f"pl_cb_{idx}")
            if is_sel:
                selected_tracks.append(tr)
        with col_info:
            st.markdown(f"`{idx+1}.` **{tr.get('artist')}** — {tr.get('title')} `{tr.get('duration', 'N/A')}`")
            
    if st.button(f"➕ Queue Selected ({len(selected_tracks)})", key=f"q_sel_pl_{title}"):
        if selected_tracks:
            for tr in selected_tracks:
                _enqueue_track(tr, settings.get("library_dir", "library"))
            st.success(f"Added {len(selected_tracks)} selected tracks to Queue!")
        else:
            st.warning("No tracks selected.")


def _execute_instant_extraction(track: dict, settings: dict):
    """Execute 3-stage vocal extraction immediately and render audio players on the spot."""
    st.markdown(f"### 🎛️ Extracting Acapella: {track['artist']} - {track['title']}")
    
    progress_bar = st.progress(0)
    status_text  = st.empty()
    
    library_dir = settings["library_dir"]
    do_s1 = settings["do_stage1"]
    do_s2 = settings["do_stage2"]
    do_s3 = settings["do_stage3"]
    fast  = settings["fast_mode"]

    artist_name = normalize_artist_name(track["artist"])
    safe_title  = sanitize_filename(track["title"])
    full_query  = track.get("full_title") or track.get("query") or f"{artist_name} - {track['title']}"
    
    lib = artist_library_paths(library_dir, artist_name)
    tmp_dir = tempfile.mkdtemp(prefix="uvr_instant_")

    def _progress(pct: int, msg: str):
        progress_bar.progress(min(max(pct, 0), 100))
        status_text.markdown(f"**Progress ({pct}%):** {msg}")

    try:
        # 1. Download Studio Master Audio
        import glob
        dl_dest_base = os.path.join(lib["downloaded"], f"{safe_title}")
        cached_files = glob.glob(f"{dl_dest_base}*.wav")
        
        if cached_files and os.path.getsize(cached_files[0]) > 0:
            source = cached_files[0]
            _progress(20, "⬇️ Original studio audio cached in library.")
            
            from src.utils.music_analysis import detect_key_bpm
            base_name = os.path.splitext(os.path.basename(source))[0]
            if "BPM" in base_name:
                safe_title = base_name
            else:
                key_str, bpm_int = detect_key_bpm(source)
                safe_title = f"{safe_title}_{bpm_int}BPM_{key_str}"
                new_dl_dest = os.path.join(lib["downloaded"], f"{safe_title}.wav")
                os.rename(source, new_dl_dest)
                source = new_dl_dest
        else:
            dl_tmp, _ = download_audio(
                full_query,
                tmp_dir,
                artist_name=artist_name,
                expected_duration=track.get("duration"),
                progress_callback=_progress,
            )
            from src.utils.music_analysis import detect_key_bpm
            key_str, bpm_int = detect_key_bpm(dl_tmp)
            safe_title = f"{safe_title}_{bpm_int}BPM_{key_str}"
            dl_dest = os.path.join(lib["downloaded"], f"{safe_title}.wav")
            shutil.copyfile(dl_tmp, dl_dest)
            source = dl_dest

        last = source
        raw_path = dry_path = clean_path = None

        # 2. Stage 1 (Raw Vocal)
        if do_s1:
            dest1 = os.path.join(lib["raw_vocal"], f"{safe_title}_Vocals_Raw.wav")
            if os.path.isfile(dest1) and os.path.getsize(dest1) > 0:
                last = dest1
                _progress(50, "🎤 Stage 1 Raw Vocal cached.")
            else:
                stem1 = run_stage(MDX_DIR, MDX_KIM_VOCAL_2, source, tmp_dir, "Stage 1 — Raw Vocal", _progress, 20, 50, fast)
                shutil.copyfile(stem1, dest1)
                last = dest1
            raw_path = last

        # 3. Stage 2 (De-Reverb)
        if do_s2 and last:
            dest2 = os.path.join(lib["dereverbed"], f"{safe_title}_Vocals_Dry.wav")
            if os.path.isfile(dest2) and os.path.getsize(dest2) > 0:
                last = dest2
                _progress(75, "🎙️ Stage 2 Dry Vocal cached.")
            else:
                stem2 = run_stage(VR_DIR, VR_DEECHO, last, tmp_dir, "Stage 2 — De-Reverb", _progress, 50, 75, fast)
                shutil.copyfile(stem2, dest2)
                last = dest2
            dry_path = last

        # 4. Stage 3 (De-Noise)
        if do_s3 and last:
            dest3 = os.path.join(lib["final_acapella"], f"{safe_title} (Acapella).wav")
            if os.path.isfile(dest3) and os.path.getsize(dest3) > 0:
                last = dest3
                _progress(100, "🧹 Stage 3 Clean Acapella cached.")
            else:
                stem3 = run_stage(VR_DIR, VR_DENOISE, last, tmp_dir, "Stage 3 — De-Noise", _progress, 75, 100, fast)
                shutil.move(stem3, dest3)
                last = dest3
            clean_path = last

        _progress(100, "🎉 Acapella Extraction Complete!")
        st.balloons()

        # Render stem players side by side
        st.markdown(f"#### 🔊 Listen to Stems: {artist_name} - {track['title']}")
        cols = st.columns(4)
        stems = [
            ("🔊 Original Audio", source),
            ("🎤 Stage 1: Raw Vocal", raw_path),
            ("🎙️ Stage 2: Dry Vocal", dry_path),
            ("🧹 Stage 3: Clean Acapella", clean_path),
        ]
        for col, (label, p) in zip(cols, stems):
            with col:
                st.caption(label)
                if p and os.path.isfile(p):
                    st.audio(p)
                    with open(p, "rb") as f:
                        st.download_button(
                            "⬇️ Download WAV",
                            data=f,
                            file_name=os.path.basename(p),
                            mime="audio/wav",
                            key=f"instant_dl_{label}_{safe_title}",
                        )
                else:
                    st.info("Skipped")

    except Exception as exc:
        status_text.error(f"❌ Extraction Error: {exc}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _enqueue_track(track: dict, library_dir: str = "library"):
    if "queue" not in st.session_state or st.session_state.queue is None:
        st.session_state.queue = load_persisted_queue(library_dir)
    artist = normalize_artist_name(track.get("artist", "Unknown"))
    title  = track.get("title", "Unknown")
    st.session_state.queue.append({
        "id":         str(uuid.uuid4())[:8],
        "artist":     artist,
        "title":      title,
        "full_title": track.get("full_title") or track.get("query") or f"{artist} - {title}",
        "duration":   track.get("duration"),
        "status":     "Pending",
        "added_at":   time.strftime("%H:%M:%S"),
    })
    save_persisted_queue(library_dir, st.session_state.queue)
