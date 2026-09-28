
import streamlit as st
from pathlib import Path
from datetime import date
import hashlib
import json
import pandas as pd

APP_DIR = Path(__file__).parent
ASSET_DIR = APP_DIR / "assets"
VIDEO_DIR = APP_DIR / "videos"
DATA_FILE = APP_DIR / "assessment_history.json"
DRAFT_FILE = APP_DIR / "assessment_draft.json"
LOGO = ASSET_DIR / "vyayamai_logo.png"

EXERCISES = {
    "Chin Tuck": ("3 × 10", "Glide the head straight backward to create a gentle double chin. Do not look up or down.", "chin_tuck.mp4"),
    "Wall Angels": ("3 × 10", "Slide the arms upward and downward against a wall while keeping the trunk controlled.", "wall_angels.mp4"),
    "Thoracic Extension": ("2 × 10", "Gently extend through the upper/mid back while keeping the lower back controlled.", "thoracic_extension.mp4"),
    "Scapular Retraction": ("3 × 12", "Gently draw the shoulder blades backward and toward each other while keeping the shoulders down.", "scapular_retraction.mp4"),
    "Pelvic Control Practice": ("3 × 10", "Perform a small controlled posterior pelvic tilt and return to neutral.", "pelvic_tilt.mp4"),
    "Glute Bridge": ("3 × 12", "Lift the hips using the glutes, pause briefly, then lower slowly.", "glute_bridge.mp4"),
    "Bird Dog": ("3 × 8/side", "Extend one arm and the opposite leg while keeping the pelvis and trunk stable.", "bird_dog.mp4"),
    "Dead Bug": ("3 × 8/side", "Extend the opposite arm and leg while keeping the trunk and pelvis stable.", "dead_bug.mp4"),
}

PATTERN_MAP = {
    "Forward head posture": ["Chin Tuck", "Wall Angels", "Thoracic Extension"],
    "Shoulder asymmetry": ["Scapular Retraction", "Wall Angels"],
    "Rounded shoulders": ["Scapular Retraction", "Wall Angels", "Thoracic Extension"],
    "Pelvic level asymmetry": ["Pelvic Control Practice", "Glute Bridge"],
    "Poor core control": ["Bird Dog", "Dead Bug"],
}

st.set_page_config(page_title="VyayamAI", page_icon=str(LOGO), layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(0,0,0,.08);}
.hero {
    padding: 1.2rem 1.4rem; border-radius: 18px;
    background: linear-gradient(135deg, rgba(0,200,160,.13), rgba(0,120,110,.05));
    border: 1px solid rgba(0,180,150,.18);
}
.hero h1 {margin: 0; font-size: 2.2rem;}
.hero p {margin: .35rem 0 0; color: #555;}
.badge {
    display:inline-block; padding:.28rem .65rem; border-radius:999px;
    background:#e9fbf6; color:#087f68; font-size:.82rem; font-weight:600;
}
.small-card {
    padding: .9rem 1rem; border-radius: 14px;
    border: 1px solid rgba(0,0,0,.08); background: rgba(255,255,255,.65);
}
</style>
""", unsafe_allow_html=True)

def load_history():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_history(history):
    DATA_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def load_draft():
    if DRAFT_FILE.exists():
        try:
            return json.loads(DRAFT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_draft(draft):
    DRAFT_FILE.write_text(json.dumps(draft, indent=2), encoding="utf-8")


def clear_draft():
    if DRAFT_FILE.exists():
        try:
            DRAFT_FILE.unlink()
        except Exception:
            pass

def score_for_image(uploaded_file, view):
    # Prototype/demo heuristic. Replace with validated pose-estimation logic later.
    digest = hashlib.sha256(uploaded_file.getvalue() + view.encode()).hexdigest()
    return 76 + (int(digest[:8], 16) % 25)

def combined_score(front, side, back):
    return round(front * .30 + side * .40 + back * .30)

def detect_patterns(front, side, back):
    patterns = []
    if side < 88:
        patterns.append("Forward head posture")
    if front < 88:
        patterns += ["Shoulder asymmetry", "Pelvic level asymmetry"]
    if back < 88:
        patterns.append("Rounded shoulders")
    return patterns or ["No major screening pattern detected"]

def personalized_plan(patterns):
    selected = []
    for p in patterns:
        for ex in PATTERN_MAP.get(p, []):
            if ex not in selected:
                selected.append(ex)
    return selected or ["Chin Tuck", "Wall Angels", "Thoracic Extension"]

def exercise_card(name):
    dosage, instructions, filename = EXERCISES[name]
    st.markdown(f"**{name}** · `{dosage}`")
    video = VIDEO_DIR / filename
    if video.exists():
        st.video(str(video))
    else:
        st.caption("▶ Exercise video slot — add the generated MP4 to the videos folder.")
    st.write(instructions)
    st.caption("Safety: use controlled movement; stop if an exercise causes significant pain.")

history = load_history()
if "assessment_draft" not in st.session_state:
    st.session_state.assessment_draft = load_draft()

# ---------- Sidebar ----------
with st.sidebar:
    if LOGO.exists():
        st.image(str(LOGO), use_container_width=True)
    st.markdown("### VyayamAI")
    st.caption("AI-Based Personalized Fitness")
    st.divider()
    page = st.radio("Menu", [
        "🏠 Assessment",
        "📈 Progress",
        "🗓️ 6-Week Plan",
        "🏋️ Exercise Library",
        "ℹ️ About",
    ])
    st.divider()
    st.caption("Screening only — not a medical diagnosis.")

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <span class="badge">VyayamAI · Binary Brains</span>
  <h1>Personalized Posture Screening</h1>
  <p>Assess → Score → Identify → Exercise → Reassess → Track</p>
</div>
""", unsafe_allow_html=True)

if page == "🏠 Assessment":
    st.subheader("Assessment")
    st.write("Upload guided **front + side + back** posture images to create a baseline.")

    draft = st.session_state.assessment_draft

    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input(
            "User name",
            placeholder="Enter participant name",
            key="assessment_name",
            persist_state="session",
        )
    with c2:
        age = st.number_input(
            "Age", 10, 100, int(draft.get("age", 20)),
            key="assessment_age",
            persist_state="session",
        )

    f1, f2, f3 = st.columns(3)
    with f1:
        front_upload = st.file_uploader(
            "📷 Front view", ["jpg","jpeg","png"], key="front"
        )
        if front_upload is not None:
            draft["front_bytes"] = front_upload.getvalue().hex()
            draft["front_name"] = front_upload.name

    with f2:
        side_upload = st.file_uploader(
            "📷 Side view", ["jpg","jpeg","png"], key="side"
        )
        if side_upload is not None:
            draft["side_bytes"] = side_upload.getvalue().hex()
            draft["side_name"] = side_upload.name

    with f3:
        back_upload = st.file_uploader(
            "📷 Back view", ["jpg","jpeg","png"], key="back"
        )
        if back_upload is not None:
            draft["back_bytes"] = back_upload.getvalue().hex()
            draft["back_name"] = back_upload.name

    draft["name"] = name
    draft["age"] = int(age)

    front_bytes = bytes.fromhex(draft["front_bytes"]) if draft.get("front_bytes") else None
    side_bytes = bytes.fromhex(draft["side_bytes"]) if draft.get("side_bytes") else None
    back_bytes = bytes.fromhex(draft["back_bytes"]) if draft.get("back_bytes") else None

    if front_bytes and side_bytes and back_bytes:
        class UploadedBytes:
            def __init__(self, data):
                self._data = data
            def getvalue(self):
                return self._data

        front = UploadedBytes(front_bytes)
        side = UploadedBytes(side_bytes)
        back = UploadedBytes(back_bytes)

        front_s = score_for_image(front, "front")
        side_s = score_for_image(side, "side")
        back_s = score_for_image(back, "back")
        combined = combined_score(front_s, side_s, back_s)
        patterns = detect_patterns(front_s, side_s, back_s)

        draft.update({
            "front": front_s,
            "side": side_s,
            "back": back_s,
            "combined": combined,
            "patterns": patterns,
        })
        save_draft(draft)

        st.info("📝 Draft preserved while you navigate. It enters Progress only after Save Assessment.")
        st.subheader("Screening result")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Front", f"{front_s}/100")
        m2.metric("Side", f"{side_s}/100")
        m3.metric("Back", f"{back_s}/100")
        m4.metric("Combined", f"{combined}/100")

        st.subheader("Detected patterns")
        for p in patterns:
            st.write(f"• {p}")

        if combined < 85 or any("asymmetry" in p.lower() for p in patterns):
            st.warning("If there is pain or significant asymmetry, professional assessment is recommended.")

        st.subheader("Personalized starter plan")
        plan = personalized_plan(patterns)
        for i in range(0, len(plan), 2):
            a, b = st.columns(2)
            with a:
                exercise_card(plan[i])
            if i + 1 < len(plan):
                with b:
                    exercise_card(plan[i + 1])

        if st.button("💾 Save Assessment", type="primary"):
            history.append({
                "name": name or "Demo User",
                "age": int(age),
                "date": str(date.today()),
                "front": front_s, "side": side_s, "back": back_s,
                "combined": combined, "patterns": patterns
            })
            save_history(history)
            st.session_state.assessment_draft = {}
            clear_draft()
            st.success("Assessment saved successfully. This assessment is now in Progress.")

    else:
        st.info("Upload all three views to generate the combined screening result.")

elif page == "📈 Progress":
    st.subheader("Progress Tracking")
    if not history:
        st.info("No saved assessments yet.")
    else:
        df = pd.DataFrame(history)
        df.insert(0, "Stage", ["Week 0 — Baseline"] + [f"Reassessment {i}" for i in range(1, len(df))])
        st.dataframe(df[["Stage","date","front","side","back","combined"]], use_container_width=True)
        st.subheader("Combined score trend")
        st.line_chart(df.set_index("Stage")[["combined"]])
        st.caption("Use the workflow at Week 2, Week 4 and Week 6 to compare reassessments.")

elif page == "🗓️ 6-Week Plan":
    st.subheader("6-Week Personalized Program")
    if history:
        st.metric("Latest baseline / score", f"{history[-1]['combined']}/100")
    else:
        st.info("Complete an assessment first to establish Week 0 baseline.")

    plan = [
        ("Week 0 — Baseline", "Complete the 3-view assessment and save the baseline."),
        ("Week 1 — Foundation", "Follow the personalized starter exercises and focus on controlled form."),
        ("Week 2 — Reassessment", "Repeat the 3-view screening and compare with Week 0."),
        ("Week 3 — Progressive practice", "Continue the plan consistently."),
        ("Week 4 — Reassessment", "Repeat the screening and review the trend."),
        ("Week 5 — Consistency", "Continue the personalized routine and exercise videos."),
        ("Week 6 — Final reassessment", "Complete the final 3-view screening and compare the trend."),
    ]
    for title, body in plan:
        with st.expander(title):
            st.write(body)
    st.info("Six weeks is a planning framework, not a guarantee of recovery.")

elif page == "🏋️ Exercise Library":
    st.subheader("Exercise Library")
    st.write("Add your generated MP4 files to the `videos` folder. The app will automatically display them.")
    for name in EXERCISES:
        with st.expander(name):
            exercise_card(name)

else:
    st.subheader("About VyayamAI")
    st.markdown("""
### Core cycle
**Assess → Score → Identify → Exercise → Reassess → Track → Consult if needed**

### MVP features
- Front + Side + Back posture screening workflow
- Individual and combined score
- Screening pattern detection
- Personalized exercise mapping
- Exercise video library
- Week 0 baseline
- Week 2 / 4 / 6 reassessment workflow
- Progress history and trend chart
- Professional escalation message

### Technical note
This MVP uses a deterministic prototype heuristic so the complete workflow can be demonstrated without claiming clinical accuracy. For the production version, the screening function should be replaced by a validated computer-vision pose-estimation pipeline with professionally reviewed thresholds.

**VyayamAI is a posture-screening and fitness-support prototype, not a medical diagnostic system.**
""")
