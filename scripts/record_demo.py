"""Record the 2-minute demo as a GIF: docs/demo.gif  (Playwright + Pillow).

Drives the real UI (streamlit must already be running) - types each question, waits
for the answer, captures frames along the way, then assembles them. Nothing is
staged: what the GIF shows is what the agent did.

    streamlit run ui/app.py --server.port 8502 --server.headless true
    python scripts/record_demo.py [--url http://localhost:8502] [--out docs/demo.gif]
"""
from __future__ import annotations

import argparse
import io
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

QUESTIONS = [
    "Quel est le modèle champion actuel ?",
    "C'est quoi la dérive (data drift) ?",
    "Y a-t-il de la dérive cette semaine ?",
    "Quelle est la latence p95 de l'API sur la dernière heure ?",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8502")
    ap.add_argument("--out", type=Path, default=Path("docs/demo.gif"))
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=820)
    ap.add_argument("--scale", type=float, default=0.6, help="GIF downscale factor")
    ap.add_argument("--timeout", type=int, default=120, help="seconds to wait per answer")
    args = ap.parse_args()

    frames: list[tuple[Image.Image, int]] = []   # (frame, duration_ms)

    def snap(page, ms: int) -> None:
        img = Image.open(io.BytesIO(page.screenshot(full_page=False))).convert("RGB")
        w, h = img.size
        img = img.resize((int(w * args.scale), int(h * args.scale)), Image.LANCZOS)
        frames.append((img.quantize(colors=128, method=Image.MEDIANCUT), ms))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_selector("textarea", timeout=120_000)
        time.sleep(2)
        snap(page, 1500)

        for q in QUESTIONS:
            box = page.locator("textarea").first
            box.click()
            box.type(q, delay=25)
            snap(page, 700)
            box.press("Enter")
            deadline = time.time() + args.timeout
            last = 0.0
            while time.time() < deadline:
                # the running status turns into 'Réponse prête' when the loop ends
                done = page.locator("text=Réponse prête").count() > 0
                if time.time() - last > 0.8:
                    snap(page, 400)
                    last = time.time()
                if done:
                    time.sleep(1.0)
                    page.mouse.wheel(0, 4000)
                    time.sleep(0.5)
                    snap(page, 3500)
                    break
                time.sleep(0.2)
            else:
                print(f"timeout waiting for: {q}")
        browser.close()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    first, *rest = frames
    first[0].save(args.out, save_all=True, append_images=[f for f, _ in rest],
                  duration=[d for _, d in frames], loop=0, optimize=True)
    print(f"{len(frames)} frames -> {args.out} ({args.out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
