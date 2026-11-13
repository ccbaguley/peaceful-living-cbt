import gc
import json
import os
import random
import signal
import sys
import time
import urllib.error
import urllib.request

MODEL_NAME = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")

# Unified Persona: Swedish Kriminalvårdare + Norwegian Import Model + Dutch Restorative + Balanced Mindful Discipline
SYSTEM_PROMPT = """
You are a calm, respectful peaceful-living and Cognitive Behavioral Therapy (CBT) mentor 
modeled on the Swedish Kriminalvården 'personal officer' (kriminalvårdare) philosophy, 
Norway's Import Model (forvaltningssamarbeid), Dutch restorative principles, Motivational 
Interviewing (MI), Integrated Dual Disorder Treatment (IDDT), Individual Placement 
and Support (IPS), mindful self-discipline, and healthy emotional balance.

Core principles:
1. Mentorship over policing: Never lecture, shame, threaten, diagnose, prescribe medication, 
   or act as law enforcement.
2. Everyday normalization: Treat the user with dignity as an equal adult capable of change.
3. Healthy emotional balance: Acknowledge negative emotions (fear, anger, jealousy, greed, 
   revenge, hatred, fatalism) as temporary warning signals without suppressing them or letting 
   them dictate destructive actions; help channel energy into constructive positive anchors.
4. Community bridge (Import Model): Encourage connecting with normal community healthcare, 
   public employment agencies, libraries, and education rather than staying isolated.
5. Clinical boundaries: If the user describes acute psychosis, severe withdrawal, or imminent 
   harm, calmly direct them to external medical or psychiatric care immediately.
"""

EMERGENCY_AND_PSYCHOSIS_KEYWORDS = [
    "kill myself", "end my life", "suicide", "hurt someone", "going to attack",
    "overdose", "seizure", "detoxing cold turkey", "alcohol withdrawal", "benzo withdrawal",
    "hearing voices", "hallucinating", "psychosis", "people are watching me"
]

OFFLINE_TASK_BANK = {
    "1": [
        "Organize one small physical space (a desk drawer, backpack, or kitchen counter) for 10 minutes.",
        "Do a 10-minute mobility or bodyweight routine (pushups, squats, stretching) while counting every rep.",
        "Prepare a simple, nutritious meal or clean up dishes with full attention on the steps."
    ],
    "2": [
        "Learn a practical terminal or coding command and test it safely in a sandbox folder.",
        "Write down 3 concrete skills you have and outline one realistic job or volunteer role that uses them.",
        "Read an educational article or technical manual and summarize the 3 main takeaways in your own words."
    ],
    "3": [
        "Pick an object in the room and sketch it or describe its exact details for 10 minutes.",
        "Write a structured plan for tomorrow broken into 30-minute blocks.",
        "Practice a calm, 30-second self-introduction or boundary script out loud."
    ]
}

MONK_AND_MARTIAL_LESSONS = [
    {
        "title": "The Empty Boat (Zhuangzi / Monastic Non-Reactivity)",
        "lesson": "If an empty boat bumps into yours on a river, you do not get angry at the boat. When someone acts out of pain, fear, or ignorance, treat their reaction like an empty boat—steer calmly around it without taking on their storm.",
        "practice": "Next time someone speaks harshly or triggers social anxiety, silently say 'Empty boat' and relax your shoulders."
    },
    {
        "title": "Gongfu Means Patient Effort Over Time",
        "lesson": "In traditional Kung Fu, 'gongfu' does not mean fighting—it means mastery earned through steady, daily repetition. A master does not conquer others; a master conquers their own impatience and impulses.",
        "practice": "Choose one small daily discipline (making your bed, 5 minutes of stillness, or keeping a promise to yourself) and complete it with full focus."
    },
    {
        "title": "The Uncarved Block & Beginner's Mind",
        "lesson": "Shame tells you that your past defines your future. Monastic training teaches Beginner's Mind: every breath is a clean slate, unburdened by yesterday's mistakes.",
        "practice": "Release one regret from yesterday right now. Focus strictly on conducting the next hour with integrity."
    },
    {
        "title": "Rooted Stance, Calm Mind",
        "lesson": "When a tree has shallow roots, any wind knocks it over. When your feet are planted and your breath is slow, external chaos cannot easily move your center.",
        "practice": "Stand or sit with both feet flat on the floor, spine straight, and drop your center of gravity into your lower belly."
    }
]

NEGATIVE_EMOTIONS = {
    "1": ("Fear", "Signals perceived threat or social rejection; becomes harmful when it triggers avoidance or panic."),
    "2": ("Anger", "Signals a perceived boundary violation; becomes harmful when it drives aggression or hostility."),
    "3": ("Revenge", "A desire to 'get even'; locks you in the past and risks legal or personal harm."),
    "4": ("Jealousy", "Comparison and scarcity thinking; erodes self-worth and social trust."),
    "5": ("Greed", "Impulsive grasping for fast money, substances, or shortcuts without regard for consequences."),
    "6": ("Hatred", "Chronic resentment; consumes mental energy and blocks peaceful re-integration."),
    "7": ("Superstition / Fatalism", "Believing 'I am doomed' or 'bad luck controls me'; undermines personal agency.")
}

POSITIVE_EMOTIONS = {
    "1": ("Purpose / Constructive Desire", "Channeling energy into a clear, legal, meaningful goal."),
    "2": ("Grounded Self-Trust (Faith)", "Confidence built through small, repeatable daily actions."),
    "3": ("Goodwill & Empathy (Love)", "Respecting yourself and treating others with basic human decency."),
    "4": ("Enthusiasm", "Active engagement in learning, work, or healthy physical effort."),
    "5": ("Hope", "Realistic belief that steady habits today create better options tomorrow."),
    "6": ("Appreciation", "Noticing small, genuine positives in daily life without ignoring real challenges."),
    "7": ("Creative Drive", "Channeling intense inner energy into building, problem-solving, or skill mastery.")
}


def check_external_care_boundary(text: str) -> bool:
    """Mirrors Sweden's Forensic Psychiatric Care boundary & medical safety (never logged)."""
    lowered = text.lower()
    for trigger in EMERGENCY_AND_PSYCHOSIS_KEYWORDS:
        if trigger in lowered:
            print("\n" + "=" * 66)
            print("[EXTERNAL PSYCHIATRIC, MEDICAL & CRISIS CARE - NOT LOGGED]")
            print("In the Nordic model, acute psychiatric symptoms, severe withdrawal,")
            print("and crisis states require real medical professionals, not software.")
            print("• Suicide & Crisis Lifeline (US/Canada): Call or text 988")
            print("• SAMHSA Mental Health & Substance Helpline: 1-800-662-4357")
            print("• Withdrawal / Medical Emergency: Abruptly stopping alcohol or")
            print("  benzodiazepines can cause fatal seizures. Call 911 / 112 or seek")
            print("  supervised medical care immediately.")
            print("• International Helplines: https://findahelpline.com")
            print("=" * 66 + "\n")
            return True
    return False


def ask_local_ai(messages: list, fallback: str = None) -> str:
    """Communicates with local Ollama via Python standard library (zero pip installs)."""
    default_fallback = (
        "[Offline AI Note: Local Ollama service is not running right now.]\n"
        "Self-Guided Mentor Check: Pause for 60 seconds, separate objective facts from\n"
        "assumptions, and choose one small, legal routine for the next 15 minutes."
    )
    payload = json.dumps({
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", fallback or default_fallback)
    except urllib.error.URLError:
        return fallback or default_fallback
    except Exception as e:
        return fallback or f"[Offline AI Note: {e}]"


def clear_session_dict(session_data: dict):
    """Overwrites mutable dictionary entries and clears references in RAM."""
    for key, val in list(session_data.items()):
        if isinstance(val, str):
            session_data[key] = "0" * len(val)
    session_data.clear()
    gc.collect()


def clamp_score(raw_input: str) -> int:
    """Parses user score input and clamps strictly between 0 and 10."""
    val = int(raw_input.strip() or 0)
    return max(0, min(10, val))


# --- TOOL 2: ASI-INSPIRED RISK & NEEDS SELF-TRIAGE ---
def run_asi_needs_triage():
    print("\n--- Ephemeral Risk & Needs Self-Triage (ASI-Inspired) ---")
    print("Rate each area from 0 (steady) to 10 (urgent struggle). Nothing is saved.\n")

    try:
        anxiety_mood = clamp_score(input("• Anxiety, panic, or depressed mood (0-10): "))
        substance = clamp_score(input("• Substance cravings or relapse risk (0-10): "))
        aggression = clamp_score(input("• Anger, hostility, or aggressive impulses (0-10): "))
        antisocial = clamp_score(input("• Temptation toward illegal/harmful shortcuts or gambling (0-10): "))
        daily_life = clamp_score(input("• Housing, work, or daily structure stress (0-10): "))
    except ValueError:
        print("\nPlease enter valid numbers between 0 and 10.\n")
        return

        scores = {
        "Psychiatric / Mood Stabilization (Tool 5, 7, 11, or 12)": anxiety_mood,
        "Substance Recovery & Medical MAT Check (Tool 6, 7, or 13)": substance,
        "Aggression & Impulse Control (Tool 4, 6, 11, or 12)": aggression,
        "Våga Välja / Criminal Lifestyle & Gambling Reframing (Tool 6 or 12)": antisocial,
        "Community Services & Vocational Bridge (Tool 9 or 10)": daily_life,
    }

top_area = max(scores, key=scores.get)
top_score = scores[top_area]
    print("\n--- Your Ephemeral Session Roadmap ---")
    if top_score == 0:
        print("All areas are steady. Recommended focus: Tool 8 (Normalization) or Tool 11 (Meditation).")
    else:
        print(f"Primary Focus Today ({top_score}/10): {top_area}")
        if substance >= 7:
            print("• Medical Note: For severe opioid/alcohol cravings, evidence-based medications (MAT)")
            print("  like buprenorphine, methadone, or naltrexone reduce relapse and overdose risk.")
        if anxiety_mood >= 8:
            print("• Psychiatric Note: High distress detected. Start with Tool 3 (Box Breathing) or Tool 11")
            print("  (Guided Meditation) and use Tool 10 (Norway Import Bridge) for clinic intake.")
        if aggression >= 6 or antisocial >= 6:
            print("• Behavioral Note: Run Tool 4 (Urge Surfing) or Tool 12 (Emotional Balance),")
            print("  then lock onto a constructive task with Tool 9 (Productive Focus-Shift).")


--- TOOL 3: BOX BREATHING ---

def run_box_breathing(cycles: int = 4):
phases = [
("Breathe IN slowly through your nose", 4),
("HOLD your breath gently            ", 4),
("Breathe OUT slowly through mouth   ", 4),
("HOLD empty before next breath      ", 4),
]
print(f"\n--- Box Breathing ({cycles} Cycles | 4-4-4-4 Nervous System Reset) ---")
print("Steady your heart rate before making any decisions. Press Ctrl+C to stop.\n")
try:
for cycle in range(1, cycles + 1):
for label, duration in phases:
for second in range(1, duration + 1):
bar = "█" * second + "░" * (duration - second)
print(
f"\rCycle {cycle}/{cycles} | {label} [{bar}] {second}/{duration}s",
end="",
flush=True,
)
time.sleep(1)
print("\n\nSession complete. Notice your shoulders, jaw, and breathing pace.\n")
except KeyboardInterrupt:
print("\n\n[Box breathing stopped early.]\n")

--- TOOL 4: URGE SURFING TIMER ---

def run_urge_surfing(seconds: int = 60):
print(f"\n--- Impulse Delay & Urge Surfing ({seconds} Seconds) ---")
print("Urges rise like a wave, peak, and pass if you do not feed them. Press Ctrl+C to stop.\n")
try:
for remaining in range(seconds, 0, -1):
cycle = (seconds - remaining) % 12
if cycle < 4:
phase = "Breathe IN slowly... "
elif cycle < 8:
phase = "HOLD gently...       "
else:
phase = "Breathe OUT slowly..."
print(f"\rTime left: {remaining:2d}s | {phase}", end="", flush=True)
time.sleep(1)
print("\n\nWave complete. Notice if the intensity dropped even by 1 point.\n")
except KeyboardInterrupt:
print("\n\n[Timer stopped early.]\n")

--- TOOL 5: 5-STEP CBT THOUGHT RECORD ---

def run_thought_record():
print("\n--- 5-Step CBT Thought Record (Anxiety & Trigger Reframing) ---")
print("Nothing you type is saved to disk.\n")
data = {
"situation": input("1. Situation (Objective facts only): ").strip(),
"emotion": input("2. Emotion & Intensity (e.g., Social Anxiety 7/10, Anger 8/10): ").strip(),
"auto_thought": input("3. Automatic Thought (What went through your mind?): ").strip(),
"evidence_for": input("4. Evidence FOR this thought (Facts only): ").strip(),
"evidence_against": input("5. Evidence AGAINST this thought (Other explanations?): ").strip(),
}
check_external_care_boundary(" ".join(data.values()))
data["prompt"] = f"""
Review this CBT Thought Record using a calm, non-judgmental Scandinavian restorative tone:
- Situation: {data['situation']}
- Emotion: {data['emotion']}
- Automatic Thought: {data['auto_thought']}
- Evidence For: {data['evidence_for']}
- Evidence Against: {data['evidence_against']}
Provide:
1. One cognitive distortion possibly at play (e.g., mind reading, catastrophizing, hostile attribution).
2. A balanced, realistic alternative thought.
3. One grounded, constructive action right now.
"""
print("\nAnalyzing thought pattern offline...\n")
print(ask_local_ai([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": data["prompt"]}]))
clear_session_dict(data)
print("\n[Thought Record wiped from RAM.]\n")

--- TOOL 6: SPECIALIZED CBT TRACKS (ONE-TO-ONE & VÅGA VÄLJA) ---

def run_specialized_cbt_track():
print("\n--- Specialized CBT Behavioral Tracks (One-to-One / Våga Välja) ---")
print("Select the specific pattern you want to interrupt right now:")
print("1. Impulse Control & Problem-Solving (One-to-One style)")
print("2. Aggression & Hostile Attribution (De-escalation)")
print("3. Addiction & Criminal Lifestyle Triggers (Våga Välja / Dare to Choose)")
print("4. Severe Gambling or Compulsive Risk Urges")
print("5. Social Anxiety & Community Re-Integration Avoidance")
track_map = {
"1": "Impulse Control and Problem-Solving (One-to-One)",
"2": "Aggression and Hostile Attribution De-escalation",
"3": "Substance Addiction and Criminal Lifestyle Triggers (Våga Välja)",
"4": "Gambling and Compulsive Risk-Taking",
"5": "Social Anxiety and Community Re-Integration",
}
choice = input("\nChoose track (1-5): ").strip()
track_name = track_map.get(choice)
if not track_name:
print("Invalid selection.\n")
return
data = {
"trigger": input(f"\n[{track_name}]\nWhat situation or thought is pulling you toward an old reaction? ").strip(),
"consequence": input("If you act on that impulse, what happens 24 hours from now? ").strip(),
}
check_external_care_boundary(" ".join(data.values()))
data["prompt"] = f"""
Facilitate a brief, structured CBT & Motivational Interviewing exercise for: {track_name}.
- User's Current Trigger: {data['trigger']}
- User's 24-Hour Consequence Reflection: {data['consequence']}
Respond as a Swedish kriminalvårdare (supportive mentor):
1. Reflect back their own awareness of the 24-hour consequence without lecturing.
2. Identify the specific "permission-giving thought" or cognitive trap trying to justify the behavior.
3. Offer two realistic, self-respecting alternative choices for the next hour.
"""
print("\nWorking through behavioral track offline...\n")
print(ask_local_ai([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": data["prompt"]}]))
clear_session_dict(data)
print("\n[Behavioral track data wiped from RAM.]\n")

--- TOOL 7: INTEGRATED DUAL-DIAGNOSIS, MEDICAL & VOCATIONAL CHECK-IN ---

def run_integrated_checkin():
print("\n--- Integrated Dual-Diagnosis, Medical & Vocational Check-In ---")
print("Addresses overlapping mood, cravings, physical health, and work/routine stress.\n")
data = {
"mood": input("1. Psychiatric/Mood State (panic, low mood, racing thoughts): ").strip(),
"craving": input("2. Substance/Behavioral Craving (0-10 scale + trigger): ").strip(),
"medical": input("3. Physical/Medical Factors (sleep, missed meds, withdrawal signs?): ").strip(),
"vocational": input("4. Work/Daily Structure Stress (job search, conflict, isolation?): ").strip(),
}
check_external_care_boundary(" ".join(data.values()))
data["prompt"] = f"""
Provide a concise, non-judgmental 4-part response modeled on
Scandinavian/Dutch Integrated Dual Disorder Treatment (IDDT) and IPS vocational support:
- Mood/Psychiatric State: {data['mood']}
- Substance/Behavioral Craving: {data['craving']}
- Physical/Medical Factors: {data['medical']}
- Vocational/Routine Context: {data['vocational']}
Include:
1. Overlap Connection: How these factors may be reinforcing each other right now.
2. CBT & Craving Tool: One concrete cognitive or behavioral step.
3. Medical & Safety Reminder: Evidence-based medical guidance (e.g., supervised detox, MAT, medication adherence).
4. Vocational / Routine Micro-Step: One small, dignity-building daily or work action today.
"""
print("\nSynthesizing whole-person support plan offline...\n")
print(ask_local_ai([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": data["prompt"]}]))
clear_session_dict(data)
print("\n[Integrated Check-In wiped from RAM.]\n")

--- TOOL 8: PERSONAL OFFICER (KRIMINALVÅRDARE) DAILY NORMALIZATION ---

def run_personal_officer_checkin():
print("\n--- 'Personal Officer' (Kriminalvårdare) Normalization Check-In ---")
print("No judgment, no surveillance—just steady, everyday mentorship.\n")
data = {
"basics": input("1. Basics today (sleep, food, hygiene, medication taken?): ").strip(),
"win": input("2. One small thing you handled calmly or stayed away from today: ").strip(),
"next_24h": input("3. One ordinary, constructive task for the next 24 hours: ").strip(),
}
check_external_care_boundary(" ".join(data.values()))
data["prompt"] = f"""
Act as a Swedish personal officer (kriminalvårdare) doing an everyday normalization check-in.
- Daily Basics: {data['basics']}
- Small Win / Restraint Shown: {data['win']}
- Next 24-Hour Plan: {data['next_24h']}
Provide a brief, warm, grounded response that:
1. Validates their everyday routine and self-restraint as real progress.
2. Uses Motivational Interviewing to reinforce their autonomy and dignity.
3. Keeps the plan simple and achievable.
"""
print("\nConnecting with mentor guide offline...\n")
print(ask_local_ai([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": data["prompt"]}]))
clear_session_dict(data)
print("\n[Normalization check-in wiped from RAM.]\n")

--- TOOL 9: PRODUCTIVE FOCUS-SHIFT & BEHAVIORAL ACTIVATION ---

def run_focus_sprint(minutes: int = 10):
total_seconds = minutes * 60
print(f"\n--- {minutes}-Minute Deep Focus Sprint ---")
print("Keep your attention strictly on the task in front of you. Press Ctrl+C to finish early.\n")
try:
for remaining in range(total_seconds, 0, -1):
mins, secs = divmod(remaining, 60)
print(f"\rTime remaining: {mins:02d}:{secs:02d} | Stay engaged with your task...", end="", flush=True)
time.sleep(1)
print("\n\nSprint complete. Notice how shifting your attention changed your mental state.\n")
except KeyboardInterrupt:
print("\n\n[Focus sprint ended early.]\n")
def run_productive_focus_shift():
print("\n--- Productive Focus-Shift & Behavioral Activation ---")
print("Shifting into an absorbing, constructive task occupies working memory and stops rumination.\n")
print("What kind of focus fits your energy right now?")
print("1. Hands-On & Physical (organizing, cleaning, movement, cooking)")
print("2. Mental & Skill-Building (coding, reading, job prep, problem-solving)")
print("3. Creative & Structured Planning (writing, mapping tomorrow, communication prep)")
category = input("\nSelect a category (1-3): ").strip()
if category not in OFFLINE_TASK_BANK:
category = "1"
data = {"interest": input("Optional: Any specific interest or goal right now? (or press Enter to skip): ").strip()}
check_external_care_boundary(data["interest"])
fallback_task = random.choice(OFFLINE_TASK_BANK[category])
if data["interest"]:
data["prompt"] = f"""
Act as a supportive Scandinavian peaceful-living mentor using CBT Behavioral Activation.
The user wants to shift their mind away from rumination, anxiety, or urges onto a productive task.
- Category chosen: {category} (1=Physical/Hands-on, 2=Mental/Skill-building, 3=Creative/Planning)
- User's specific interest/goal: {data['interest']}
Suggest ONE concrete, absorbing 10-to-15-minute task they can start immediately right where they are.
Explain in 2 short sentences why this task occupies working memory and builds real-world capability.
"""
print("\nFinding an absorbing task offline...\n")
suggestion = ask_local_ai(
[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": data["prompt"]}],
fallback=f"Suggested Task: {fallback_task}"
)
print(suggestion)
else:
print(f"\nSuggested Task: {fallback_task}")
start_timer = input("\nStart a 10-minute focus sprint timer for this task now? (y/n): ").strip().lower()
if start_timer == "y":
run_focus_sprint(minutes=10)
clear_session_dict(data)
print("[Focus-shift session wiped from RAM.]\n")

--- TOOL 10: NORWAY IMPORT MODEL (FORVALTNINGSSAMARBEID) COMMUNITY BRIDGE ---

def run_norway_import_bridge():
print("\n--- Norway 'Import Model' Community & Service Bridge ---")
print("Norway's model avoids isolated silos by bringing normal community healthcare,")
print("employment, education, and housing services directly to the individual.")
print("Prepare a calm, practical 'Warm Handoff' with a real-world resource.\n")
print("Which community pillar do you want to connect with next?")
print("1. Community Healthcare / Dual-Diagnosis / MAT Clinic")
print("2. Employment, Vocational Rehab & Benefits Agency (NAV-style support)")
print("3. Housing Stability & Municipal Social Services")
print("4. Public Library, Trade School, or Free Adult Education")
pillar_map = {
"1": "Community Healthcare, Dual-Diagnosis Psychiatry, or MAT Clinic",
"2": "Public Employment Center, Vocational Rehabilitation, or Benefits Caseworker",
"3": "Housing Stability & Municipal Social Support",
"4": "Public Library, Trade Training, or Free Community Education",
}
choice = input("\nSelect a community pillar (1-4): ").strip()
pillar = pillar_map.get(choice, pillar_map["1"])
data = {
"barrier": input(f"\n[{pillar}]\nWhat makes reaching out or walking in feel difficult right now? ").strip(),
"goal": input("What is the single main thing you need help with from them? ").strip(),
}
check_external_care_boundary(" ".join(data.values()))
fallback_guide = (
f"\n[Self-Guided Warm Handoff Plan — {pillar}]\n"
f"1. Opening Script: 'Hi, I'm looking to get connected with {data['goal']}. Can you tell me what the first intake step is?'\n"
"2. What to Bring: Photo ID (or ask how to get a replacement ID), a list of current medications, and a pen.\n"
"3. Anxiety Buffer: You do not have to explain your whole life story at the front desk—just state your immediate goal.\n"
)
data["prompt"] = f"""
Act as a Norwegian coordinator applying Norway's 'Import Model' (forvaltningssamarbeid),
which connects individuals directly to normal municipal healthcare, labor (NAV), housing, and education.
- Target Community Pillar: {pillar}
- User's Social Anxiety / Practical Barrier: {data['barrier']}
- User's Concrete Goal: {data['goal']}
Provide a concise, dignity-centered 3-part 'Warm Handoff' preparation guide:
1. Exact Opening Script: A calm, 2-sentence script they can say or read when calling or walking in.
2. Practical Checklist: 3 basic items or questions to bring so the appointment goes smoothly.
3. Social Anxiety & Dignity Reframe: Remind them that public services exist for every citizen—using them is normal self-advocacy, not failure.
"""
print("\nPreparing your real-world service bridge offline...\n")
print(ask_local_ai(
[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": data["prompt"]}],
fallback=fallback_guide
))
clear_session_dict(data)
print("\n[Community bridge notes wiped from RAM.]\n")

--- TOOL 11: MARTIAL DISCIPLINE, MONK LESSONS & GUIDED MEDITATION ---

def run_guided_meditation(minutes: int = 3):
steps = [
(0.20, "Posture & Root: Sit upright or stand with feet flat. Drop your shoulders and unclench your jaw."),
(0.25, "Breath Anchor: Breathe slowly into your lower belly (hara/dantian). Feel the rise and fall."),
(0.30, "Observing Thoughts: Notice worries, anger, or urges like clouds drifting across an open sky—do not chase them."),
(0.25, "Quiet Resolve: Rest in stillness. You do not need to react to every feeling. Return gently to the room.")
]
total_seconds = minutes * 60
print(f"\n--- {minutes}-Minute Guided Stillness & Somatic Meditation ---")
print("Follow each stage quietly. Press Ctrl+C at any time to return.\n")
try:
elapsed = 0
for ratio, instruction in steps:
stage_seconds = max(1, int(total_seconds * ratio))
print(f"\n• {instruction}")
for _ in range(stage_seconds, 0, -1):
if elapsed >= total_seconds:
break
mins_left, secs_left = divmod(total_seconds - elapsed, 60)
print(f"\r  Remaining: {mins_left:02d}:{secs_left:02d} | Stillness in progress...", end="", flush=True)
time.sleep(1)
elapsed += 1
print("\n\nMeditation complete. Carry this quiet center into your next action.\n")
except KeyboardInterrupt:
print("\n\n[Meditation ended early.]\n")
def run_martial_and_monk_training():
print("\n--- Martial Discipline, Monk Lessons & Guided Meditation ---")
print("True strength is self-restraint, stillness under pressure, and steady daily practice.\n")
print("1. Guided Stillness Meditation (3-Minute Timed Practice)")
print("2. Deep Guided Meditation (5-Minute Timed Practice)")
print("3. Daily Monk Lesson & Kung Fu Discipline Reflection")
print("4. Apply Monastic Restraint to a Current Challenge (Offline AI / Self-Guided)")
choice = input("\nSelect an option (1-4): ").strip()
if choice == "1":
run_guided_meditation(minutes=3)
elif choice == "2":
run_guided_meditation(minutes=5)
elif choice == "3":
item = random.choice(MONK_AND_MARTIAL_LESSONS)
print(f"\n=== {item['title']} ===")
print(f"Lesson:   {item['lesson']}")
print(f"Practice: {item['practice']}\n")
elif choice == "4":
data = {"situation": input("\nDescribe the provocation, anxiety, or impulse testing your discipline: ").strip()}
check_external_care_boundary(data["situation"])
item = random.choice(MONK_AND_MARTIAL_LESSONS)
fallback = (
f"\n[{item['title']}]\n"
f"Lesson: {item['lesson']}\n"
f"Action: {item['practice']}\n"
)
data["prompt"] = f"""
Act as a calm martial arts master and monastic teacher grounded in CBT principles.
The user is facing this test of self-discipline: "{data['situation']}"
Respond briefly in 3 parts:
1. The Principle of Restraint: Explain why not reacting impulsively shows greater strength than lashing out or giving in.
2. Monastic Perspective: Share a brief, grounded insight on observing the emotion without letting it control their conduct.
3. One Disciplined Drill: Give one concrete physical or mental posture/breath action for the next 5 minutes.
"""
print("\nReflecting on disciplined response offline...\n")
print(ask_local_ai(
[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": data["prompt"]}],
fallback=fallback
))
clear_session_dict(data)
print("\n[Reflection wiped from RAM.]\n")
else:
print("Invalid selection.\n")

--- TOOL 12: EMOTIONAL BALANCE & TRANSMUTATION (HILL + CBT INTEGRATION) ---

def run_emotional_balance():
print("\n--- Emotional Balance & Transmutation (Hill + CBT Integration) ---")
print("Healthy balance is NOT pretending negative emotions do not exist.")
print("Negative emotions are temporary warning signals; positive emotions are your steering wheel.\n")
print("Step 1: Which negative emotion is pulling hardest at your mind right now?")
for key, (name, _) in NEGATIVE_EMOTIONS.items():
print(f"  {key}. {name}")
neg_choice = input("\nSelect a negative emotion (1-7): ").strip()
neg_name, neg_desc = NEGATIVE_EMOTIONS.get(neg_choice, NEGATIVE_EMOTIONS["1"])
print(f"\n[Signal Recognized: {neg_name}]")
print(f"Healthy Perspective: {neg_desc}\n")
print("Step 2: Which constructive positive emotion do you want to cultivate as a counterweight?")
for key, (name, _) in POSITIVE_EMOTIONS.items():
print(f"  {key}. {name}")
pos_choice = input("\nSelect a positive counterweight (1-7): ").strip()
pos_name, pos_desc = POSITIVE_EMOTIONS.get(pos_choice, POSITIVE_EMOTIONS["1"])
data = {"context": input(f"\nBriefly describe what triggered '{neg_name}' today (or press Enter to skip): ").strip()}
check_external_care_boundary(data["context"])
fallback = (
f"\n[Healthy Emotional Balance Plan: {neg_name} -> {pos_name}]\n"
f"1. Acknowledge Without Judgment: It is human to feel {neg_name.lower()}. Thank the alarm, then step out of the driver's seat.\n"
f"2. Channel Into {pos_name}: {pos_desc}\n"
"3. Immediate Action: Spend 10 minutes on one concrete, legal task that expresses this positive counterweight.\n"
)
if data["context"]:
data["prompt"] = f"""
Act as a grounded CBT and Scandinavian peaceful-living mentor integrating Napoleon Hill's
7 positive and 7 negative emotions with modern emotional regulation (no toxic positivity).
- Negative Emotion Active: {neg_name} ({neg_desc})
- Chosen Positive Counterweight: {pos_name} ({pos_desc})
- User Context: {data['context']}
Provide a brief, practical 3-part response:
1. Healthy Validation: Acknowledge the legitimate signal behind {neg_name} without justifying harmful behavior.
2. Balanced Perspective: Explain why neither suppressing {neg_name} nor letting it rule is healthy.
3. Practical Transmutation: Give one concrete, grounded action right now to channel that energy into {pos_name}.
"""
print("\nBuilding balanced emotional plan offline...\n")
print(ask_local_ai(
[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": data["prompt"]}],
fallback=fallback
))
else:
print(fallback)
clear_session_dict(data)
print("\n[Emotional balance reflection wiped from RAM.]\n")

--- TOOL 13: EVIDENCE-BASED MEDICAL, HARM-REDUCTION & VOCATIONAL GUIDE ---

def show_reference_guide():
print("\n--- Evidence-Based Medical, Harm-Reduction & Vocational Guide ---")
print("1. Medical & Withdrawal Safety:")
print("   • Alcohol & Benzodiazepines: Stopping abruptly can cause fatal seizures. Seek medical supervision.")
print("   • Medications for Addiction Treatment (MAT): Buprenorphine, methadone, and naltrexone are")
print("     evidence-based treatments introduced pre-release and in community care to prevent overdose.")
print("   • Dual-Diagnosis & External Psychiatric Care: Acute psychiatric symptoms require clinical care")
print("     from licensed psychiatrists and psychologists alongside behavioral tools.")
print("\n2. Vocational Re-Integration (IPS Principles):")
print("   • Zero-Exclusion: Meaningful work, education, or structured volunteering supports recovery.")
print("   • Micro-Steps: Spend 15 minutes organizing ID documents, listing practical skills, or practicing")
print("     a calm, brief explanation for employment gaps.")
print("\n3. Confidential 24/7 Resources:")
print("   • Suicide & Crisis Lifeline (US/Canada): Call or text 988")
print("   • SAMHSA National Helpline: 1-800-662-4357")
print("   • International Directory: https://findahelpline.com\n")
class PeacefulLivingApp:
def init(self):
self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
def wipe_all(self):
for msg in self.messages:
msg["content"] = "0" * len(msg["content"])
self.messages.clear()
gc.collect()
print("\n[Session ended. All RAM buffers overwritten and cleared.]")
# --- TOOL 1: EPHEMERAL PERSONAL OFFICER & CBT CHAT ---
def run_chat_mode(self):
print("\n--- Ephemeral 'Personal Officer' & CBT Chat ---")
print("Type '/menu' to return to the 14-tool menu, or '/wipe' to clear RAM and exit.\n")
while True:
user_input = input("You: ").strip()
if not user_input:
continue
if user_input.lower() == "/menu":
print("\nReturning to main menu...\n")
return False
if user_input.lower() in ["/wipe", "exit", "quit"]:
return True
check_external_care_boundary(user_input)
self.messages.append({"role": "user", "content": user_input})
reply = ask_local_ai(self.messages)
self.messages.append({"role": "assistant", "content": reply})
print(f"\nMentor: {reply}\n")
def main_menu(self):
def handle_exit(sig, frame):
self.wipe_all()
sys.exit(0)
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
while True:
print("==================================================================")
print("  NORDIC-DUTCH PEACEFUL LIVING & CBT SUITE (14 TOOLS)")
print("  [100% Offline | RAM-Only Privacy | Zero Disk Logging]")
print("==================================================================")
print(" 1. Ephemeral 'Personal Officer' (Kriminalvårdare) & CBT Chat")
print(" 2. Ephemeral Risk & Needs Self-Triage (ASI-Inspired)")
print(" 3. Box Breathing (4-4-4-4 Nervous System Reset)")
print(" 4. Urge Surfing Timer (60-Second Impulse Delay)")
print(" 5. 5-Step CBT Thought Record (Anxiety & Trigger Reframing)")
print(" 6. Specialized CBT Tracks (One-to-One / Våga Välja / Gambling)")
print(" 7. Integrated Check-In (Mood + Cravings + Medical + Work)")
print(" 8. 'Personal Officer' Everyday Normalization Check-In")
print(" 9. Productive Focus-Shift & 10-Min Behavioral Activation Sprint")
print("10. Norway 'Import Model' Community & Service Bridge")
print("11. Kung Fu Discipline, Monk Lessons & Guided Meditation")
print("12. Emotional Balance & Transmutation (Hill + CBT Integration)")
print("13. Evidence-Based Medical, MAT & Vocational Reference Guide")
print("14. Exit & Wipe All RAM")
choice = input("\nSelect a tool (1-14): ").strip()
if choice == "1":
should_exit = self.run_chat_mode()
if should_exit:
self.wipe_all()
break
elif choice == "2":
run_asi_needs_triage()
elif choice == "3":
run_box_breathing(cycles=4)
elif choice == "4":
run_urge_surfing(seconds=60)
elif choice == "5":
run_thought_record()
elif choice == "6":
run_specialized_cbt_track()
elif choice == "7":
run_integrated_checkin()
elif choice == "8":
run_personal_officer_checkin()
elif choice == "9":
run_productive_focus_shift()
elif choice == "10":
run_norway_import_bridge()
elif choice == "11":
run_martial_and_monk_training()
elif choice == "12":
run_emotional_balance()
elif choice == "13":
show_reference_guide()
elif choice == "14":
self.wipe_all()
break
else:
print("\nPlease enter a number between 1 and 14.\n")
if name == "main":
app = PeacefulLivingApp()
app.main_menu()
