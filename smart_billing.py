import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import winsound
from datetime import datetime
import json
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
# Add this import at the top
import qrcode
from PIL import Image
import tkinter.filedialog as filedialog

class SmartBillingSystem:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Smart Billing System")
        self.window.geometry("1200x800")
        
        # Local product database (dictionary)
        self.products = {
            '8901234567890': {'name': 'Milk 1L', 'price': 60.00},
            '8902345678901': {'name': 'Bread', 'price': 40.00},
            '8903456789012': {'name': 'Eggs (6pcs)', 'price': 48.00},
            '8904567890123': {'name': 'Butter 500g', 'price': 250.00},
            '8905678901234': {'name': 'Cheese 200g', 'price': 120.00}
        }
        
        # Current bill items
        self.bill_items = []
        self.total_amount = 0.0
        
        self.setup_gui()
        self.setup_camera()
        
    def setup_gui(self):
        # Left panel - Camera feed
        self.camera_label = tk.Label(self.window)
        self.camera_label.place(x=20, y=20, width=480, height=360)
        
        # Right panel - Billing table
        columns = ('name', 'price', 'quantity', 'total')
        self.bill_table = ttk.Treeview(self.window, columns=columns, show='headings')
        
        # Set column headings
        self.bill_table.heading('name', text='Product')
        self.bill_table.heading('price', text='Price')
        self.bill_table.heading('quantity', text='Qty')
        self.bill_table.heading('total', text='Total')
        
        self.bill_table.place(x=520, y=20, width=660, height=360)
        
        # Total amount label
        self.total_label = tk.Label(self.window, text="Total: ₹0.00", 
                                  font=('Arial', 20, 'bold'))
        self.total_label.place(x=520, y=400)
        
        # Buttons
        # Add customer name field (add after total label)
        tk.Label(self.window, text="Customer Name:", 
                font=('Arial', 12)).place(x=520, y=450)
        self.customer_name_entry = tk.Entry(self.window, font=('Arial', 12))
        self.customer_name_entry.place(x=650, y=450, width=200)
        
        # Move other buttons down
        tk.Button(self.window, text="Generate Bill", command=self.generate_bill,
                 font=('Arial', 12)).place(x=520, y=490)
        
        tk.Button(self.window, text="Clear", command=self.clear_bill,
                 font=('Arial', 12)).place(x=650, y=490)
        
        # Manual entry
        tk.Label(self.window, text="Manual Barcode Entry:",
                font=('Arial', 12)).place(x=20, y=400)
        self.barcode_entry = tk.Entry(self.window, font=('Arial', 12))
        self.barcode_entry.place(x=20, y=430, width=200)
        tk.Button(self.window, text="Add", command=self.manual_add,
                 font=('Arial', 12)).place(x=230, y=428)
        
        # Add QR Code Generation section
        tk.Label(self.window, text="Generate QR Code", 
                font=('Arial', 14, 'bold')).place(x=20, y=500)
        
        # Product details entry
        tk.Label(self.window, text="Barcode:", 
                font=('Arial', 12)).place(x=20, y=540)
        self.qr_barcode_entry = tk.Entry(self.window, font=('Arial', 12))
        self.qr_barcode_entry.place(x=120, y=540, width=200)
        
        tk.Label(self.window, text="Product Name:", 
                font=('Arial', 12)).place(x=20, y=580)
        self.qr_name_entry = tk.Entry(self.window, font=('Arial', 12))
        self.qr_name_entry.place(x=120, y=580, width=200)
        
        tk.Label(self.window, text="Price (₹):", 
                font=('Arial', 12)).place(x=20, y=620)
        self.qr_price_entry = tk.Entry(self.window, font=('Arial', 12))
        self.qr_price_entry.place(x=120, y=620, width=200)
        
        # Generate button
        tk.Button(self.window, text="Generate QR Code", 
                 command=self.generate_qr_code,
                 font=('Arial', 12)).place(x=120, y=660)
                 
    def generate_qr_code(self):
        barcode = self.qr_barcode_entry.get().strip()
        name = self.qr_name_entry.get().strip()
        try:
            price = float(self.qr_price_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Invalid price")
            return
            
        if not all([barcode, name, price]):
            messagebox.showerror("Error", "All fields are required")
            return
            
        # Add to products dictionary
        self.products[barcode] = {'name': name, 'price': price}
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(barcode)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            initialfile=f"qr_{barcode}.png"
        )
        
        if filename:
            qr_image.save(filename)
            messagebox.showinfo("Success", 
                f"QR Code generated and saved as {filename}\nBarcode: {barcode}")
            
            # Clear entries
            self.qr_barcode_entry.delete(0, tk.END)
            self.qr_name_entry.delete(0, tk.END)
            self.qr_price_entry.delete(0, tk.END)
        
    def setup_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.update_camera()
        
    def update_camera(self):
        ret, frame = self.cap.read()
        if ret:
            # Use QR Code detector instead of pyzbar
            qr_detector = cv2.QRCodeDetector()
            retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)
            
            if retval:
                for barcode_data in decoded_info:
                    if barcode_data:  # if data is not empty
                        self.process_barcode(barcode_data)
                        # Draw rectangle around QR code
                        if points is not None:
                            pts = points.astype(int)
                            cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
            
            # Convert frame for display
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (480, 360))
            photo = tk.PhotoImage(data=cv2.imencode('.png', frame)[1].tobytes())
            self.camera_label.photo = photo
            self.camera_label.configure(image=photo)
        
        self.window.after(10, self.update_camera)
        
    def process_barcode(self, barcode_data):
        if barcode_data in self.products:
            # Play beep sound
            winsound.Beep(1000, 100)
            
            # Add to bill
            product = self.products[barcode_data]
            self.add_to_bill(product)
            
    def add_to_bill(self, product):
        # Check if product already in bill
        for item in self.bill_items:
            if item['name'] == product['name']:
                item['quantity'] += 1
                item['total'] = item['quantity'] * item['price']
                self.update_bill_display()
                return
        
        # Add new item
        item = {
            'name': product['name'],
            'price': product['price'],
            'quantity': 1,
            'total': product['price']
        }
        self.bill_items.append(item)
        self.update_bill_display()
        
    def update_bill_display(self):
        # Clear current display
        for item in self.bill_table.get_children():
            self.bill_table.delete(item)
        
        # Update table
        self.total_amount = 0
        for item in self.bill_items:
            self.bill_table.insert('', 'end', values=(
                item['name'],
                f"₹{item['price']:.2f}",
                item['quantity'],
                f"₹{item['total']:.2f}"
            ))
            self.total_amount += item['total']
        
        # Update total
        self.total_label.config(text=f"Total: ₹{self.total_amount:.2f}")
        
    def manual_add(self):
        barcode = self.barcode_entry.get().strip()
        if barcode in self.products:
            self.process_barcode(barcode)
            self.barcode_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Invalid barcode")
            
    def generate_bill(self):
        if not self.bill_items:
            messagebox.showerror("Error", "No items in bill")
            return
            
        # Get customer name
        customer_name = self.customer_name_entry.get().strip()
        if not customer_name:
            customer_name = "Guest"
            
        # Generate PDF bill
        filename = f"bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        
        # Add software name and header
        c.setFont("Helvetica-Bold", 28)
      #  c.drawString(50, 780, "ProBill360")
        
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, 750, "Smart Billing System")
        
        # Add customer name and date
        c.setFont("Helvetica", 12)
        c.drawString(50, 720, f"Customer: {customer_name}")
        c.drawString(50, 700, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add items (adjust y coordinate for new customer line)
        y = 660
        c.drawString(50, y, "Product")
        c.drawString(250, y, "Price")
        c.drawString(350, y, "Qty")
        c.drawString(450, y, "Total")
        
        y -= 20
        for item in self.bill_items:
            c.drawString(50, y, item['name'])
            c.drawString(250, y, f"₹{item['price']:.2f}")
            c.drawString(350, y, str(item['quantity']))
            c.drawString(450, y, f"₹{item['total']:.2f}")
            y -= 20
            
        # Add total
        c.setFont("Helvetica-Bold", 14)
        c.drawString(350, y-20, f"Total: ₹{self.total_amount:.2f}")
        
        # Add circular stamp
        c.saveState()
        c.setStrokeColorRGB(0.7, 0, 0)  # Dark red color for stamp
        c.setFillColorRGB(0.7, 0, 0)
        c.circle(300, y-100, 40, stroke=1, fill=0)  # Outer circle
        
        # Add "Visit Again" text in stamp
        c.setFont("Helvetica-Bold", 12)
        c.rotate(30)  # Rotate text slightly
        c.drawString(240, y-180, "Visit Again")
        c.restoreState()
        
        # Add toll-free number at bottom
        c.setFont("Helvetica", 10)
        c.drawString(50, 50, "For Support: Toll-Free 1800-123-4567")
        c.drawString(50, 35, "Thank you for choosing ProBill360!")
        
        c.save()
        messagebox.showinfo("Success", f"Bill generated: {filename}")
        
    def clear_bill(self):
        self.bill_items = []
        self.customer_name_entry.delete(0, tk.END)
        self.update_bill_display()
        
    def run(self):
        self.window.mainloop()
        self.cap.release()

if __name__ == "__main__":
    app = SmartBillingSystem()
    app.run()