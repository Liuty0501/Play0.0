# SwipeGate Serial Trigger

A small Arduino + Python “kiosk trigger” system:

- **Arduino** watches a digital input (e.g., relay/RFID reader output) and, after a stable signal, sends a single-character trigger (`C`) over **Serial**.
- **Python (PC kiosk)** shows a **full-screen camera feed** with an on-screen prompt, listens on the same Serial port, and **plays a video with sound** when it receives `C`.

This is useful for interactive installations like “swipe to enter gate / play animation”.

---

## How it works

1. Visitor swipes a card / activates a sensor.
2. Arduino detects the signal and prints `C` via `Serial.println("C")`.
3. Python listens on the configured Serial port and, when it detects `C`, it:
   - closes the camera window
   - plays the configured video using VLC
   - returns to the camera view after the video finishes

In the current Python script, Serial and media paths are configured as constants (port/baud/video/font/VLC). :contentReference[oaicite:0]{index=0}

---

## Repository structure (recommended)

```text
SwipeGate-Serial-Trigger/
├─ arduino/
│  └─ SwipeGateSerialTrigger/
│     └─ SwipeGateSerialTrigger.ino
├─ python/
│  └─ swipegate_kiosk.py
├─ assets/
│  ├─ animial.mp4
│  └─ font.ttf
├─ requirements.txt
└─ README.md
