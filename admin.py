#!/usr/bin/env python3
"""
Kickboxing Scoring System – Admin Interface
"""

# ====================================================
# IMPORTS
# ====================================================
import uuid
import tkinter as tk
import threading
import random
from tkinter import messagebox
from flask import Flask, request
from flask import Flask, render_template, jsonify  # ensure jsonify is imported
from flask import Flask, render_template, request, jsonify

# ====================================================
# GLOBAL VARIABLES & CONFIGURATIONS
# ====================================================
# Flask application instance (used for the judge web interface)
app = Flask(__name__)

# Global state variables
judge_tokens = {}         # Unique tokens for each judge (generated when a new fight starts)
fight_over = False        # Set to True when the winner is declared
blinking = False          # Controls if the winner text is blinking
winner_text_global = ""   # Winner announcement text
winner_color_global = ""  # Winner announcement text color
red_warning_count = 0
blue_warning_count = 0

# Indicator flags for the fight state
fighters_validated = False
settings_validated = False
fight_started = False     # Set to True once the fight timer starts
winner_label = None       # Reference to the winner label (if any)

# Judge scores: Each judge (1, 2, 3) has a score for Red and Blue
judge_scores = {
    1: {"red": 0, "blue": 0},
    2: {"red": 0, "blue": 0},
    3: {"red": 0, "blue": 0}
}

# Points mappings for tatami disciplines
tatami_points = {
    "POINT RED": {"red": 1, "blue": 0},
    "POINT BLUE": {"red": 0, "blue": 1},
    "HIGH KICK RED": {"red": 2, "blue": 0},
    "HIGH KICK BLUE": {"red": 0, "blue": 2},
    "JUMP KICK RED": {"red": 2, "blue": 0},
    "JUMP KICK BLUE": {"red": 0, "blue": 2},
    "HI-JUMP KICK RED": {"red": 3, "blue": 0},
    "HI-JUMP KICK BLUE": {"red": 0, "blue": 3},
}

# Points mappings for ring disciplines
ring_points = {
    "POINT RED": {"red": 1, "blue": 0},
    "POINT BLUE": {"red": 0, "blue": 1},
}

# ====================================================
# TKINTER SETUP & MAIN WINDOW
# ====================================================
root = tk.Tk()
root.title("Kickboxing Scoring System - Admin")
root.geometry("1200x900")
root.option_add("*Font", ("Arial", 12))

# Timer & round variables
round_duration = tk.IntVar(root, value=180)  # Default: 180 sec (3 minutes)
break_duration = tk.IntVar(root, value=45)     # Default: 45 sec
current_round = tk.IntVar(root, value=1)
total_rounds = tk.IntVar(root, value=3)
timer_running = False
mode_timer = "round"  # Can be "round" or "break"
time_left = round_duration.get()

# ====================================================
# NEW FIGHT SETUP FUNCTION (Reinitialize all fight variables)
# ====================================================
def new_fight(confirm=True):
    global fight_started, timer_running, fighters_validated, settings_validated, fight_over, blinking, time_left
    global judge_tokens, judge_scores, red_warning_count, blue_warning_count

    # Ask for confirmation to reset everything.
    answer = messagebox.askyesno("Confirm New Fight", "Do you really want to start a new fight? All current data will be lost.")
    if not answer:
        return

    # Reset all fight state flags.
    fight_started    = False
    timer_running    = False
    fighters_validated = False
    settings_validated = False
    fight_over       = False
    blinking         = False

    # Reset round and time variables.
    current_round.set(1)
    time_left = round_duration.get()  # round_duration is assumed to be a global control holding the base round time.

    # Reset judge tokens and judge scores.
    judge_tokens.clear()
    judge_scores = {
        1: {"red": 0, "blue": 0},
        2: {"red": 0, "blue": 0},
        3: {"red": 0, "blue": 0}
    }
    red_warning_count = 0
    blue_warning_count = 0

    # Generate new tokens for each judge.
    judge_tokens[1] = str(uuid.uuid4())
    judge_tokens[2] = str(uuid.uuid4())
    judge_tokens[3] = str(uuid.uuid4())

    # Reset fighter data fields (name, country, etc.).
    for entry in (red_name, red_country, blue_name, blue_country):
        entry.config(state="normal")
        entry.delete(0, tk.END)
    red_gender.set("Male")
    blue_gender.set("Male")
    red_gender_optionmenu.config(state="normal")
    blue_gender_optionmenu.config(state="normal")

    # Reset fight settings controls (total rounds, round duration, break duration, etc.).
    om_total_rounds.config(state="normal")
    om_round_duration.config(state="normal")
    om_break_duration.config(state="normal")

    # Reset timer (clock) display.
    minutes = time_left // 60
    seconds = time_left % 60
    timer_label.config(text=f"{minutes:02d}:{seconds:02d}", fg="black", font=("Arial", 20))
    round_label.config(text=f"Round: {current_round.get()} / {total_rounds.get()}")

    # Reset judge score labels.
    judge1_red_label.config(text="0")
    judge1_blue_label.config(text="0")
    judge2_red_label.config(text="0")
    judge2_blue_label.config(text="0")
    judge3_red_label.config(text="0")
    judge3_blue_label.config(text="0")

    # Reset the warning counter labels.
    warning_red_label.config(text="0")
    warning_blue_label.config(text="0")

    # Reset any winner display (if present).
    timer_label.config(font=("Arial", 20), fg="black")

    # Re-enable all control buttons as they would be at a new launch.
    # Disable the fight button until fighters and settings are properly validated.
    btn_fight.config(state="disabled")
    btn_stop.config(state="normal")
    btn_ko_red.config(state="normal")
    btn_ko_blue.config(state="normal")
    btn_warning_red.config(state="normal")
    btn_warning_blue.config(state="normal")

# ====================================================
# UI COMPONENTS: BUTTONS & FRAMES
# ====================================================

# -- Top Frame: New Fight Button --
frame_top = tk.Frame(root)
frame_top.pack(side="top", fill="x", pady=5)
new_fight_btn = tk.Button(frame_top, text="New Fight", fg="black", command=lambda: new_fight())
new_fight_btn.pack(expand=True)

# -- Fighter Data Section --
frame_fighter = tk.Frame(root)
frame_fighter.pack(pady=10)
tk.Label(frame_fighter, text="Red Corner", fg="red", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2)
tk.Label(frame_fighter, text="Name:", font=("Arial", 10)).grid(row=1, column=0)
red_name = tk.Entry(frame_fighter, font=("Arial", 10))
red_name.grid(row=1, column=1)
tk.Label(frame_fighter, text="Country/Club:", font=("Arial", 10)).grid(row=2, column=0)
red_country = tk.Entry(frame_fighter, font=("Arial", 10))
red_country.grid(row=2, column=1)

tk.Label(frame_fighter, text="Blue Corner", fg="blue", font=("Arial", 14, "bold")).grid(row=0, column=2, columnspan=2)
tk.Label(frame_fighter, text="Name:", font=("Arial", 10)).grid(row=1, column=2)
blue_name = tk.Entry(frame_fighter, font=("Arial", 10))
blue_name.grid(row=1, column=3)
tk.Label(frame_fighter, text="Country/Club:", font=("Arial", 10)).grid(row=2, column=2)
blue_country = tk.Entry(frame_fighter, font=("Arial", 10))
blue_country.grid(row=2, column=3)

# Gender variables and option menus
red_gender = tk.StringVar(value="Male")
blue_gender = tk.StringVar(value="Male")

def update_blue_gender(*args):
    """
    Update the Blue fighter gender: if Red is Female, set Blue to Female; otherwise set Blue to Male;
    then update weight options.
    """
    blue_gender.set("Female" if red_gender.get() == "Female" else "Male")
    update_weights()

red_gender_optionmenu = tk.OptionMenu(frame_fighter, red_gender, "Male", "Female", command=update_blue_gender)
red_gender_optionmenu.config(font=("Arial", 10))
red_gender_optionmenu.grid(row=3, column=1)
blue_gender_optionmenu = tk.OptionMenu(frame_fighter, blue_gender, "Male", "Female", command=lambda v: update_weights())
blue_gender_optionmenu.config(font=("Arial", 10))
blue_gender_optionmenu.grid(row=3, column=3)

# -- Validate Fighter Data Section --
frame_validate_fighter = tk.Frame(root)
frame_validate_fighter.pack(pady=10)
def validate_fighter_data():
    """
    Validate fighter information and lock the inputs.
    """
    global fighters_validated
    if not red_name.get() or not red_country.get() or not blue_name.get() or not blue_country.get():
        messagebox.showerror("Error", "All fighter data fields must be filled.")
        return
    answer = messagebox.askyesno("Confirm Fighter Data", "Finalize fighter data? (Inputs will be locked)")
    if answer:
        red_name.config(state="disabled")
        red_country.config(state="disabled")
        blue_name.config(state="disabled")
        blue_country.config(state="disabled")
        red_gender_optionmenu.config(state="disabled")
        blue_gender_optionmenu.config(state="disabled")
        fighters_validated = True
        enable_start_if_valid()

btn_validate_fighter = tk.Button(frame_validate_fighter, text="Validate Fighter Data", command=validate_fighter_data, font=("Arial", 10))
btn_validate_fighter.pack()

# -- Discipline, Categories, and Weight Options Section --
frame_options = tk.Frame(root)
frame_options.pack(pady=10)
tk.Label(frame_options, text="Discipline:", font=("Arial", 10)).grid(row=0, column=0)

# Discipline option menu (exact string values required for age dictionaries)
discipline = tk.StringVar(value="Full Contact")
discipline_menu = tk.OptionMenu(frame_options, discipline,
                                "Full Contact", "Low Kick", "K-1", "Point Fighting",
                                "Light Contact", "Kick Light", "Forms")
discipline_menu.config(font=("Arial", 10))
discipline_menu.grid(row=0, column=1)
discipline_label = tk.Label(frame_options, text="Discipline: N/A", font=("Arial", 10))
discipline_label.grid(row=1, column=1)

tk.Label(frame_options, text="Age Category:", font=("Arial", 10)).grid(row=2, column=0)
age_categories = tk.StringVar()
age_menu = tk.OptionMenu(frame_options, age_categories, "")
age_menu.config(font=("Arial", 10))
age_menu.grid(row=2, column=1)

tk.Label(frame_options, text="Weight Category:", font=("Arial", 10)).grid(row=3, column=0)
weight_categories = tk.StringVar()
weight_menu = tk.OptionMenu(frame_options, weight_categories, "")
weight_menu.config(font=("Arial", 10))
weight_menu.grid(row=3, column=1)

tk.Label(frame_options, text="Authorized Ages:", font=("Arial", 10)).grid(row=2, column=2)
authorized_ages_label = tk.Label(frame_options, text="N/A", font=("Arial", 10))
authorized_ages_label.grid(row=2, column=3, padx=10)

# ====================================================
# DATA DICTIONARIES FOR AGE & WEIGHT CATEGORIES
# ====================================================
authorized_ages_tatami = {
    "Children": "(7, 8, 9 years old)",
    "Younger Cadets": "(10, 11, 12 years old)",
    "Older Cadets": "(13, 14, 15 years old)",
    "Juniors": "(16, 17, 18 years old)",
    "Seniors": "(from age 19 to 40)",
    "Masters": "(from age 41 to 55)"
}
authorized_ages_ring = {
    "Younger Juniors": "(15, 16 years old)",
    "Older Juniors": "(17, 18 years old)",
    "Seniors": "(19–40 years old)"
}

ring_age_dict = {
    "Full Contact": ["Younger Juniors", "Older Juniors", "Seniors"],
    "Low Kick": ["Younger Juniors", "Older Juniors", "Seniors"],
    "K-1": ["Younger Juniors", "Older Juniors", "Seniors"]
}
tatami_age_dict = {
    "Point Fighting": ["Children", "Younger Cadets", "Older Cadets", "Juniors", "Seniors", "Masters"],
    "Light Contact": ["Children", "Younger Cadets", "Older Cadets", "Juniors", "Seniors", "Masters"],
    "Kick Light": ["Children", "Younger Cadets", "Older Cadets", "Juniors", "Seniors", "Masters"],
    "Forms": ["Children", "Younger Cadets", "Older Cadets", "Juniors", "Seniors", "Masters"]
}

weight_dict = {
    "Female_Ring": {
        "Younger Juniors": ["-36 kg", "-40 kg", "-44 kg", "-48 kg", "-52 kg", "-56 kg", "-60 kg", "+60 kg"],
        "Older Juniors": ["-48 kg", "-52 kg", "-56 kg", "-60 kg", "-65 kg", "-70 kg", "+70 kg"],
        "Seniors": ["-48 kg", "-52 kg", "-56 kg", "-60 kg", "-65 kg", "-70 kg", "+70 kg"]
    },
    "Ring_Male": {
        "Younger Juniors": ["-42 kg", "-45 kg", "-48 kg", "-51 kg", "-54 kg", "-57 kg", "-60 kg", "-63.5 kg", "-67 kg", "-71 kg", "-75 kg", "-81 kg", "+81 kg"],
        "Older Juniors": ["-51 kg", "-54 kg", "-57 kg", "-60 kg", "-63.5 kg", "-67 kg", "-71 kg", "-75 kg", "-81 kg", "-86 kg", "-91 kg", "+91 kg"],
        "Seniors": ["-51 kg", "-54 kg", "-57 kg", "-60 kg", "-63.5 kg", "-67 kg", "-71 kg", "-75 kg", "-81 kg", "-86 kg", "-91 kg", "+91 kg"]
    },
    "Tatami_Male": {
        "Children": ["-18 kg", "-21 kg", "-24 kg", "-27 kg", "-30 kg", "-33 kg", "-36 kg", "+36 kg"],
        "Younger Cadets": ["-28 kg", "-32 kg", "-37 kg", "-42 kg", "-47 kg", "+47 kg"],
        "Older Cadets": ["-32 kg", "-37 kg", "-42 kg", "-47 kg", "-52 kg", "-57 kg", "-63 kg", "-69 kg", "+69 kg"],
        "Juniors": ["-57 kg", "-63 kg", "-69 kg", "-74 kg", "-79 kg", "-84 kg", "-89 kg", "-94 kg", "+94 kg"],
        "Seniors": ["-57 kg", "-63 kg", "-69 kg", "-74 kg", "-79 kg", "-84 kg", "-89 kg", "-94 kg", "+94 kg"],
        "Masters": ["-63 kg", "-74 kg", "-84 kg", "-94 kg", "+94 kg"]
    },
    "Tatami_Female": {
        "Children": ["-18 kg", "-21 kg", "-24 kg", "-27 kg", "-30 kg", "-33 kg", "-36 kg", "+36 kg"],
        "Younger Cadets": ["-28 kg", "-32 kg", "-37 kg", "-42 kg", "-47 kg", "+47 kg"],
        "Older Cadets": ["-32 kg", "-37 kg", "-42 kg", "-46 kg", "-50 kg", "-55 kg", "-60 kg", "-65 kg", "+65 kg"],
        "Juniors": ["-50 kg", "-55 kg", "-60 kg", "-65 kg", "-70 kg", "+70 kg"],
        "Seniors": ["-50 kg", "-55 kg", "-60 kg", "-65 kg", "-70 kg", "+70 kg"],
        "Masters": ["-55 kg", "-65 kg", "+65 kg"]
    }
}

# ====================================================
# FUNCTIONS FOR UPDATING OPTIONS & VALIDATING SETTINGS
# ====================================================

def update_weights(*args):
    """
    Update weight options based on discipline, selected age category, and fighter gender.
    """
    selected_age = age_categories.get().strip()
    red_category_key = ("Tatami_Male" if discipline.get() in tatami_age_dict and red_gender.get() == "Male"
                        else "Tatami_Female" if discipline.get() in tatami_age_dict and red_gender.get() == "Female"
                        else "Ring_Male" if discipline.get() not in tatami_age_dict and red_gender.get() == "Male"
                        else "Female_Ring")
    blue_category_key = ("Tatami_Male" if discipline.get() in tatami_age_dict and blue_gender.get() == "Male"
                         else "Tatami_Female" if discipline.get() in tatami_age_dict and blue_gender.get() == "Female"
                         else "Ring_Male" if discipline.get() not in tatami_age_dict and blue_gender.get() == "Male"
                         else "Female_Ring")
    weight_menu['menu'].delete(0, 'end')
    if selected_age in weight_dict.get(red_category_key, {}):
        for weight in weight_dict[red_category_key][selected_age]:
            weight_menu['menu'].add_command(label=weight, command=lambda v=weight: weight_categories.set(v))
        weight_categories.set(weight_dict[red_category_key][selected_age][0])
    elif selected_age in weight_dict.get(blue_category_key, {}):
        for weight in weight_dict[blue_category_key][selected_age]:
            weight_menu['menu'].add_command(label=weight, command=lambda v=weight: weight_categories.set(v))
        weight_categories.set(weight_dict[blue_category_key][selected_age][0])
    else:
        weight_categories.set("N/A")
    update_authorized_ages()

def update_authorized_ages():
    """
    Update the 'Authorized Ages' label based on the selected age category.
    """
    cat = age_categories.get().strip()
    if discipline.get() in tatami_age_dict:
        if cat in authorized_ages_tatami:
            authorized_ages_label.config(text=authorized_ages_tatami[cat], font=("Arial", 10))
        else:
            authorized_ages_label.config(text="N/A", font=("Arial", 10))
    else:
        if cat in authorized_ages_ring:
            authorized_ages_label.config(text=authorized_ages_ring[cat], font=("Arial", 10))
        else:
            authorized_ages_label.config(text="N/A", font=("Arial", 10))

def update_options(*args):
    """
    Update the discipline label and refresh age category options based on the selected discipline.
    """
    selected_discipline = discipline.get().strip()
    print("Selected discipline:", selected_discipline)  # Debug output
    
    if selected_discipline in tatami_age_dict:
        discipline_label.config(text=f"Tatami Discipline ({selected_discipline})", font=("Arial", 10))
        age_dict = tatami_age_dict
    else:
        discipline_label.config(text=f"Ring Discipline ({selected_discipline})", font=("Arial", 10))
        age_dict = ring_age_dict
        
    age_menu['menu'].delete(0, 'end')
    if selected_discipline in age_dict:
        for category in age_dict[selected_discipline]:
            age_menu['menu'].add_command(label=category, command=lambda v=category: age_categories.set(v))
        age_categories.set(age_dict[selected_discipline][0])
    update_weights()

# Set up traces to automatically update options when discipline or age category changes
discipline.trace_add("write", lambda *args: update_options())
age_categories.trace_add("write", lambda *args: update_weights())

# Initialize options with default values so that they no longer show "N/A"
update_options()

def validate_fight_settings():
    """
    Finalize fight settings and lock editing.
    """
    global settings_validated, time_left
    answer = messagebox.askyesno("Confirm Fight Settings", "Are you sure you want to finalize fight settings? They will be locked for editing.")
    if answer:
        om_total_rounds.config(state="disabled")
        om_round_duration.config(state="disabled")
        om_break_duration.config(state="disabled")
        settings_validated = True
        enable_start_if_valid()
        if not fight_started:
            time_left = round_duration.get()
            minutes = time_left // 60
            seconds = time_left % 60
            timer_label.config(text=f"{minutes:02d}:{seconds:02d}", fg="black")
            round_label.config(text=f"Round: {current_round.get()} / {total_rounds.get()}")

# ====================================================
# FIGHT SETTINGS UI SECTION
# ====================================================
frame_settings = tk.Frame(root)
frame_settings.pack(pady=10)
tk.Label(frame_settings, text="Fight Settings", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2)
tk.Label(frame_settings, text="Number of Rounds:", font=("Arial", 10)).grid(row=1, column=0)
om_total_rounds = tk.OptionMenu(frame_settings, total_rounds, 3, 5, 7)
om_total_rounds.config(font=("Arial", 10))
om_total_rounds.grid(row=1, column=1)
tk.Label(frame_settings, text="Round Duration (sec):", font=("Arial", 10)).grid(row=2, column=0)
om_round_duration = tk.OptionMenu(frame_settings, round_duration, 60, 90, 120, 180)
om_round_duration.config(font=("Arial", 10))
om_round_duration.grid(row=2, column=1)
tk.Label(frame_settings, text="Break Duration (sec):", font=("Arial", 10)).grid(row=3, column=0)
om_break_duration = tk.OptionMenu(frame_settings, break_duration, 45, 60)
om_break_duration.config(font=("Arial", 10))
om_break_duration.grid(row=3, column=1)

btn_validate_settings = tk.Button(frame_settings, text="Validate Fight Settings", command=validate_fight_settings, font=("Arial", 10))
btn_validate_settings.grid(row=4, column=0, columnspan=2, pady=5)

# ====================================================
# TIMER & ROUND DISPLAY SECTION
# ====================================================
frame_timer = tk.Frame(root)
frame_timer.pack(pady=10)
round_label = tk.Label(frame_timer, text=f"Round: {current_round.get()} / {total_rounds.get()}", font=("Arial", 14))
round_label.pack(pady=5)
timer_label = tk.Label(frame_timer, text="00:00", font=("Arial", 20))
timer_label.pack(pady=5)

def update_timer():
    """
    Update the countdown timer and manage round transitions.
    
    When the fight time expires during a round:
      - If there are rounds remaining, the timer switches to break mode.
      - Else, the fight stops and the winner is determined based on the favorable judges.
    """
    global time_left, timer_running, mode_timer, current_round, total_rounds
    if timer_running and time_left > 0:
        minutes = time_left // 60
        seconds = time_left % 60
        timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
        time_left -= 1
        root.after(1000, update_timer)
    elif time_left <= 0:
        if mode_timer == "round":
            # If there is another round to be played, start a break period.
            if current_round.get() < total_rounds.get():
                mode_timer = "break"
                time_left = break_duration.get()
                timer_label.config(fg="red")
                round_label.config(text=f"Break after Round {current_round.get()}")
                root.after(1000, update_timer)
            else:
                # No more rounds: stop the fight and determine the winner by favorable judges.
                timer_running = False
                declare_winner_by_judges()
        elif mode_timer == "break":
            # Transition back to a new round after a break.
            current_round.set(current_round.get() + 1)
            mode_timer = "round"
            time_left = round_duration.get()
            timer_label.config(fg="black")
            round_label.config(text=f"Round: {current_round.get()} / {total_rounds.get()}")
            root.after(1000, update_timer)

def start_fight():
    """
    Initialize and start the fight timer; tokens have already been generated in new_fight().
    """
    global timer_running, fight_started, current_round, total_rounds, time_left, judge_tokens
    if not fight_started:
        fight_started = True
        current_round.set(1)
        time_left = round_duration.get()
        round_label.config(text=f"Round: {current_round.get()} / {total_rounds.get()}")
        # Note: No new token generation here
        
    if not timer_running:
        timer_running = True
        update_timer()
    enable_fight_controls()

def stop_fight():
    """
    Stop (pause) the fight timer; if fight is over, stop blinking.
    """
    global timer_running, blinking, fight_over
    if fight_over:
        blinking = False
        timer_label.config(fg=winner_color_global)
    else:
        timer_running = False

def warning_blue():
    """
    When the admin clicks the Blue warning button:
      - Verify that the fight is active (started, not over, and in a round).
      - If the timer is still running, show an error and exit.
      - Otherwise, ask for confirmation.
      - If confirmed, apply the warning: add 3 points (per judge) in favor of Red.
      - If the Blue fighter receives 4 warnings, disqualify Blue.
    """
    global blue_warning_count, judge_scores, timer_running, winner_text_global, winner_color_global

    # Check if warnings can be given (only active round, fight started, not over)
    if not fight_started or fight_over or mode_timer != "round":
        messagebox.showerror("Warning", "Warnings can only be given during an active round.")
        return

    # If the timer is still running, stop the admin from giving a warning.
    if timer_running:
        messagebox.showerror("Warning", "Please stop time before giving warning.")
        return

    # Confirm if the admin wants to apply the warning.
    if not messagebox.askyesno("Confirm Warning", "Are you sure you want to give a Blue warning?"):
        return

    # Apply the warning.
    blue_warning_count += 1
    for judge in judge_scores:
        judge_scores[judge]["red"] += 3
    update_judge_details()
    # Update the warning counter label for Blue
    warning_blue_label.config(text=str(blue_warning_count))
    
    # Check if Blue has reached 4 warnings and disqualify if so.
    if blue_warning_count >= 4:
        timer_running = False
        winner_text_global = "WINNER RED (DISQUALIFIED)"
        winner_color_global = "red"
        timer_label.config(text=winner_text_global, fg=winner_color_global, font=("Arial", 36, "bold"))
        messagebox.showinfo("Disqualification", "The Blue fighter received 4 warnings and is disqualified.")
        lock_interface_final()

def warning_red():
    """
    When the admin clicks the Red warning button:
      - Verify that the fight is active (started, not over, and in a round).
      - If the timer is still running, show an error and exit.
      - Otherwise, ask for confirmation.
      - If confirmed, apply the warning: add 3 points (per judge) in favor of Blue.
      - If the Red fighter receives 4 warnings, disqualify Red.
    """
    global red_warning_count, judge_scores, timer_running, winner_text_global, winner_color_global

    # Check if warnings can be given (only active round, fight started, not over)
    if not fight_started or fight_over or mode_timer != "round":
        messagebox.showerror("Warning", "Warnings can only be given during an active round.")
        return

    # Ensure the chronometer is stopped.
    if timer_running:
        messagebox.showerror("Warning", "Please stop time before giving warning.")
        return

    # Confirm if the admin wants to give the warning.
    if not messagebox.askyesno("Confirm Warning", "Are you sure you want to give a Red warning?"):
        return

    # Apply the warning.
    red_warning_count += 1
    for judge in judge_scores:
        judge_scores[judge]["blue"] += 3
    update_judge_details()
    # Update the warning counter label for Red
    warning_red_label.config(text=str(red_warning_count))



    # Check if Red has reached 4 warnings and disqualify if so.
    if red_warning_count >= 4:
        timer_running = False
        winner_text_global = "WINNER BLUE (DISQUALIFIED)"
        winner_color_global = "blue"
        timer_label.config(text=winner_text_global, fg=winner_color_global, font=("Arial", 36, "bold"))
        messagebox.showinfo("Disqualification", "The Red fighter received 4 warnings and is disqualified.")
        lock_interface_final()

def ko_red():
    """
    Trigger a Knockout (KO) for Red, awarding victory to Blue.
    """
    global timer_running, fight_over, blinking, winner_text_global, winner_color_global
    if not fight_started:
        messagebox.showwarning("Warning", "Fight has not started yet.")
        return
    answer = messagebox.askyesno("Confirmation", "Confirm KO for Red? (This will award victory to Blue)")
    if not answer:
        return
    timer_running = False
    winner_text_global = "WINNER BLUE (KO)"
    winner_color_global = "blue"
    timer_label.config(text=winner_text_global, fg=winner_color_global, font=("Arial", 36, "bold"))
    fight_over = True
    blinking = True
    start_blinking()
    lock_interface_final()

def ko_blue():
    """
    Trigger a Knockout (KO) for Blue, awarding victory to Red.
    """
    global timer_running, fight_over, blinking, winner_text_global, winner_color_global
    if not fight_started:
        messagebox.showwarning("Warning", "Fight has not started yet.")
        return
    answer = messagebox.askyesno("Confirmation", "Confirm KO for Blue? (This will award victory to Red)")
    if not answer:
        return
    timer_running = False
    winner_text_global = "WINNER RED (KO)"
    winner_color_global = "red"
    timer_label.config(text=winner_text_global, fg=winner_color_global, font=("Arial", 36, "bold"))
    fight_over = True
    blinking = True
    start_blinking()
    lock_interface_final()

def start_blinking():
    """
    Begin the blinking routine for the winner display.
    """
    blink_winner()

def blink_winner():
    """
    Toggle the timer label's color to create a blinking effect.
    """
    global blinking, winner_color_global
    if blinking:
        current_fg = timer_label.cget("fg")
        timer_label.config(fg="white" if current_fg == winner_color_global else winner_color_global)
        root.after(500, blink_winner)

def enable_fight_controls():
    """
    Enable the Stop and KO buttons during the fight.
    """
    btn_stop.config(state="normal")
    btn_ko_red.config(state="normal")
    btn_ko_blue.config(state="normal")

def determine_winner():
    """
    Placeholder function to determine the winner when the fight ends.
    (The logic here can be implemented as needed.)
    """
    pass

def lock_interface_final():
    """
    Lock the interface after the fight is over.
    (Any final locking actions can be implemented here.)
    """
    pass

def enable_start_if_valid():
    """
    Enable the 'Fight' button if both fighter data and fight settings are validated.
    """
    if fighters_validated and settings_validated:
        btn_fight.config(state="normal")

def lock_interface_final():
    # Disable all fight control buttons, so no further input is possible.
    btn_fight.config(state="disabled")
    btn_stop.config(state="disabled")
    btn_warning_blue.config(state="disabled")
    btn_warning_red.config(state="disabled")
    btn_ko_red.config(state="disabled")
    btn_ko_blue.config(state="disabled")

# ====================================================
# TIMER CONTROL BUTTONS
# ====================================================
timer_buttons_frame = tk.Frame(frame_timer)
timer_buttons_frame.pack(pady=5)
btn_fight = tk.Button(timer_buttons_frame, text="Fight", command=start_fight, font=("Arial", 12),
                      bg="green", fg="white", state="disabled")
btn_fight.pack(side="left", padx=5)
btn_stop = tk.Button(timer_buttons_frame, text="Stop", command=stop_fight, font=("Arial", 12),
                     bg="black", fg="white")
btn_stop.pack(side="left", padx=5)

btn_warning_red = tk.Button(timer_buttons_frame, text="WARNING RED", command=warning_red, font=("Arial", 12), bg="red", fg="white")
btn_warning_red.pack(side="left", padx=5)

btn_warning_blue = tk.Button(timer_buttons_frame, text="WARNING BLUE", command=warning_blue, font=("Arial", 12), bg="blue", fg="white")
btn_warning_blue.pack(side="left", padx=5)

btn_ko_red = tk.Button(timer_buttons_frame, text="K.O RED", command=ko_red, font=("Arial", 12),
                       bg="red", fg="white")
btn_ko_red.pack(side="left", padx=5)

btn_ko_blue = tk.Button(timer_buttons_frame, text="K.O BLUE", command=ko_blue, font=("Arial", 12),
                        bg="blue", fg="white")
btn_ko_blue.pack(side="left", padx=5)

# ====================================================
# JUDGE INTERFACE DISPLAY (Favorability Counter & Detailed Scores)
# ====================================================
# Judge Favorability Counter Section
frame_judge_counts = tk.Frame(root)
frame_judge_counts.pack(pady=10)
label_red_judges = tk.Label(frame_judge_counts, text="0", fg="red", font=("Arial", 24, "bold"))
label_red_judges.pack(side="left", padx=20)
label_blue_judges = tk.Label(frame_judge_counts, text="0", fg="blue", font=("Arial", 24, "bold"))
label_blue_judges.pack(side="left", padx=20)

# Detailed Judge Scores Section
frame_judge_details = tk.Frame(root)
frame_judge_details.pack(pady=10)
tk.Label(frame_judge_details, text="Judge 1 Red:", font=("Arial", 10), fg="red").grid(row=0, column=0, padx=5)
judge1_red_label = tk.Label(frame_judge_details, text="0", font=("Arial", 12), fg="red")
judge1_red_label.grid(row=0, column=1, padx=5)
tk.Label(frame_judge_details, text="Judge 1 Blue:", font=("Arial", 10), fg="blue").grid(row=0, column=2, padx=5)
judge1_blue_label = tk.Label(frame_judge_details, text="0", font=("Arial", 12), fg="blue")
judge1_blue_label.grid(row=0, column=3, padx=5)

tk.Label(frame_judge_details, text="Judge 2 Red:", font=("Arial", 10), fg="red").grid(row=1, column=0, padx=5)
judge2_red_label = tk.Label(frame_judge_details, text="0", font=("Arial", 12), fg="red")
judge2_red_label.grid(row=1, column=1, padx=5)
tk.Label(frame_judge_details, text="Judge 2 Blue:", font=("Arial", 10), fg="blue").grid(row=1, column=2, padx=5)
judge2_blue_label = tk.Label(frame_judge_details, text="0", font=("Arial", 12), fg="blue")
judge2_blue_label.grid(row=1, column=3, padx=5)

tk.Label(frame_judge_details, text="Judge 3 Red:", font=("Arial", 10), fg="red").grid(row=2, column=0, padx=5)
judge3_red_label = tk.Label(frame_judge_details, text="0", font=("Arial", 12), fg="red")
judge3_red_label.grid(row=2, column=1, padx=5)
tk.Label(frame_judge_details, text="Judge 3 Blue:", font=("Arial", 10), fg="blue").grid(row=2, column=2, padx=5)
judge3_blue_label = tk.Label(frame_judge_details, text="0", font=("Arial", 12), fg="blue")
judge3_blue_label.grid(row=2, column=3, padx=5)

# Warning counter labels for each corner (placed in row 3, just under Judge 3 scoring)
tk.Label(frame_judge_details, text="Warnings Red:", font=("Arial", 10), fg="red").grid(row=3, column=0, padx=5)
warning_red_label = tk.Label(frame_judge_details, text="0", font=("Arial", 12), fg="red")
warning_red_label.grid(row=3, column=1, padx=5)

tk.Label(frame_judge_details, text="Warnings Blue:", font=("Arial", 10), fg="blue").grid(row=3, column=2, padx=5)
warning_blue_label = tk.Label(frame_judge_details, text="0", font=("Arial", 12), fg="blue")
warning_blue_label.grid(row=3, column=3, padx=5)

# ====================================================
# FLASK ROUTES: WEB-BASED JUDGE INTERFACE
# ====================================================
@app.route("/judge_login", methods=["GET", "POST"])
def judge_login():
    """
    Display a common judge login page.
    Lock login once the fight starts.
    """
    if fight_started:
        return "Judge login is locked because the fight has started.", 403
    if request.method == "GET":
        return '''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title>Judge Login</title>
        </head>
        <body>
          <h1>Judge Login</h1>
          <form method="post">
            <label>Select your judge role:</label>
            <select name="judge_num">
              <option value="1">Judge 1</option>
              <option value="2">Judge 2</option>
              <option value="3">Judge 3</option>
            </select>
            <input type="submit" value="Login">
          </form>
        </body>
        </html>
        '''
    else:
        judge_num = request.form.get("judge_num")
        if judge_num not in ['1', '2', '3']:
            return "Invalid judge selection", 400
        token = judge_tokens.get(int(judge_num))
        if not token:
            return "Judge token not available. Has a new fight been started?", 400
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta http-equiv="refresh" content="0; url=/final_judge/{token}" />
          <title>Redirecting...</title>
        </head>
        <body>
          Redirecting to your final judge interface...
        </body>
        </html>
        '''

@app.route("/final_judge/<token>")
def final_judge(token):
    """
    Display the final judge interface after validating the judge token.
    """
    judge_num = None
    for num, tok in judge_tokens.items():
        if tok == token:
            judge_num = num
            break
    if judge_num is None:
        return "Unauthorized: Invalid token", 403
    if discipline.get() in tatami_age_dict:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title>Judge Interface - Judge {judge_num}</title>
          <style>
            body {{
              font-family: Arial, sans-serif;
              text-align: center;
              background-color: #f7f7f7;
            }}
            h1 {{
              margin-top: 20px;
              font-size: 16px;
            }}
            .button {{
              display: block;
              padding: 10px;
              font-size: 16px;
              margin: 10px auto;
              border: none;
              border-radius: 5px;
              color: #fff;
              cursor: pointer;
              width: 90%;
            }}
            .red {{
              background-color: #e74c3c;
            }}
            .blue {{
              background-color: #3498db;
            }}
            table {{
              width: 100%;
              border-collapse: collapse;
            }}
            td {{
              vertical-align: top;
              width: 50%;
            }}
          </style>
        </head>
        <body>
          <h1>Judge Interface - Judge {judge_num}</h1>
          <table>
            <tr>
              <td>
                <button class="button red" onclick="sendScore('red', 'HI-JUMP KICK RED')">3 - Head Jump Kick</button>
              </td>
              <td>
                <button class="button blue" onclick="sendScore('blue', 'HI-JUMP KICK BLUE')">3 - Head Jump Kick</button>
              </td>
            </tr>
            <tr>
              <td>
                <button class="button red" onclick="sendScore('red', 'JUMP KICK RED')">2 - Jump/Head Kick</button>
              </td>
              <td>
                <button class="button blue" onclick="sendScore('blue', 'JUMP KICK BLUE')">2 - Jump/Head Kick</button>
              </td>
            </tr>
            <tr>
              <td>
                <button class="button red" onclick="sendScore('red', 'POINT RED')">1 - Point Red</button>
              </td>
              <td>
                <button class="button blue" onclick="sendScore('blue', 'POINT BLUE')">1 - Point Blue</button>
              </td>
            </tr>
          </table>
          <script>
            function sendScore(color, scoring_action) {{
              var xhr = new XMLHttpRequest();
              xhr.open("GET", "/judge_score/{token}/" + color + "/" + scoring_action, true);
              xhr.send();
            }}
          </script>
        </body>
        </html>
        """
    else:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title>Judge Interface - Judge {judge_num}</title>
          <style>
            body {{
              font-family: Arial, sans-serif;
              text-align: center;
              background-color: #f7f7f7;
            }}
            h1 {{
              margin-top: 20px;
              font-size: 16px;
            }}
            .button {{
              display: block;
              padding: 15px 0;
              font-size: 20px;
              margin: 15px auto;
              border: none;
              border-radius: 10px;
              color: #fff;
              cursor: pointer;
              width: 90%;
            }}
            .red {{
              background-color: #e74c3c;
            }}
            .blue {{
              background-color: #3498db;
            }}
            table {{
              width: 100%;
              border-collapse: collapse;
            }}
            td {{
              vertical-align: middle;
              width: 50%;
            }}
          </style>
        </head>
        <body>
          <h1>Judge Interface - Judge {judge_num}</h1>
          <table>
            <tr>
              <td>
                <button class="button red" onclick="sendScore('red', 'POINT RED')">1 - Point Red</button>
              </td>
              <td>
                <button class="button blue" onclick="sendScore('blue', 'POINT BLUE')">1 - Point Blue</button>
              </td>
            </tr>
          </table>
          <script>
            function sendScore(color, scoring_action) {{
              var xhr = new XMLHttpRequest();
              xhr.open("GET", "/judge_score/{token}/" + color + "/" + scoring_action, true);
              xhr.send();
            }}
          </script>
        </body>
        </html>
        """
    return html

@app.route("/judge_score/<token>/<color>/<scoring_action>", methods=["GET"])
def judge_score(token, color, scoring_action):
    global fight_started, timer_running, mode_timer, fight_over

    # Only allow scoring if the fight has started, is actively running,
    # and is in the round phase.
    if not fight_started or not timer_running or mode_timer != "round":
        return "Scoring not allowed at this time.", 403

    # Verify the judge token.
    judge_num = None
    for num, tok in judge_tokens.items():
        if tok == token:
            judge_num = num
            break
    if judge_num is None:
        return "Unauthorized access: invalid token", 403

    if color not in ["red", "blue"]:
        return "Invalid input", 400

    global judge_scores, discipline
    if discipline.get() in tatami_age_dict:
        points = tatami_points.get(scoring_action, None)
    else:
        points = ring_points.get(scoring_action, None)

    if points:
        judge_scores[judge_num][color] += points[color]
        root.after(0, update_judge_details)
        return "OK", 200
    else:
        return "Invalid scoring action", 400

def update_judge_details():
    """
    Update the detailed judge scores displayed on the admin interface,
    update the main favorable judges counter based on which judge favors which fighter,
    and in kick light/light contact check for a 15-point advantage on at least two judges.
    """
    # Update the detailed individual scores for each judge.
    judge1_red_label.config(text=str(judge_scores[1]["red"]))
    judge1_blue_label.config(text=str(judge_scores[1]["blue"]))
    judge2_red_label.config(text=str(judge_scores[2]["red"]))
    judge2_blue_label.config(text=str(judge_scores[2]["blue"]))
    judge3_red_label.config(text=str(judge_scores[3]["red"]))
    judge3_blue_label.config(text=str(judge_scores[3]["blue"]))

    # Calculate favorable judges for each side.
    favorable_red = 0
    favorable_blue = 0
    for judge in judge_scores:
        red_points = judge_scores[judge]["red"]
        blue_points = judge_scores[judge]["blue"]
        if red_points > blue_points:
            favorable_red += 1
        elif blue_points > red_points:
            favorable_blue += 1

    # Update the main favorable counter labels.
    label_red_judges.config(text=str(favorable_red))
    label_blue_judges.config(text=str(favorable_blue))

    # Check for the early stoppage condition (kick light and light contact only)
    check_early_stop_by_points()

def check_early_stop_by_points():
    """
    In kick light and light contact only:
    If one opponent achieves an advantage of at least 15 points (for that judge)
    in at least two of the judges, then stop the fight.
    The fighter ahead by points will be declared as winner,
    using the same display style and blinking effect as used for KO or disqualification.
    """
    # Ensure the rule applies only to Kick Light and Light Contact disciplines.
    # (Assuming discipline is a StringVar; adjust as needed.)
    if discipline.get().lower() not in ["kick light", "light contact"]:
        return

    red_advantage_count = 0
    blue_advantage_count = 0

    for judge in judge_scores:
        diff = judge_scores[judge]["red"] - judge_scores[judge]["blue"]
        if diff >= 15:
            red_advantage_count += 1
        elif diff <= -15:
            blue_advantage_count += 1

    # If at least two judges have a 15+ advantage for one fighter, stop the fight.
    if red_advantage_count >= 2:
        end_fight_by_points("red")
    elif blue_advantage_count >= 2:
        end_fight_by_points("blue")

def end_fight_by_points(winning_side):
    """
    Stop the fight and display the winning fighter based on points advantage.
    The display will use the same style (font, size, blinking text) as in a KO/disqualification scenario.
    """
    global timer_running, fight_over, winner_text_global, winner_color_global

    timer_running = False
    fight_over = True

    if winning_side == "red":
        winner_text_global = "WINNER RED"
        winner_color_global = "red"
    else:
        winner_text_global = "WINNER BLUE"
        winner_color_global = "blue"

    timer_label.config(text=winner_text_global, fg=winner_color_global, font=("Arial", 36, "bold"))
    blink_winner_text()
    lock_interface_final()


def blink_winner_text():
    """
    Toggle the text color of the timer_label to create a blinking effect.
    """
    current_fg = timer_label.cget("fg")
    if current_fg == winner_color_global:
        timer_label.config(fg="white")
    else:
        timer_label.config(fg=winner_color_global)
    timer_label.after(500, blink_winner_text)

@app.route('/public')
def public_display():
    # Retrieve fighter names.
    red_fighter_name = red_name.get() if hasattr(red_name, 'get') else red_name
    blue_fighter_name = blue_name.get() if hasattr(blue_name, 'get') else blue_name

    # Retrieve club/country details.
    red_club = red_country.get() if hasattr(red_country, 'get') else red_country
    blue_club = blue_country.get() if hasattr(blue_country, 'get') else blue_country

    # Retrieve discipline.
    discipline_val = discipline.get() if hasattr(discipline, 'get') else discipline

    # Retrieve age category using the variable 'age_categories'
    age_categories_val = age_categories.get() if hasattr(age_categories, 'get') else age_categories

    # Retrieve weight category using the variable 'weight_categories'
    weight_categories_val = weight_categories.get() if hasattr(weight_categories, 'get') else weight_categories

    # Retrieve round and timer information from their labels.
    round_info = round_label.cget("text")
    timer_info = timer_label.cget("text")

    # Build the context dictionary for your template.
    return render_template("public_display.html",
                           red_name=red_fighter_name,
                           blue_name=blue_fighter_name,
                           red_club=red_club,
                           blue_club=blue_club,
                           red_favorable=label_red_judges.cget("text"),
                           blue_favorable=label_blue_judges.cget("text"),
                           judge_scores=judge_scores,
                           red_warnings=red_warning_count,
                           blue_warnings=blue_warning_count,
                           discipline=discipline_val,
                           age_category=age_categories_val,  # using the plural variable
                           weight_category=weight_categories_val,  # using the plural variable
                           round_info=round_info,
                           timer_info=timer_info)

# ====================================================
# RUN FLASK IN A SEPARATE THREAD & START TKINTER MAIN LOOP
# ====================================================
def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# Automatically start a new fight when the program launches (no confirmation)
root.after(0, lambda: new_fight(confirm=False))
root.mainloop()
