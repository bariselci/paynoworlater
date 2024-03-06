import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
from tkinter import filedialog
from PIL import Image, ImageTk

def place_logo(logo_path, target_size, root):
    logo = Image.open(logo_path)
    original_width, original_height = logo.size
    scale_factor = min(target_size[0] / original_width, target_size[1] / original_height)
    new_size = (int(original_width * scale_factor), int(original_height * scale_factor))
    resized_logo = logo.resize(new_size, Image.LANCZOS)
    logo_tk = ImageTk.PhotoImage(resized_logo)
    logo_label = tk.Label(root, image=logo_tk)
    logo_label.image = logo_tk  
    difference = root.winfo_width()
    logo_label.place(x=difference-10, y=10, anchor='ne')

def save_debts_to_json():
    debts = []
    for child in debts_tree.get_children():
        debt = debts_tree.item(child, 'values')
        debts.append({'name': debt[0], 'amount': float(debt[1]), 'due_date': debt[2]})
    settings = {
        'initial_balance': initial_balance_entry.get(),
        'annual_interest_rate': annual_interest_rate_entry.get(),
        'start_date': start_date_entry.get(),
        'pay_immediately': pay_now_var.get()
    }
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'w') as f:
            json.dump({'debts': debts, 'settings': settings}, f, indent=4)
        messagebox.showinfo("Success", f"Debts and settings saved to {file_path}")

def load_debts_from_json():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            debts = data.get('debts', [])
            settings = data.get('settings', {})
            debts_tree.delete(*debts_tree.get_children())
            for debt in debts:
                debts_tree.insert("", tk.END, values=(debt['name'], debt['amount'], debt['due_date']))
            initial_balance_entry.delete(0, tk.END)
            initial_balance_entry.insert(0, settings.get('initial_balance', ''))
            annual_interest_rate_entry.delete(0, tk.END)
            annual_interest_rate_entry.insert(0, settings.get('annual_interest_rate', ''))
            start_date_entry.delete(0, tk.END)
            start_date_entry.insert(0, settings.get('start_date', ''))
            pay_now_var.set(settings.get('pay_immediately', False))
            messagebox.showinfo("Success", f"Debts and settings loaded from {file_path}")
        except FileNotFoundError:
            messagebox.showerror("Error", "The file does not exist.")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "The file is not a valid JSON file.")
    simulate_button.config(state="normal")

def debt_repayment_simulation(initial_balance, annual_interest_rate, start_date, debts, pay_immediately):
    daily_interest_rate = annual_interest_rate / 365 / 100
    start_date = pd.to_datetime(start_date)
    dates = pd.date_range(start=start_date, periods=30)
    balances = pd.DataFrame(index=dates, columns=['Balance'])
    balances.iloc[0] = initial_balance
    if pay_immediately:
        total_debt = sum(debt['amount'] for debt in debts)
        balances.iloc[0] -= total_debt
    for i in range(1, 30):
        date = dates[i]
        daily_balance = balances.iloc[i-1]['Balance']
        if not pay_immediately:
            for debt in debts:
                if pd.to_datetime(debt['due_date']) == date:
                    daily_balance -= debt['amount']
        interest_for_today = daily_balance * daily_interest_rate
        balances.iloc[i] = daily_balance + interest_for_today
    return balances

def simulate_and_plot():
    initial_balance = float(initial_balance_entry.get())
    annual_interest_rate = float(annual_interest_rate_entry.get())
    start_date = start_date_entry.get()
    pay_immediately = pay_now_var.get()
    debts = []
    for child in debts_tree.get_children():
        debt = debts_tree.item(child, 'values')
        debts.append({'name': debt[0], 'amount': float(debt[1]), 'due_date': debt[2]})
    result = debt_repayment_simulation(initial_balance, annual_interest_rate, start_date, debts, pay_immediately)
    fig, ax = plt.subplots(figsize=(5, 3))
    result.plot(kind='line', y='Balance', ax=ax)
    ax.set_title('Daily Balance Over 30 Days')
    ax.set_xlabel('Date')
    ax.set_ylabel('Balance')
    last_date = result.index[-1]
    last_balance = result.iloc[-1]['Balance']
    ax.annotate(f'{last_balance:.2f}', xy=(last_date, last_balance), xytext=(last_date, last_balance),
                arrowprops=dict(facecolor='black', shrink=0.05), ha='center')
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.grid(row=12, column=0, columnspan=3)
    canvas.draw()
    # Update the result label
    last_balance_label.config(text=f"Last balance: {last_balance:.2f}")

def submit_debt():
    selected_items = debts_tree.selection()
    debt_name = debt_name_entry.get()
    amount = debt_amount_entry.get()
    due_date = debt_due_date_entry.get()
    if selected_items:
        debts_tree.item(selected_items[0], values=(debt_name, amount, due_date))
    else:
        debts_tree.insert("", tk.END, values=(debt_name, amount, due_date))
    clear_entries()

def clear_entries():
    debt_name_entry.delete(0, tk.END)
    debt_amount_entry.delete(0, tk.END)
    debt_due_date_entry.delete(0, tk.END)
    debts_tree.selection_remove(debts_tree.selection())

def delete_debt():
    selected_item = debts_tree.selection()
    debts_tree.delete(selected_item)

def select_debt_for_edit(event):
    selected_item = debts_tree.selection()
    if selected_item:
        debt = debts_tree.item(selected_item, 'values')
        debt_name_entry.delete(0, tk.END)
        debt_name_entry.insert(0, debt[0])
        debt_amount_entry.delete(0, tk.END)
        debt_amount_entry.insert(0, debt[1])
        debt_due_date_entry.delete(0, tk.END)
        debt_due_date_entry.insert(0, debt[2])
        
def validate_entries(event=None):
    # Check if both initial balance and annual interest rate entries are not empty
    if initial_balance_entry.get() and annual_interest_rate_entry.get():
        simulate_button.config(state="normal")
    else:
        simulate_button.config(state="disabled")

root = tk.Tk()
root.title("Debt Repayment Simulation")
root.iconbitmap("icon.ico")
window_width = 500
window_height = 745
root.geometry(f"{window_width}x{window_height}")
root.resizable(0, 0)

# Variables
pay_now_var = tk.BooleanVar()

# GUI elements for initial conditions setup
initial_balance_label = tk.Label(root, text="Initial Balance:")
initial_balance_label.grid(row=0, column=0, sticky="w")
initial_balance_entry = tk.Entry(root)
initial_balance_entry.grid(row=0, column=1, sticky="w")

annual_interest_rate_label = tk.Label(root, text="Annual Interest Rate (%):")
annual_interest_rate_label.grid(row=1, column=0, sticky="w")
annual_interest_rate_entry = tk.Entry(root)
annual_interest_rate_entry.grid(row=1, column=1, sticky="w")

start_date_label = tk.Label(root, text="Start Date (YYYY-MM-DD):")
start_date_label.grid(row=2, column=0, sticky="w")
start_date_entry = DateEntry(root, date_pattern='y-mm-dd')
start_date_entry.grid(row=2, column=1, sticky="w")

# GUI elements for debt details entry
debt_name_label = tk.Label(root, text="Debt Name:")
debt_name_label.grid(row=4, column=0, sticky="w")
debt_name_entry = tk.Entry(root)
debt_name_entry.grid(row=4, column=1, sticky="w")

debt_amount_label = tk.Label(root, text="Amount:")
debt_amount_label.grid(row=5, column=0, sticky="w")
debt_amount_entry = tk.Entry(root)
debt_amount_entry.grid(row=5, column=1, sticky="w")

debt_due_date_label = tk.Label(root, text="Due Date (YYYY-MM-DD):")
debt_due_date_label.grid(row=6, column=0, sticky="w")
debt_due_date_entry = DateEntry(root, date_pattern='y-mm-dd')
debt_due_date_entry.grid(row=6, column=1, sticky="w")

# Debt Treeview setup
columns = ("debt_name", "amount", "due_date")
debts_tree = ttk.Treeview(root, columns=columns, show="headings")
debts_tree.heading("debt_name", text="Debt Name")
debts_tree.column("debt_name", width=200)
debts_tree.heading("amount", text="Amount")
debts_tree.column("amount", width=150)
debts_tree.heading("due_date", text="Due Date")
debts_tree.column("due_date", width=150)
debts_tree.grid(row=7, column=0, columnspan=3, sticky='nsew')

# Checkbox for immediate payment
pay_now_checkbox = tk.Checkbutton(root, text="Pay debts immediately", variable=pay_now_var)
pay_now_checkbox.grid(row=8, column=0)

# Buttons for debt management
submit_button = tk.Button(root, text="Add/Update Debt", command=submit_debt)
submit_button.grid(row=8, column=1)

delete_button = tk.Button(root, text="Delete Selected Debt", command=delete_debt)
delete_button.grid(row=8, column=2)

# Save debts to JSON button
save_debts_button = tk.Button(root, text="Save Debts to JSON", command=save_debts_to_json)
save_debts_button.grid(row=9, column=0, pady=5, padx=5, sticky="ew")

# Load debts from JSON button
load_debts_button = tk.Button(root, text="Load Debts from JSON", command=load_debts_from_json)
load_debts_button.grid(row=9, column=1, pady=5, padx=5, sticky="ew")

# Result label
last_balance_label = tk.Label(root, text="End Balance: ")
last_balance_label.grid(row=9, column=2, pady=5, padx=5, sticky="ew")

# Button for simulation
simulate_button = tk.Button(root, text="Simulate and Plot", command=simulate_and_plot, bg="yellow", state="disabled")
simulate_button.grid(row=10, column=1)

# Binding the select event to load selected debt for editing
debts_tree.bind('<Double-1>', select_debt_for_edit)

# Bind the validation function to the <<KeyRelease>> event for both entry widgets
initial_balance_entry.bind("<KeyRelease>", validate_entries)
annual_interest_rate_entry.bind("<KeyRelease>", validate_entries)

place_logo('logo.png', (100, 100), root)

root.mainloop()
