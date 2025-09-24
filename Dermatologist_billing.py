import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import tempfile
import os
import platform
import subprocess
import json
import re

# === Abstraction: Base class defining what a Treatment should have ===
class Treatment(ABC):
    @abstractmethod
    def get_cost(self):
        pass

    @abstractmethod
    def get_name(self):
        pass

# === Generic Treatment class for all treatments ===
class GenericTreatment(Treatment):
    def __init__(self, name, cost):
        self.__name = name
        self.__cost = cost

    def get_cost(self):
        return self.__cost

    def get_name(self):
        return self.__name

# === Patient Class (Encapsulation of patient data) ===
class Patient:
    def __init__(self, name, phone, patient_type="Normal", vip_discount=10):
        self.__name = name
        self.__phone = phone
        self.__treatments = []
        self.__prescription = ""
        self.__patient_type = patient_type
        self.__vip_discount = vip_discount

    def add_treatment(self, treatment: Treatment):
        self.__treatments.append(treatment)

    def set_prescription(self, prescription_text):
        self.__prescription = prescription_text

    def get_prescription(self):
        return self.__prescription

    def get_bill_text(self):
        width = 60
        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        lines = []
        lines.append("=" * width)
        lines.append(f"{' Reimagine Hair Transplant & Skin Care Clinic ':^{width}}")
        lines.append("=" * width)
        lines.append(f"Patient Name : {self.__name}")
        lines.append(f"Phone Number : {self.__phone}")
        lines.append(f"Patient Type : {self.__patient_type}")
        lines.append(f"Date & Time  : {now}")
        lines.append("-" * width)
        lines.append(f"{'Treatment':<35}{'Cost (Rs.)':>20}")
        lines.append("-" * width)

        total = 0
        for t in self.__treatments:
            lines.append(f"{t.get_name():<35}{t.get_cost():>20}")
            total += t.get_cost()

        discount = 0
        if self.__patient_type == "VIP":
            discount = total * (self.__vip_discount / 100)
            total_after_discount = total - discount
        else:
            total_after_discount = total

        lines.append("-" * width)
        if discount > 0:
            lines.append(f"{'Subtotal':<35}{total:>20.2f}")
            lines.append(f"{f'VIP Discount ({self.__vip_discount}%)':<35}{-discount:>20.2f}")
        lines.append(f"{'Total Bill':<35}{total_after_discount:>20.2f}")
        lines.append("=" * width)
        lines.append(f"{'Thank you for choosing our clinic!':^{width}}")
        lines.append("=" * width)

        return "\n".join(lines)

    def get_prescription_text(self):
        width = 60
        now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

        lines = []
        lines.append("=" * width)
        lines.append(f"{' Prescription ':^{width}}")
        lines.append("=" * width)
        lines.append(f"Patient Name : {self.__name}")
        lines.append(f"Phone Number : {self.__phone}")
        lines.append(f"Date & Time  : {now}")
        lines.append("-" * width)
        lines.append(self.__prescription if self.__prescription else "No prescription provided.")
        lines.append("=" * width)

        return "\n".join(lines)

# === Main GUI Application ===
class ClinicApp:
    TREATMENTS_FILE = "treatments.json"
    APPOINTMENTS_FILE = "appointments.json"

    def __init__(self, root):
        self.root = root
        self.root.title("Reimagine Hair Transplant & Skin Care Clinic")
        self.root.geometry("900x750")
        self.root.minsize(700, 650)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(4, weight=1)

        # Load treatments (if file missing, start with defaults)
        self.treatments_dict = self.load_treatments()
        if not self.treatments_dict:
            # sensible defaults
            self.treatments_dict = {
            }
            self.save_treatments()

        self.patient = None
        self.selected_treatments = []
        self.treatment_price_vars = {}

        self.create_widgets()

        # Check reminders for tomorrow
        self.check_appointments_reminder()

    # --------------------
    # Treatments persistence
    # --------------------
    def load_treatments(self):
        if os.path.exists(self.TREATMENTS_FILE):
            try:
                with open(self.TREATMENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {str(k): int(v) for k, v in data.items()}
            except Exception:
                return {}
        return {}

    def save_treatments(self):
        try:
            with open(self.TREATMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.treatments_dict, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save treatments:\n{e}")

    # --------------------
    # UI creation
    # --------------------
    def create_widgets(self):
        # Patient info frame
        frame_patient = ttk.LabelFrame(self.root, text="Patient Information")
        frame_patient.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        frame_patient.columnconfigure(1, weight=1)

        ttk.Label(frame_patient, text="Name:").grid(row=0, column=0, sticky="w")
        self.entry_name = ttk.Entry(frame_patient)
        self.entry_name.grid(row=0, column=1, sticky="ew")

        ttk.Label(frame_patient, text="Phone:").grid(row=1, column=0, sticky="w")
        self.entry_phone = ttk.Entry(frame_patient)
        self.entry_phone.grid(row=1, column=1, sticky="ew")

        ttk.Label(frame_patient, text="Patient Type:").grid(row=2, column=0, sticky="w")
        self.patient_type_var = tk.StringVar(value="Normal")
        frame_ptype = ttk.Frame(frame_patient)
        frame_ptype.grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(frame_ptype, text="Normal", variable=self.patient_type_var, value="Normal").pack(side="left")
        ttk.Radiobutton(frame_ptype, text="VIP", variable=self.patient_type_var, value="VIP").pack(side="left")

        ttk.Label(frame_patient, text="VIP Discount (%):").grid(row=3, column=0, sticky="w")
        self.vip_discount_var = tk.IntVar(value=10)
        self.entry_vip_discount = ttk.Entry(frame_patient, textvariable=self.vip_discount_var, width=6)
        self.entry_vip_discount.grid(row=3, column=1, sticky="w")

        # Treatments frame
        frame_treatments = ttk.LabelFrame(self.root, text="Treatments")
        frame_treatments.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        frame_treatments.columnconfigure(0, weight=1)

        self.treatment_listbox = tk.Listbox(frame_treatments, height=6, selectmode=tk.MULTIPLE)
        self.treatment_listbox.grid(row=0, column=0, rowspan=6, padx=5, pady=5, sticky="nsew")
        self.update_treatment_listbox()

        ttk.Button(frame_treatments, text="Add Selected Treatment(s)", command=self.add_selected_treatments).grid(row=0, column=1, padx=5, pady=3, sticky="ew")
        ttk.Button(frame_treatments, text="Add New Treatment", command=self.add_new_treatment).grid(row=1, column=1, padx=5, pady=3, sticky="ew")
        ttk.Button(frame_treatments, text="Remove Treatment", command=self.remove_treatment).grid(row=2, column=1, padx=5, pady=3, sticky="ew")

        # Selected treatments & editable prices
        frame_selected = ttk.LabelFrame(self.root, text="Selected Treatments and Prices")
        frame_selected.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        frame_selected.columnconfigure(1, weight=1)

        self.selected_treatments_frame = ttk.Frame(frame_selected)
        self.selected_treatments_frame.grid(row=0, column=0, sticky="ew")
        self.selected_treatments_frame.columnconfigure(1, weight=1)

        # Prescription
        frame_prescription = ttk.LabelFrame(self.root, text="Prescription")
        frame_prescription.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        self.text_prescription = tk.Text(frame_prescription, height=4)  
        self.text_prescription.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Buttons
        frame_buttons = ttk.Frame(self.root)
        frame_buttons.grid(row=5, column=0, pady=10, sticky="ew")
        frame_buttons.columnconfigure((0,1,2,3,4), weight=1)

        ttk.Button(frame_buttons, text="Generate Bill & Prescription", command=self.generate_bill_prescription).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(frame_buttons, text="Print Bill & Prescription", command=self.print_bill_and_prescription).grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(frame_buttons, text="Reset", command=self.reset_all).grid(row=0, column=2, padx=5, sticky="ew")
        ttk.Button(frame_buttons, text="Exit", command=self.root.quit).grid(row=0, column=3, padx=5, sticky="ew")

        ttk.Button(frame_buttons, text="Save Bill & Prescription to TXT", command=self.save_to_txt).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(frame_buttons, text="Book Appointment", command=self.book_appointment).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(frame_buttons, text="View Appointments", command=self.view_appointments).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        ttk.Button(frame_buttons, text="Refresh Treatments", command=self.update_treatment_listbox).grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Output (bill/prescription)
        frame_output = ttk.LabelFrame(self.root, text="Output")
        frame_output.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        frame_output.columnconfigure(0, weight=1)
        frame_output.rowconfigure(0, weight=1)

        self.text_output = tk.Text(frame_output)
        self.text_output.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    # --------------------
    # Treatments UI helpers
    # --------------------
    def update_treatment_listbox(self):
        self.treatment_listbox.delete(0, tk.END)
        for treatment_name, cost in self.treatments_dict.items():
            self.treatment_listbox.insert(tk.END, f"{treatment_name} (Rs. {cost})")

    def add_selected_treatments(self):
        selected_indices = self.treatment_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select at least one treatment.")
            return
        for idx in selected_indices:
            treatment_str = self.treatment_listbox.get(idx)
            treatment_name = treatment_str.split(" (")[0]
            if treatment_name not in self.selected_treatments:
                self.selected_treatments.append(treatment_name)
        self.update_selected_treatments_display()

    def update_selected_treatments_display(self):
        # Clear previous widgets
        for widget in self.selected_treatments_frame.winfo_children():
            widget.destroy()
        self.treatment_price_vars.clear()
        for i, t_name in enumerate(self.selected_treatments):
            ttk.Label(self.selected_treatments_frame, text=t_name).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            price_var = tk.IntVar(value=self.treatments_dict.get(t_name, 0))
            self.treatment_price_vars[t_name] = price_var
            ttk.Entry(self.selected_treatments_frame, textvariable=price_var, width=12).grid(row=i, column=1, sticky="w", padx=5, pady=2)

    def add_new_treatment(self):
        new_name = simpledialog.askstring("New Treatment", "Enter new treatment name:")
        if not new_name:
            return
        new_name = new_name.strip()
        if not new_name:
            return
        if new_name in self.treatments_dict:
            messagebox.showerror("Error", "Treatment already exists.")
            return
        try:
            new_price = simpledialog.askinteger("New Treatment Price", f"Enter price for {new_name} (Rs.):", minvalue=1)
            if new_price is None:
                return
        except Exception:
            messagebox.showerror("Error", "Invalid price entered.")
            return
        self.treatments_dict[new_name] = int(new_price)
        self.save_treatments()
        self.update_treatment_listbox()
        messagebox.showinfo("Success", f"Added new treatment: {new_name} (Rs. {new_price})")

    def remove_treatment(self):
        if not self.treatments_dict:
            messagebox.showinfo("Info", "No treatments available to remove.")
            return
        popup = tk.Toplevel(self.root)
        popup.title("Remove Treatment")
        popup.geometry("320x360")
        popup.grab_set()
        ttk.Label(popup, text="Select treatment(s) to remove:").pack(pady=5)
        listbox = tk.Listbox(popup, selectmode=tk.MULTIPLE)
        listbox.pack(expand=True, fill="both", padx=10, pady=5)
        for t in self.treatments_dict.keys():
            listbox.insert(tk.END, t)

        def on_remove():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select at least one treatment to remove.")
                return
            for idx in reversed(selected_indices):
                treatment_name = listbox.get(idx)
                if treatment_name in self.treatments_dict:
                    del self.treatments_dict[treatment_name]
                if treatment_name in self.selected_treatments:
                    self.selected_treatments.remove(treatment_name)
            self.save_treatments()
            self.update_treatment_listbox()
            self.update_selected_treatments_display()
            popup.destroy()

        ttk.Button(popup, text="Remove", command=on_remove).pack(pady=8)

    # --------------------
    # Bill & Prescription
    # --------------------
    def generate_bill_prescription(self):
        name = self.entry_name.get().strip()
        phone = self.entry_phone.get().strip()
        patient_type = self.patient_type_var.get()
        vip_discount = self.vip_discount_var.get()
        if not name or not phone:
            messagebox.showerror("Input Error", "Please enter patient name and phone number.")
            return
        # phone basic validation: allow digits, plus, spaces, dashes
        if not re.match(r"^[+\d][\d\s\-+()]{5,}$", phone):
            if not messagebox.askyesno("Phone format", "Phone number looks unusual. Continue anyway?"):
                return
        if not self.selected_treatments:
            messagebox.showerror("Input Error", "Please select at least one treatment.")
            return
        if patient_type == "VIP" and not (0 <= vip_discount <= 100):
            messagebox.showerror("Input Error", "VIP discount must be between 0 and 100.")
            return
        if patient_type != "VIP":
            vip_discount = 0

        self.patient = Patient(name, phone, patient_type, vip_discount)
        for t_name in self.selected_treatments:
            cost = self.treatment_price_vars[t_name].get()
            treatment_obj = GenericTreatment(t_name, cost)
            self.patient.add_treatment(treatment_obj)

        prescription_text = self.text_prescription.get("1.0", tk.END).strip()
        self.patient.set_prescription(prescription_text)

        bill_text = self.patient.get_bill_text()
        prescription_text = self.patient.get_prescription_text()

        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, bill_text + "\n\n" + prescription_text)

        # Auto-save to records folder (date-wise)
        date_folder = datetime.now().strftime("%Y-%m-%d")
        folder_path = os.path.join("records", date_folder)
        os.makedirs(folder_path, exist_ok=True)
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"{safe_name}_{datetime.now().strftime('%H%M%S')}.txt"
        filepath = os.path.join(folder_path, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(bill_text + "\n\n" + prescription_text)
        except Exception:
            pass  # non-fatal

    def print_bill_and_prescription(self):
        if not self.patient:
            messagebox.showerror("Error", "Generate bill and prescription first before printing.")
            return
        combined_text = self.patient.get_bill_text() + "\n\n" + self.patient.get_prescription_text()
        self.print_text(combined_text)

    def print_text(self, text_content):
        # create a temp text file and send to default printer (platform-dependent)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write(text_content)
            temp_filename = f.name
        try:
            if platform.system() == "Windows":
                os.startfile(temp_filename, 'print')
            elif platform.system() == "Darwin":
                subprocess.run(['lp', temp_filename])
            else:  # Linux
                subprocess.run(['lp', temp_filename])
            messagebox.showinfo("Success", "Document sent to printer")
        except Exception as e:
            messagebox.showerror("Print Error", f"Could not print: {str(e)}")
        finally:
            # remove after short delay
            try:
                self.root.after(5000, lambda: os.remove(temp_filename))
            except Exception:
                pass

    def save_to_txt(self):
        if not self.patient:
            messagebox.showerror("Error", "Generate bill and prescription first before saving.")
            return
        combined_text = self.patient.get_bill_text() + "\n\n" + self.patient.get_prescription_text()
        folder = "txt"
        os.makedirs(folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(folder, f"bill_prescription_{timestamp}.txt")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(combined_text)
            messagebox.showinfo("Success", f"Bill and prescription saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file:\n{str(e)}")

    def reset_all(self):
        self.entry_name.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.patient_type_var.set("Normal")
        self.vip_discount_var.set(10)
        self.text_prescription.delete("1.0", tk.END)
        self.text_output.delete("1.0", tk.END)
        self.selected_treatments.clear()
        self.treatment_price_vars.clear()
        self.update_selected_treatments_display()
        self.treatment_listbox.selection_clear(0, tk.END)
        self.patient = None

    # --------------------
    # Appointments persistence
    # --------------------
    def load_appointments(self):
        if os.path.exists(self.APPOINTMENTS_FILE):
            try:
                with open(self.APPOINTMENTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        else:
            return []

    def save_appointments(self, appointments):
        try:
            with open(self.APPOINTMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(appointments, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save appointments:\n{e}")

    # --------------------
    # Appointment actions
    # --------------------
    def book_appointment(self):
        popup = tk.Toplevel(self.root)
        popup.title("Book Appointment")
        popup.geometry("360x260")
        popup.grab_set()

        ttk.Label(popup, text="Patient Name:").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        entry_name = ttk.Entry(popup)
        entry_name.grid(row=0, column=1, padx=10, pady=6)
        # default to current name field if present
        entry_name.insert(0, self.entry_name.get().strip())

        ttk.Label(popup, text="Phone Number:").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        entry_phone = ttk.Entry(popup)
        entry_phone.grid(row=1, column=1, padx=10, pady=6)
        entry_phone.insert(0, self.entry_phone.get().strip())

        ttk.Label(popup, text="Appointment Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", padx=10, pady=6)
        entry_date = ttk.Entry(popup)
        entry_date.grid(row=2, column=1, padx=10, pady=6)

        def save_appointment():
            name = entry_name.get().strip()
            phone = entry_phone.get().strip()
            date_str = entry_date.get().strip()
            if not name or not phone or not date_str:
                messagebox.showerror("Input Error", "Please fill all fields.")
                return
            try:
                appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                if appt_date < datetime.now().date():
                    messagebox.showerror("Input Error", "Appointment date cannot be in the past.")
                    return
            except ValueError:
                messagebox.showerror("Input Error", "Invalid date format. Use YYYY-MM-DD.")
                return
            appointments = self.load_appointments()
            appointments.append({
                "name": name,
                "phone": phone,
                "date": date_str
            })
            self.save_appointments(appointments)
            messagebox.showinfo("Success", f"Appointment booked for {name} on {date_str}")
            popup.destroy()

        btn_save = ttk.Button(popup, text="Book", command=save_appointment)
        btn_save.grid(row=3, column=0, columnspan=2, pady=12)

    def check_appointments_reminder(self):
        appointments = self.load_appointments()
        tomorrow = datetime.now().date() + timedelta(days=1)
        due_appointments = [appt for appt in appointments if appt.get("date") == tomorrow.strftime("%Y-%m-%d")]
        if due_appointments:
            msg_lines = ["Appointments due tomorrow:"]
            for appt in due_appointments:
                msg_lines.append(f"- {appt.get('name')} (Phone: {appt.get('phone')}) on {appt.get('date')}")
            try:
                messagebox.showinfo("Appointment Reminder", "\n".join(msg_lines))
            except Exception:
                print("\n".join(msg_lines))

    # --------------------
    # View / Search / Edit / Delete appointments
    # --------------------
    def view_appointments(self):
        appointments = self.load_appointments()
        if not appointments:
            messagebox.showinfo("Appointments", "No appointments found.")
            return

        today = datetime.now().date()
        # keep only today or future
        upcoming = []
        for appt in appointments:
            try:
                appt_date = datetime.strptime(appt.get("date", ""), "%Y-%m-%d").date()
                if appt_date >= today:
                    upcoming.append(appt.copy())
            except Exception:
                continue

        if not upcoming:
            messagebox.showinfo("Appointments", "No upcoming appointments.")
            return

        upcoming.sort(key=lambda x: x.get("date"))

        popup = tk.Toplevel(self.root)
        popup.title("Upcoming Appointments")
        popup.geometry("620x480")
        popup.grab_set()

        ttk.Label(popup, text="Upcoming Appointments", font=("Arial", 12, "bold")).pack(pady=8)

        # Search bar
        frame_search = ttk.Frame(popup)
        frame_search.pack(fill="x", padx=12, pady=6)
        ttk.Label(frame_search, text="Search (name or phone):").pack(side="left")
        search_var = tk.StringVar()
        entry_search = ttk.Entry(frame_search, textvariable=search_var)
        entry_search.pack(side="left", expand=True, fill="x", padx=8)

        # Listbox with scrollbar
        frame_list = ttk.Frame(popup)
        frame_list.pack(expand=True, fill="both", padx=12, pady=6)

        scrollbar = ttk.Scrollbar(frame_list, orient=tk.VERTICAL)
        listbox = tk.Listbox(frame_list, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", expand=True, fill="both")

        def populate_list(filtered_list):
            listbox.delete(0, tk.END)
            for appt in filtered_list:
                listbox.insert(tk.END, f"{appt.get('date')}  |  {appt.get('name')}  |  {appt.get('phone')}")

        # initial populate
        populate_list(upcoming)

        # search function
        def search_appointments(*args):
            q = search_var.get().strip().lower()
            if not q:
                populate_list(upcoming)
                return
            filtered = [appt for appt in upcoming if q in appt.get("name", "").lower() or q in appt.get("phone", "")]
            populate_list(filtered)

        search_var.trace_add("write", search_appointments)

        # delete selected
        def delete_selected():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select an appointment to delete.")
                return
            index = sel[0]
            # compute current filtered list
            q = search_var.get().strip().lower()
            current_list = [appt for appt in upcoming if q in appt.get("name", "").lower() or q in appt.get("phone", "")]
            if index >= len(current_list):
                return
            appt_to_delete = current_list[index]
            # remove from saved appointments
            saved = self.load_appointments()
            # remove the first matching item with same name+phone+date
            for i, a in enumerate(saved):
                if a.get("name") == appt_to_delete.get("name") and a.get("phone") == appt_to_delete.get("phone") and a.get("date") == appt_to_delete.get("date"):
                    del saved[i]
                    break
            self.save_appointments(saved)
            # update upcoming and UI
            upcoming.remove(appt_to_delete)
            search_appointments()
            messagebox.showinfo("Deleted", f"Appointment for {appt_to_delete['name']} on {appt_to_delete['date']} deleted.")

        # edit selected
        def edit_selected():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select an appointment to edit.")
                return
            index = sel[0]
            q = search_var.get().strip().lower()
            current_list = [appt for appt in upcoming if q in appt.get("name", "").lower() or q in appt.get("phone", "")]
            if index >= len(current_list):
                return
            appt_to_edit = current_list[index]

            # Edit date
            new_date_str = simpledialog.askstring("Edit Date", f"Enter new date (YYYY-MM-DD) [Current: {appt_to_edit['date']}]:", parent=popup)
            if new_date_str:
                try:
                    new_date = datetime.strptime(new_date_str, "%Y-%m-%d").date()
                    if new_date < datetime.now().date():
                        messagebox.showerror("Invalid Date", "Appointment date cannot be in the past.")
                        return
                    appt_to_edit["date"] = new_date_str
                except Exception:
                    messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
                    return

            # Edit phone
            new_phone = simpledialog.askstring("Edit Phone", f"Enter new phone [Current: {appt_to_edit['phone']}]:", parent=popup)
            if new_phone:
                appt_to_edit["phone"] = new_phone

            # Save changes to the persisted appointments (match by previous unique triple)
            saved = self.load_appointments()
            for i, a in enumerate(saved):
                if a.get("name") == appt_to_edit.get("name") and a.get("date") == a.get("date") and a.get("phone") == a.get("phone"):
                    # this logic may not find exact match in mutated case; safer approach: find by name+old date+old phone from current_list before edit
                    pass

            # Safer: find by name and any date/phone among saved and update the first occurrence that matches name
            updated = False
            for i, a in enumerate(saved):
                if a.get("name") == appt_to_edit.get("name"):
                    saved[i] = {"name": appt_to_edit["name"], "phone": appt_to_edit["phone"], "date": appt_to_edit["date"]}
                    updated = True
                    break

            if not updated:
                # fallback: append as new
                saved.append({"name": appt_to_edit["name"], "phone": appt_to_edit["phone"], "date": appt_to_edit["date"]})

            self.save_appointments(saved)

            # refresh upcoming list (rebuild)
            # reload from saved and re-filter today+
            new_upcoming = []
            saved2 = self.load_appointments()
            for ap in saved2:
                try:
                    d = datetime.strptime(ap.get("date", ""), "%Y-%m-%d").date()
                    if d >= datetime.now().date():
                        new_upcoming.append(ap.copy())
                except Exception:
                    continue
            # replace upcoming with new list sorted
            upcoming.clear()
            upcoming.extend(sorted(new_upcoming, key=lambda x: x.get("date")))
            search_appointments()
            messagebox.showinfo("Updated", f"Appointment updated for {appt_to_edit['name']}.")

        # Buttons frame
        frame_btns = ttk.Frame(popup)
        frame_btns.pack(pady=8)
        btn_delete = ttk.Button(frame_btns, text="Delete Selected", command=delete_selected)
        btn_delete.pack(side="left", padx=6)
        btn_edit = ttk.Button(frame_btns, text="Edit Selected", command=edit_selected)
        btn_edit.pack(side="left", padx=6)
        btn_close = ttk.Button(frame_btns, text="Close", command=popup.destroy)
        btn_close.pack(side="left", padx=6)

    # --------------------
    # End of class
    # --------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = ClinicApp(root)
    root.mainloop()
