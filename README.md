# Nordic-Dutch Peaceful Living & CBT Suite

An **offline-first, zero-persistence mental health, self-mastery, and peaceful living CLI** built for Ubuntu and Linux systems. Inspired by Scandinavian and Dutch restorative principles, Cognitive Behavioral Therapy (CBT), and mindful self-discipline, it helps users navigate anxiety, social anxiety, substance cravings, and impulsive behaviors while protecting their privacy in volatile RAM.

> **Important Notice:** This project is an open-source self-regulation and educational tool, not a replacement for licensed medical, psychiatric, or addiction care. See [SECURITY_AND_ETHICS.md](SECURITY_AND_ETHICS.md) for full clinical boundaries and crisis resources.

---

## Core Philosophy

1. **Zero-Persistence RAM Privacy:** All chats, Thought Records, and self-assessments live strictly in volatile memory and are overwritten upon exit or `Ctrl+C`. Nothing is ever written to disk.
2. **Zero External Dependencies:** Built using only Python 3's standard library (`json`, `time`, `urllib`, `gc`, `signal`, `os`). Runs immediately on standard Ubuntu installations without `pip` or `sudo`.
3. **Scandinavian & Dutch Principles of Normality:**
   - **Sweden (*Kriminalvården*):** Modeled on the non-coercive *Personal Officer (kriminalvårdare)* mentor dynamic, ASI-inspired needs triage, and accredited CBT tracks (*One-to-One* and *Våga välja*).
   - **Norway (*Forvaltningssamarbeid*):** Applies Norway's **Import Model** to connect users with real-world community healthcare, employment agencies, housing, and libraries rather than keeping them isolated.
   - **The Netherlands:** Emphasizes dignity, everyday normalization, harm reduction, and peaceful community re-integration.
4. **Mindful Discipline & Emotional Balance:** Integrates Kung Fu self-restraint, timed guided meditations, behavioral activation focus sprints, and balanced regulation of Napoleon Hill's positive and negative emotions.

---

## Included Tools (14-in-1 Suite)

1. **Ephemeral 'Personal Officer' & CBT Chat** — Non-judgmental motivational interviewing and CBT mentorship.
2. **Risk & Needs Self-Triage (ASI-Inspired)** — RAM-only check-in across mood, substance cravings, aggression, and daily stability.
3. **Box Breathing (4-4-4-4)** — Visual terminal progress bar for rapid nervous system regulation.
4. **Urge Surfing Timer (60s)** — Real-time impulse delay timer with paced breathing.
5. **5-Step CBT Thought Record** — Separates objective facts from cognitive distortions and hostile attribution.
6. **Specialized CBT Behavioral Tracks** — Targeted exercises for impulse control, aggression, addiction/criminal lifestyle triggers (*Våga välja*), gambling, and social anxiety.
7. **Integrated Dual-Diagnosis Check-In** — Addresses overlapping mood, cravings, physical health, and work stress simultaneously.
8. **Everyday Normalization Check-In** — Grounded daily routine and restraint reflection.
9. **Productive Focus-Shift & 10-Min Sprint** — Behavioral activation tool to redirect rumination into absorbing, constructive tasks.
10. **Norway 'Import Model' Service Bridge** — Prepares calm opening scripts and checklists for real-world clinics, job centers, and libraries.
11. **Kung Fu Discipline, Monk Lessons & Meditation** — 3-minute and 5-minute guided meditations plus non-reactive martial wisdom.
12. **Emotional Balance & Transmutation** — Channels negative warning signals (fear, anger, revenge, greed) into constructive anchors without toxic positivity.
13. **Evidence-Based Medical, MAT & Vocational Guide** — Offline reference for withdrawal safety, Medications for Addiction Treatment (MAT), and IPS employment steps.
14. **Instant RAM Wipe & Exit** — Overwrites active memory buffers and triggers garbage collection.

---

## Quick Start on Ubuntu / WSL

### 1. Run Immediately (No Dependencies Required)
```bash
git clone https://github.com
cd peaceful-living-cbt
python3 app.py
```
*(All breathing timers, guided meditations, focus sprints, triage tools, and offline fallback guides work out of the box without an AI model.)*

### 2. Optional: Enable Local AI Mentorship via Ollama
To enable interactive offline AI feedback across the chat and CBT exercises:
1. Install [Ollama](https://ollama.com) on your Linux machine or Windows host.
2. Pull a local open-weights model:
   ```bash
   ollama pull llama3.1
   ```
3. Ensure Ollama is running on `http://localhost:11434` (or set `export OLLAMA_URL="http://YOUR_IP:11434/api/chat"`) and launch `python3 app.py`.

---

## Ubuntu Privacy Hardening Tips
- **Disable Swap:** Run `sudo swapoff -a` before sensitive sessions so Linux never writes inactive RAM pages to disk.
- **Skip Shell History:** Launch with a leading space (` python3 app.py`) to keep the command out of `~/.bash_history`.

---

## Contributing
Contributions from developers, clinicians, social workers, and people with lived recovery experience are welcome. Please ensure any pull request preserves **zero disk logging**, **offline execution**, and **non-judgmental, evidence-based language**.

## License
Released under the [MIT License](LICENSE).
