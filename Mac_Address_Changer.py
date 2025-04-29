from customtkinter import *
from tkinter import messagebox
import subprocess

class MacChanger():
    def __init__(self):
        pass
    
    def get_network_interfaces(self):
        try:
            result = subprocess.run(["ifconfig", "-a"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode()
            # Remove colon from interface names and filter empty lines
            interfaces = [line.split()[0].rstrip(':') 
                        for line in output.split('\n') 
                        if line and not line.startswith(' ')]
            return interfaces
        except Exception as e:
            print(f"Error getting interfaces: {e}")
            return ["eth0"]  # fallback to eth0 if detection fails
    
    def show_mac_address(self, interface):
        try:
            result = subprocess.run(["ifconfig", interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode()
            if "ether" in output:
                mac_address = output.split("ether ")[1].split(" ")[0]
                return mac_address
            return f"No MAC address found for {interface}"
        except Exception as e:
            return f"Could not determine MAC address: {e}"
    
    def change_mac_address(self, interface, new_mac):
        try:
            subprocess.run(["sudo", "ifconfig", interface, "down"], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "hw", "ether", new_mac], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "up"], check=True)
            return True, f"MAC address changed successfully on {interface}"
        except subprocess.CalledProcessError as e:
            return False, f"Error changing MAC address on {interface}: {e}"
        except Exception as e:
            return False, f"Unexpected error on {interface}: {e}"
    
    def reset_mac_address(self, interface):
        try:
            original_mac = self.show_mac_address(interface)
            if "Could not determine" in original_mac or "No MAC" in original_mac:
                return False, original_mac
            
            subprocess.run(["sudo", "ifconfig", interface, "down"], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "hw", "ether", original_mac], check=True)
            subprocess.run(["sudo", "ifconfig", interface, "up"], check=True)
            return True, f"MAC address reset successfully on {interface}"
        except subprocess.CalledProcessError as e:
            return False, f"Error resetting MAC address on {interface}: {e}"
        except Exception as e:
            return False, f"Unexpected error on {interface}: {e}"

class GUI():
    def __init__(self, master):
        self.master = master
        self.mac_changer = MacChanger()
        self.current_interface = None
        
        self.master.title("Mac Address Changer")
        self.master.geometry("700x550")
        self.master.resizable(False, False)
        self.master.configure(bg="#2C2F33")
        
        self.frame = CTkFrame(self.master, fg_color="#2C2F33")
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        CTkLabel(self.frame, text="Mac Address Changer", text_color="white", font=("Arial", 24)).pack(pady=10)
        
        # Interface Selection
        self.interface_frame = CTkFrame(self.frame)
        self.interface_frame.pack(pady=10,padx=10, fill="x")
        
        CTkLabel(self.interface_frame, text="Network Interface:", text_color="white", font=("Arial", 14)).pack(side="left", padx=10)
        self.interface_var = StringVar()
        self.interface_dropdown = CTkOptionMenu(self.interface_frame, variable=self.interface_var, values=[])
        self.interface_dropdown.pack(side="left", padx=5)
        
        CTkButton(self.interface_frame, text="Refresh Interfaces", command=self.refresh_interfaces, width=150).pack(side="right", padx=10)
        
        # Buttons
        CTkButton(self.frame, text="Show Mac Address", command=self.show_mac_address, width=200).pack(pady=5)
        CTkButton(self.frame, text="Change Mac Address", command=self.change_mac_address, width=200).pack(pady=5)
        
        
        # Current MAC address display
        self.current_mac_label = CTkLabel(self.frame, text="Current MAC Address:", text_color="white", font=("Arial", 16))
        self.current_mac_label.pack(pady=5)
        self.current_mac_value = CTkLabel(self.frame, text="Select an interface first", text_color="white", font=("Arial", 16))
        self.current_mac_value.pack(pady=5)
        
        # New MAC address entry
        CTkLabel(self.frame, text="New Mac Address:", text_color="white", font=("Arial", 16)).pack(pady=5)
        self.new_mac_entry = CTkEntry(self.frame, placeholder_text="00:00:00:00:00:00", width=200)
        self.new_mac_entry.pack(pady=5)
        
        # Status display
        self.status_value = CTkLabel(self.frame, text="", text_color="white", font=("Arial", 16))
        self.status_value.pack(pady=5)
        
        # Error display
        self.error_value = CTkLabel(self.frame, text="", text_color="red", font=("Arial", 16))
        self.error_value.pack(pady=5)
        
        # Note
        CTkLabel(self.frame, 
                text="Note: Please select an interface and enter a valid MAC address", 
                text_color="white", 
                font=("Arial", 12)).pack(pady=5)
        
        # Initialize interfaces
        self.refresh_interfaces()
    
    def refresh_interfaces(self):
        interfaces = self.mac_changer.get_network_interfaces()
        if not interfaces:
            messagebox.showerror("Error", "No network interfaces found!")
            return
        
        self.interface_dropdown.configure(values=interfaces)
        self.interface_var.set(interfaces[0])
        self.current_interface = interfaces[0]
        self.update_current_mac()
    
    def update_current_mac(self):
        if not self.current_interface:
            return
        
        current_mac = self.mac_changer.show_mac_address(self.current_interface)
        self.current_mac_value.configure(text=current_mac)
    
    def show_mac_address(self):
        self.current_interface = self.interface_var.get()
        if not self.current_interface:
            self.error_value.configure(text="Please select an interface first")
            return
        
        self.update_current_mac()
        self.status_value.configure(text=f"Current MAC address displayed for {self.current_interface}")
        self.error_value.configure(text="")
    
    def change_mac_address(self):
        self.current_interface = self.interface_var.get()
        if not self.current_interface:
            self.error_value.configure(text="Please select an interface first")
            return
        
        new_mac = self.new_mac_entry.get()
        if not new_mac:
            self.error_value.configure(text="Please enter a MAC address")
            return
        
        success, message = self.mac_changer.change_mac_address(self.current_interface, new_mac)
        if success:
            self.status_value.configure(text=message)
            self.error_value.configure(text="")
            self.update_current_mac()
        else:
            self.error_value.configure(text=message)
            self.status_value.configure(text="Change failed")
    
    

if __name__ == "__main__":
    root = CTk()
    app = GUI(root)
    root.mainloop()