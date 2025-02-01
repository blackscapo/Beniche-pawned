import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading
import json
from collections import Counter
import re
import os

# Define color schemes for dark and light modes
dark_mode = {
    "bg": "#121212",
    "fg": "#58D68D",
    "entry_bg": "#2C3E50",
    "button_bg": "#58D68D",
    "button_fg": "white",
    "listbox_bg": "#2C3E50",
    "listbox_fg": "#58D68D",
    "progress_bar": "default",
    "hover_bg": "#45B39D",
    "alert_fg": "#E74C3C"
}

light_mode = {
    "bg": "#FFFFFF",
    "fg": "#000000",
    "entry_bg": "#F0F0F0",
    "button_bg": "#4CAF50",
    "button_fg": "white",
    "listbox_bg": "#F0F0F0",
    "listbox_fg": "#000000",
    "progress_bar": "black",
    "hover_bg": "#45a049",
    "alert_fg": "#D32F2F"
}

# Configuration file for theme preference
CONFIG_FILE = "config.json"

# Function to toggle between dark and light modes
def toggle_theme():
    global current_theme
    if current_theme == dark_mode:
        current_theme = light_mode
    else:
        current_theme = dark_mode
    apply_theme()
    save_theme_preference(current_theme)

# Function to save theme preference to a file
def save_theme_preference(theme):
    with open(CONFIG_FILE, "w") as file:
        json.dump({"theme": "dark" if theme == dark_mode else "light"}, file)

# Function to load theme preference from a file
def load_theme_preference():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            return dark_mode if config.get("theme") == "dark" else light_mode
    return dark_mode

# Function to apply the selected theme
def apply_theme():
    root.config(bg=current_theme["bg"])
    search_frame.config(bg=current_theme["bg"])
    results_frame.config(bg=current_theme["bg"])
    stats_frame.config(bg=current_theme["bg"])
    alerts_frame.config(bg=current_theme["bg"])
    button_frame.config(bg=current_theme["bg"])
    
    search_label.config(bg=current_theme["bg"], fg=current_theme["fg"])
    search_entry.config(bg=current_theme["entry_bg"], fg=current_theme["fg"], insertbackground=current_theme["fg"])
    search_button.config(bg=current_theme["button_bg"], fg=current_theme["button_fg"])
    result_count_label.config(bg=current_theme["bg"], fg=current_theme["fg"])
    result_listbox.config(bg=current_theme["listbox_bg"], fg=current_theme["listbox_fg"])
    copy_button.config(bg=current_theme["button_bg"], fg=current_theme["button_fg"])
    save_button.config(bg=current_theme["button_bg"], fg=current_theme["button_fg"])
    theme_button.config(bg=current_theme["button_bg"], fg=current_theme["button_fg"])
    clear_button.config(bg=current_theme["button_bg"], fg=current_theme["button_fg"])
    progress_bar.config(style=f"{current_theme['progress_bar']}.Horizontal.TProgressbar")
    stats_label.config(bg=current_theme["bg"], fg=current_theme["fg"])
    security_alert_label.config(bg=current_theme["bg"], fg=current_theme["alert_fg"])
    password_strength_label.config(bg=current_theme["bg"], fg=current_theme["fg"])

# Function to fetch data based on search query
def fetch_data(query):
    url = f"https://api.proxynova.com/comb?query={query}&start=0&limit=15"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)
        
        # Parse the JSON response
        data = response.json()
        
        # Extract the list of email:password combinations
        combo_list = data.get("lines", [])
        return combo_list
    except requests.exceptions.RequestException as e:
        security_alert_label.config(text=f"Error: {e}", fg=current_theme["alert_fg"])
        return []
    except json.JSONDecodeError:
        security_alert_label.config(text="Error: Invalid JSON response from the server.", fg=current_theme["alert_fg"])
        return []

# Function to update the list box with search results
def on_search():
    query = search_entry.get()  # Get the query from the search box
    if not query:
        security_alert_label.config(text="Please enter a search term.", fg=current_theme["alert_fg"])
        return
    
    # Start the progress bar
    progress_bar.start()
    search_button.config(state=tk.DISABLED)  # Disable the search button during the search

    # Run the search function in a separate thread so it doesn't block the UI
    threading.Thread(target=search_thread, args=(query,), daemon=True).start()

# Function to simulate the search and update the progress bar
def search_thread(query):
    results = fetch_data(query)
    
    # Use the `after` method to update the GUI in a thread-safe manner
    root.after(0, update_gui, results, query)

def update_gui(results, query):
    # Clear the list box before adding new results
    result_listbox.delete(0, tk.END)

    # Update the result count label
    result_count_label.config(text=f"Results Found: {len(results)}")
    
    if results:
        for result in results:
            result_listbox.insert(tk.END, result)
        
        # Check if the query appears in the results
        if any(query.lower() in result.lower() for result in results):
            result_listbox.config(fg="red")  # Highlight results in red
            security_alert_label.config(
                text="You have been pawned! Change your password immediately.\n\n"
                     "Tips to secure your account:\n"
                     "1. Use a strong, unique password.\n"
                     "2. Enable two-factor authentication.\n"
                     "3. Regularly monitor your accounts for suspicious activity.",
                fg=current_theme["alert_fg"]
            )
            # Check password strength
            check_password_strength(results, query)
        else:
            result_listbox.config(fg=current_theme["listbox_fg"])  # Reset to default color
            security_alert_label.config(text="No security issues found.", fg=current_theme["fg"])
        
        # Update statistics
        update_statistics(results)
    else:
        security_alert_label.config(text="No results found.", fg=current_theme["fg"])
    
    # Stop the progress bar and re-enable the search button
    progress_bar.stop()
    search_button.config(state=tk.NORMAL)

# Function to update statistics
def update_statistics(results):
    # Extract domains and passwords
    domains = [result.split(":")[0].split("@")[-1] for result in results if ":" in result]
    passwords = [result.split(":")[1] for result in results if ":" in result]
    
    # Calculate statistics
    total_results = len(results)
    unique_domains = len(set(domains))
    common_passwords = Counter(passwords).most_common(3)  # Top 3 most common passwords
    
    # Update statistics label
    stats_text = f"Statistics:\nTotal Results: {total_results}\nUnique Domains: {unique_domains}\n"
    stats_text += "Most Common Passwords:\n"
    for password, count in common_passwords:
        stats_text += f"- {password} (used {count} times)\n"
    stats_label.config(text=stats_text)

# Function to check password strength
def check_password_strength(results, query):
    for result in results:
        if query.lower() in result.lower():
            email, password = result.split(":") if ":" in result else (None, None)
            if password:
                strength = evaluate_password_strength(password)
                password_strength_label.config(text=f"Password for {email} is {strength}.", fg=current_theme["fg"])

# Enhanced password strength evaluation
def evaluate_password_strength(password):
    if len(password) < 8:
        return "very weak (too short)"
    
    strength = 0
    if re.search(r"[A-Z]", password):
        strength += 1
    if re.search(r"[a-z]", password):
        strength += 1
    if re.search(r"[0-9]", password):
        strength += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        strength += 1
    
    if strength == 4:
        return "very strong"
    elif strength == 3:
        return "strong"
    elif strength == 2:
        return "moderate"
    else:
        return "weak"

# Function to copy selected result to clipboard
def copy_to_clipboard():
    selected = result_listbox.get(tk.ACTIVE)
    if selected:
        root.clipboard_clear()
        root.clipboard_append(selected)
        security_alert_label.config(text="Selected result copied to clipboard.", fg=current_theme["fg"])

# Function to save results to a file
def save_results():
    results = result_listbox.get(0, tk.END)
    if not results:
        security_alert_label.config(text="No results to save.", fg=current_theme["alert_fg"])
        return
    
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            for result in results:
                file.write(result + "\n")
        security_alert_label.config(text="Results saved successfully.", fg=current_theme["fg"])

# Function to clear results
def clear_results():
    result_listbox.delete(0, tk.END)
    result_count_label.config(text="Results Found: 0")
    security_alert_label.config(text="")
    password_strength_label.config(text="")
    stats_label.config(text="Statistics:\nTotal Results: 0\nUnique Domains: 0\nMost Common Passwords: None")

# Set up the main window (root window)
root = tk.Tk()
root.title("Beniche-pawned")
root.geometry("600x900")  # Set the window size to 600x900
root.minsize(600, 900)  # Set a minimum size

# Initialize theme
current_theme = load_theme_preference()

# Create frames for better organization
search_frame = tk.Frame(root, bg=current_theme["bg"])
search_frame.pack(pady=10, padx=20, fill="x")

results_frame = tk.Frame(root, bg=current_theme["bg"])
results_frame.pack(pady=10, padx=20, fill="both", expand=True)

stats_frame = tk.Frame(root, bg=current_theme["bg"])
stats_frame.pack(pady=10, padx=20, fill="x")

alerts_frame = tk.Frame(root, bg=current_theme["bg"])
alerts_frame.pack(pady=10, padx=20, fill="x")

button_frame = tk.Frame(root, bg=current_theme["bg"])
button_frame.pack(pady=10, padx=20, fill="x")

# Create a label for the search box
search_label = tk.Label(search_frame, text="Enter search query:", font=("Segoe UI", 14, "bold"))
search_label.pack(anchor="w")

# Create an entry widget for the search box
search_entry = tk.Entry(search_frame, width=50, font=("Segoe UI", 12), borderwidth=2, relief="solid")
search_entry.pack(pady=10, fill="x")

# Create a search button
search_button = tk.Button(search_frame, text="Search", command=on_search, font=("Segoe UI", 12, "bold"), relief="raised", bd=4, width=20)
search_button.pack(pady=10)

# Create a progress bar to show the search status
progress_bar = ttk.Progressbar(search_frame, orient="horizontal", length=500, mode="indeterminate")
progress_bar.pack(pady=10, fill="x")

# Create a label for showing the number of results found
result_count_label = tk.Label(results_frame, text="Results Found: 0", font=("Segoe UI", 12, "bold"))
result_count_label.pack(anchor="w")

# Create a listbox to display the results
result_listbox = tk.Listbox(results_frame, width=70, height=15, font=("Courier New", 10), selectmode=tk.SINGLE, bd=3, relief="solid")
result_listbox.pack(side=tk.LEFT, fill="both", expand=True)

# Add a scrollbar to the listbox
scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=result_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill="y")
result_listbox.config(yscrollcommand=scrollbar.set)

# Add buttons to the button frame
copy_button = tk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard, font=("Segoe UI", 10, "bold"), relief="raised", bd=2, width=20)
copy_button.pack(side=tk.LEFT, padx=5, pady=5)

save_button = tk.Button(button_frame, text="Save Results", command=save_results, font=("Segoe UI", 10, "bold"), relief="raised", bd=2, width=20)
save_button.pack(side=tk.LEFT, padx=5, pady=5)

theme_button = tk.Button(button_frame, text="Toggle Theme", command=toggle_theme, font=("Segoe UI", 10, "bold"), relief="raised", bd=2, width=20)
theme_button.pack(side=tk.LEFT, padx=5, pady=5)

clear_button = tk.Button(button_frame, text="Clear Results", command=clear_results, font=("Segoe UI", 10, "bold"), relief="raised", bd=2, width=20)
clear_button.pack(side=tk.LEFT, padx=5, pady=5)

# Add a label for statistics
stats_label = tk.Label(stats_frame, text="Statistics:\nTotal Results: 0\nUnique Domains: 0\nMost Common Passwords: None", font=("Segoe UI", 10), justify="left")
stats_label.pack(anchor="w")

# Add a label for security alerts
security_alert_label = tk.Label(alerts_frame, text="", font=("Segoe UI", 10), justify="left", wraplength=550)
security_alert_label.pack(anchor="w")

# Add a label for password strength feedback
password_strength_label = tk.Label(alerts_frame, text="", font=("Segoe UI", 10), justify="left", wraplength=550)
password_strength_label.pack(anchor="w")

# Apply the theme after all widgets are created
apply_theme()

# Run the main event loop
root.mainloop()
