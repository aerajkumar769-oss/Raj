"""A timed macOS display-awake utility with a small vocabulary window."""
import math
import platform
import subprocess
import time
import tkinter as tk
from tkinter import messagebox, ttk


# Offline vocabulary: cycles back to the first word after the list ends.
WORDS = (
    ("Resilient", "Able to recover after difficulties."),
    ("Curious", "Eager to learn or know more."),
    ("Diligent", "Working carefully with steady effort."),
    ("Serene", "Calm and peaceful."),
    ("Empathy", "The ability to understand another person's feelings."),
    ("Adapt", "To change to suit a new situation."),
    ("Candid", "Honest and direct."),
    ("Thrive", "To grow or develop successfully."),
    ("Gratitude", "A feeling of thankfulness."),
    ("Prudent", "Careful and sensible when making decisions."),
    ("Lucid", "Clear and easy to understand."),
    ("Persevere", "To keep trying despite difficulties."),
    ("Harmony", "A peaceful agreement or pleasing combination."),
    ("Insight", "A clear understanding of something."),
    ("Versatile", "Able to do many different things well."),
    ("Benevolent", "Kind and willing to help others."),
    ("Concise", "Expressed clearly in few words."),
    ("Vivid", "Very clear, bright, or detailed."),
    ("Integrity", "The quality of being honest and having strong principles."),
    ("Aspire", "To hope and work toward achieving something."),
    ("Abundant", "Existing in large amounts."),
    ("Meticulous", "Paying very careful attention to details."),
    ("Resourceful", "Good at finding ways to solve problems."),
    ("Tenacious", "Determined and unwilling to give up."),
    ("Tranquil", "Quiet and peaceful."),
    ("Eloquent", "Able to express ideas clearly and effectively."),
    ("Optimistic", "Hopeful that good things will happen."),
    ("Initiative", "The ability to act without waiting to be told."),
    ("Patience", "The ability to wait calmly or handle difficulties calmly."),
    ("Ingenious", "Clever and inventive."),
)


def vocabulary_frame(elapsed):
    """A new word each 30 seconds, then its meaning, typed at 0.1s/letter."""
    elapsed = max(0, elapsed)
    word, meaning = WORDS[int(elapsed // 30) % len(WORDS)]
    count = int((elapsed % 30) / 0.1) + 1
    return word[:count], meaning[:max(0, count - len(word) - 5)]


def duration_seconds(text):
    minutes = float(text)
    if not math.isfinite(minutes) or not 0 < minutes <= 1440:
        raise ValueError("Enter a duration greater than 0 and no more than 1440 minutes.")
    return max(1, math.ceil(minutes * 60))


class AwakeSession:
    def __init__(self, clock=time.monotonic, launch=subprocess.Popen):
        self.clock = clock
        self.launch = launch
        self.process = None
        self.deadline = None

    def start(self, seconds):
        self.stop()
        self.process = self.launch(["/usr/bin/caffeinate", "-di", "-t", str(seconds)])
        self.deadline = self.clock() + seconds

    def remaining(self):
        return max(0, math.ceil(self.deadline - self.clock())) if self.deadline else 0

    def stop(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait()
        self.process = None
        self.deadline = None


class Jiggler:
    def __init__(self, root):
        self.root = root
        self.session = AwakeSession()
        self.job = None
        self.started_at = None
        root.title("Jiggler")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.close)
        panel = ttk.Frame(root, padding=20)
        panel.grid()
        ttk.Label(panel, text="Keep your Mac awake", font=("Helvetica", 17, "bold")).grid(row=0, columnspan=2, pady=(0, 12))
        ttk.Label(panel, text="Timer (minutes)").grid(row=1, column=0, sticky="w")
        self.minutes = tk.StringVar(value="30")
        ttk.Entry(panel, textvariable=self.minutes, width=12).grid(row=1, column=1, padx=10)
        ttk.Label(panel, text="Learn a new word every 30 seconds").grid(row=2, columnspan=2, pady=10)
        self.character = ttk.Label(panel, text="—", font=("Helvetica", 28), width=16, anchor="center")
        self.character.grid(row=3, columnspan=2)
        self.meaning = ttk.Label(panel, text="", wraplength=340, anchor="center", justify="center")
        self.meaning.grid(row=4, columnspan=2, pady=10, sticky="ew")
        self.status = ttk.Label(panel, text="Ready", anchor="center")
        self.status.grid(row=5, columnspan=2, pady=10)
        self.start_button = ttk.Button(panel, text="Start", command=self.start)
        self.start_button.grid(row=6, column=0, sticky="ew")
        self.stop_button = ttk.Button(panel, text="Stop", command=self.stop, state="disabled")
        self.stop_button.grid(row=6, column=1, sticky="ew", padx=(10, 0))
        ttk.Label(panel, text="Words and meanings appear only in this window.").grid(row=7, columnspan=2, pady=(15, 0))

    def start(self):
        try:
            seconds = duration_seconds(self.minutes.get())
            self.session.start(seconds)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Could not start", str(exc))
            return
        self.started_at = self.session.clock()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.tick()

    def tick(self):
        self.job = None
        remaining = self.session.remaining()
        if remaining == 0:
            self.stop("Timer finished")
            return
        if self.session.process.poll() is not None:
            self.stop("Awake service stopped")
            messagebox.showerror("Awake service stopped", "caffeinate exited before the timer ended.")
            return
        word, meaning = vocabulary_frame(self.session.clock() - self.started_at)
        self.character.configure(text=word)
        self.meaning.configure(text=meaning)
        self.status.configure(text=f"Awake · {remaining // 60:02d}:{remaining % 60:02d} remaining")
        self.job = self.root.after(100, self.tick)

    def stop(self, status="Stopped"):
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
        self.session.stop()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status.configure(text=status)

    def close(self):
        self.stop()
        self.root.destroy()


def main():
    if platform.system() != "Darwin":
        raise SystemExit("Jiggler requires macOS and its built-in /usr/bin/caffeinate.")
    root = tk.Tk()
    Jiggler(root)
    root.mainloop()


if __name__ == "__main__":
    main()
