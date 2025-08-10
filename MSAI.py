# Code Written By SayyadN
# Date: 8/7/2025
# Python Version of Gemini CLI

# ===== Imports =====
import subprocess 
import argparse
import platform
import google.generativeai as genai
import time
import pyautogui
import json
from pathlib import Path
import os
import requests

# ===== Setup Gemini API =====
genai.configure(api_key="AIzaSyD0QaJRhq6z1S01MI2HhQMl5Kx1svC0-jg")
model = genai.GenerativeModel("gemini-2.5-flash")

# ===== Usage History File =====
HISTORY_FILE = Path.home() / ".msai_usage.json"

# ===== Load User History =====
def load_user_usage():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print("[ERROR] Failed to load usage history:", e)
    return {}

# ===== Save User History =====
def save_user_usage(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ===== Log New Command =====
def log_user_usage(prompt):
    data = load_user_usage()
    data[prompt] = data.get(prompt, 0) + 1
    save_user_usage(data)

# ===== Suggest Frequent Commands =====
def suggest_frequent_commands():
    data = load_user_usage()
    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
    if sorted_items:
        print("\nMost Frequently Used Commands:")
        for prompt, count in sorted_items[:5]:
            print(f" - {prompt} (x{count})")

# ===== Classify Prompt Type =====
def classify_task(prompt):
    gui_keywords = [
        "mouse", "press", "click", "write", "screen", "move", "open", 'close' 
        "ماوس", "اضغط", "انقر", "اكتب", "سكرين", "تحريك", "افتح" , 'اغلق'
    ]
    web_action_words = [
        "http", "https", "request", "api", "download"
    ]
    for word in gui_keywords:
        if word in prompt:
            return "gui"
    for word in web_action_words:
        if word in prompt:
            return "web"
    return "bash"

# ===== Extract Python Code Block =====
def extract_code(text):
    lines = text.strip().splitlines()
    code_lines = []
    capture = False
    for line in lines:
        if line.strip().startswith("```python"):
            capture = True
            continue
        elif line.strip().startswith("```"):
            break
        if capture:
            code_lines.append(line)
    return "\n".join(code_lines)

# ===== Execute Web Action =====
def web_command(prompt):
    try:
        response = model.generate_content(
            f"Write a Python script using requests or wget to perform this web task:\n{prompt}"
        )
        code = extract_code(response.text)
        print("\n[Generated Web Action Code:]\n")
        print(code)
        context = {
            'requests': requests,
            'os': os,
            'subprocess': subprocess
        }
        exec(code, context)
        functions_defined = [name for name in context if callable(context[name]) and not name.startswith('__')]
        if len(functions_defined) == 1:
            print(f"\n[Auto Executing Web Function]: {functions_defined[0]}()")
            context[functions_defined[0]]()
        else:
            print("[!] No callable function found to execute.")
    except Exception as e:
        print("[❌] Error while executing Web action:", e)

# ===== Execute Bash Command =====
def bash_command_exec(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, check=True, text=True)
        print("[OUTPUT]\n", result.stdout)
    except Exception as e:
        print("[ERROR]\n", e)

# ===== GUI Command Execution =====
def gui_action(prompt):
    try:
        response = model.generate_content(
            f"Write Python code using pyautogui to directly perform the following GUI task without explanations:\n{prompt}"
        )
        code = extract_code(response.text)
        print("\n[Generated GUI Code:]\n")
        print(code)
        if not code.strip():
            print("[!] No GUI code generated. Trying Bash fallback instead...")
            fallback = prompt_to_bash(prompt)
            if fallback:
                print("[Fallback Bash Command]:", fallback)
                if input("Execute it? (y/n): ").lower() == "y":
                    bash_command_exec(fallback)
            else:
                print("[⚠️] Neither GUI nor Bash code could be generated.")
            return
        context = {
            'pyautogui': pyautogui,
            'time': time
        }
        exec(code, context)
        functions_defined = [name for name in context if callable(context[name]) and not name.startswith('__')]
        if len(functions_defined) == 1:
            print(f"\n[Auto Executing GUI Function]: {functions_defined[0]}()")
            context[functions_defined[0]]()
        else:
            print("[!] No callable function found to execute.")
    except Exception as e:
        print("[❌] Error while executing GUI action:", e)

# ===== Convert Natural Prompt to Bash =====
def prompt_to_bash(prompt):
    system_prompt = f"Convert this to a bash command only:\n{prompt}"
    try:
        response = model.generate_content(system_prompt)
        lines = response.text.strip().splitlines()
        for line in lines:
            if line.startswith("```bash") or line.startswith("```"):
                continue
            return line.strip()
    except Exception as e:
        print("[ERROR in Gemini bash conversion]", e)
        return None

# ===== Main Program =====
def main():
    parser = argparse.ArgumentParser(description="MSAI - Smart CLI by SayyadN")
    parser.add_argument("instruction", type=str, help="Write your command in natural language")
    parser.add_argument("-a", "--auto", action="store_true", help="Execute without confirmation")
    args = parser.parse_args()

    suggest_frequent_commands()
    log_user_usage(args.instruction)

    task_type = classify_task(args.instruction)
    print(f"\n[Command]: {args.instruction}")
    print(f"[Task Type]: {task_type}\n")

    if task_type == "bash":
        bash_command = prompt_to_bash(args.instruction)
        if not bash_command:
            print("Failed to generate bash command.")
            return
        print("[Generated Bash]:")
        print("\033[92m" + bash_command + "\033[0m\n")
        if args.auto or input("Execute this command? (y/n): ").lower() == "y":
            bash_command_exec(bash_command)
        else:
            print("[Cancelled]")

    elif task_type == "gui":
        if args.auto or input("Execute GUI action? (y/n): ").lower() == "y":
            gui_action(args.instruction)
        else:
            print("[Cancelled]")

    elif task_type == "web":
        if args.auto or input("Execute web/network action? (y/n): ").lower() == "y":
            web_command(args.instruction)
        else:
            print("[Cancelled]")

if __name__ == "__main__":
    if platform.system() != "Linux":
        print("[Unsupported OS] This script supports Linux  only.")
    else:
        main()
