import json
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QFormLayout,
    QSpinBox, QDateTimeEdit, QComboBox, QDialogButtonBox, QMessageBox,
    QFileDialog, QTextEdit
)
from PyQt5.QtCore import QDateTime, QStandardPaths
from datetime import datetime
import sys
from PyQt5.QtGui import QColor

### Booking Class
class Booking:
    def __init__(self, booking_id, check_in, num_guests, room_id, is_paid=False):
        self.booking_id = booking_id
        self.check_in = check_in
        self.check_out = None
        self.num_guests = num_guests
        self.room_id = room_id
        self.is_paid = is_paid
        self.checkout_reason = None
        self.checkout_notes = None

    def to_dict(self):
        return {
            "booking_id": self.booking_id,
            "check_in": self.check_in.isoformat(),
            "num_guests": self.num_guests,
            "room_id": self.room_id,
            "check_out": self.check_out.isoformat() if self.check_out else None,
            "is_paid": self.is_paid,
            "checkout_reason": self.checkout_reason,
            "checkout_notes": self.checkout_notes
        }

    @staticmethod
    def from_dict(data):
        """Create a Booking instance from a dictionary."""
        booking = Booking(
            booking_id=data["booking_id"],
            check_in=datetime.fromisoformat(data["check_in"]),
            num_guests=data["num_guests"],
            room_id=data["room_id"],
            is_paid=data.get("is_paid", False)
        )
        booking.check_out = datetime.fromisoformat(data["check_out"]) if data["check_out"] else None
        booking.checkout_reason = data.get("checkout_reason")
        booking.checkout_notes = data.get("checkout_notes")
        return booking

    def checkout_status(self):
        """Determine checkout status with more detailed information."""
        if self.check_out:
            status = f"Checked out ({self.checkout_reason})"
            if self.checkout_reason == "Emergency" and self.checkout_notes:
                status += f": {self.checkout_notes}"
            return status
        return "Currently checked in"

### HotelManager Class
class HotelManager:
    def __init__(self):
        self.bookings = []
        self.next_id = 1
        self.available_rooms = list(range(1, 51))  # Room numbers 1 to 50
        self.maintenance_rooms = []  # Rooms under maintenance

    def check_in(self, num_guests, check_in_datetime, room_id, is_paid=False):
        """Add a new booking."""
        if room_id not in self.available_rooms or room_id in self.maintenance_rooms:
            raise ValueError("Room ID is not available.")
        
        booking = Booking(self.next_id, check_in_datetime, num_guests, room_id, is_paid)
        self.bookings.append(booking)
        self.available_rooms.remove(room_id)  # Mark room as booked
        self.next_id += 1
        
        self.save_data(self.get_default_data_path())  # Save data after each operation

    def check_out(self, booking_id, check_out_datetime, reason="Normal", notes=None):
        """Check out a booking with reason and optional notes."""
        for booking in self.bookings:
            if booking.booking_id == booking_id:
                if booking.check_out is None and check_out_datetime > booking.check_in:
                    booking.check_out = check_out_datetime
                    booking.checkout_reason = reason
                    booking.checkout_notes = notes
                    self.available_rooms.append(booking.room_id)
                    self.save_data(self.get_default_data_path())
                    return True
                return False
        return False

    def mark_room_under_maintenance(self, room_id):
        """Mark a room as under maintenance."""
        if room_id in self.available_rooms:
            self.available_rooms.remove(room_id)
            self.maintenance_rooms.append(room_id)
            self.save_data(self.get_default_data_path())

    def mark_room_repaired(self, room_id):
        """Mark a room as repaired."""
        if room_id in self.maintenance_rooms:
            self.maintenance_rooms.remove(room_id)
            self.available_rooms.append(room_id)
            self.save_data(self.get_default_data_path())

    def get_current_bookings(self):
        """Return a list of current bookings."""
        return [b for b in self.bookings if b.check_out is None]

    def get_checked_out_bookings(self):
        """Return a list of checked-out bookings."""
        return [b for b in self.bookings if b.check_out is not None]

    def get_total_guests(self):
        """Calculate total guests staying."""
        return sum(b.num_guests for b in self.get_current_bookings())

    def get_available_rooms(self):
        """Return available room IDs."""
        return self.available_rooms

    def get_unavailable_rooms(self):
        """Return unavailable room IDs."""
        return [b.room_id for b in self.bookings if b.check_out is None] + self.maintenance_rooms

    def get_default_data_path(self):
        """Get the default path for saving data."""
        docs_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        return os.path.join(docs_path, "hotel_data.json")

    def save_data(self, filename):
        """Save bookings to a JSON file."""
        data = {
            "next_id": self.next_id,
            "available_rooms": self.available_rooms,
            "maintenance_rooms": self.maintenance_rooms,
            "bookings": [booking.to_dict() for booking in self.bookings]
        }
        try:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def load_data(self, filename):
        """Load bookings from a JSON file."""
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
                self.next_id = data.get("next_id", 1)
                self.available_rooms = data.get("available_rooms", list(range(1, 51)))
                self.maintenance_rooms = data.get("maintenance_rooms", [])
                self.bookings = [Booking.from_dict(b) for b in data.get("bookings", [])]
            return True
        except FileNotFoundError:
            print("No data file found. Starting with empty data.")
            return False
        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def clear_checked_out_bookings(self):
        """Remove all checked-out bookings while keeping active ones."""
        checked_out_bookings = self.get_checked_out_bookings()
        for booking in checked_out_bookings:
            self.bookings.remove(booking)
        self.save_data(self.get_default_data_path())
        return len(checked_out_bookings)

    def save_to_txt(self):
        """Save current data to a text file."""
        try:
            docs_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            file_path = os.path.join(docs_path, "hotel_report.txt")
            
            with open(file_path, 'w') as file:
                file.write("=== Hotel Management System Report ===\n")
                file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                file.write("== Current Bookings ==\n")
                current_bookings = self.get_current_bookings()
                if current_bookings:
                    for booking in current_bookings:
                        file.write(f"ID: {booking.booking_id}, Room: {booking.room_id}, Guests: {booking.num_guests}, "
                                 f"Check-in: {booking.check_in.strftime('%Y-%m-%d %H:%M:%S')}, "
                                 f"Paid: {'Yes' if booking.is_paid else 'No'}\n")
                else:
                    file.write("No current bookings\n")
                
                file.write("\n== Room Status ==\n")
                file.write(f"Available rooms: {len(self.available_rooms)}\n")
                file.write(f"Booked rooms: {len([b for b in self.bookings if b.check_out is None])}\n")
                file.write(f"Maintenance rooms: {len(self.maintenance_rooms)}\n")
                
                file.write("\n== Statistics ==\n")
                file.write(f"Total guests currently staying: {self.get_total_guests()}\n")
            
            return file_path
        except Exception as e:
            print(f"Error saving to TXT: {e}")
            return None

### MainWindow Class
class MainWindow(QMainWindow):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Hotel Counter Application (Offline)")
        self.setMinimumSize(800, 600)

        # Set up the central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Buttons for various actions
        button_layout = QHBoxLayout()
        self.check_in_button = QPushButton("Check In", self)
        self.check_out_button = QPushButton("Check Out", self)
        self.room_status_button = QPushButton("Show Room Status", self)
        self.mark_maintenance_button = QPushButton("Mark Room Under Maintenance", self)
        self.mark_repaired_button = QPushButton("Mark Room Repaired", self)
        self.save_button = QPushButton("Save Data", self)
        self.load_button = QPushButton("Load Data", self)
        self.clear_checked_out_button = QPushButton("Clear Checked-Out", self)
        self.save_txt_button = QPushButton("Generate Report", self)

        button_layout.addWidget(self.check_in_button)
        button_layout.addWidget(self.check_out_button)
        button_layout.addWidget(self.room_status_button)
        button_layout.addWidget(self.mark_maintenance_button)
        button_layout.addWidget(self.mark_repaired_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.clear_checked_out_button)
        button_layout.addWidget(self.save_txt_button)
        layout.addLayout(button_layout)

        # Table to display current bookings
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Check-in", "Check-out", "Guests", "Room ID", "Paid", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Label to show total guests
        self.total_label = QLabel(self)
        layout.addWidget(self.total_label)

        # Connect buttons to their functions
        self.check_in_button.clicked.connect(self.open_check_in_dialog)
        self.check_out_button.clicked.connect(self.open_check_out_dialog)
        self.room_status_button.clicked.connect(self.show_room_status)
        self.mark_maintenance_button.clicked.connect(self.open_maintenance_dialog)
        self.mark_repaired_button.clicked.connect(self.open_repaired_dialog)
        self.save_button.clicked.connect(self.save_data)
        self.load_button.clicked.connect(self.load_data)
        self.clear_checked_out_button.clicked.connect(self.clear_checked_out_data)
        self.save_txt_button.clicked.connect(self.save_to_txt)

        # Load data when the application starts
        self.load_initial_data()

        # Initial UI update
        self.refresh_table()
        self.refresh_total_guests()

    def load_initial_data(self):
        """Load data from default location on startup."""
        default_path = self.manager.get_default_data_path()
        if os.path.exists(default_path):
            self.manager.load_data(default_path)

    def open_check_in_dialog(self):
        """Open the check-in dialog and process the input if accepted."""
        dialog = CheckInDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            num_guests = dialog.get_num_guests()
            check_in_dt = dialog.get_check_in_datetime()
            room_id = dialog.get_room_id()
            is_paid = dialog.get_payment_status()
            try:
                self.manager.check_in(num_guests, check_in_dt, room_id, is_paid)
                self.refresh_table()
                self.refresh_total_guests()
            except ValueError as e:
                QMessageBox.warning(self, "Room Unavailable", str(e))

    def open_check_out_dialog(self):
        """Open the enhanced check-out dialog."""
        current_bookings = self.manager.get_current_bookings()
        if not current_bookings:
            QMessageBox.information(self, "No Bookings", "There are no current bookings to check out.")
            return
        
        booking_ids = [str(b.booking_id) for b in current_bookings]
        dialog = EnhancedCheckOutDialog(booking_ids, self)
        
        if dialog.exec_() == QDialog.Accepted:
            selected_id = int(dialog.get_selected_booking_id())
            check_out_dt = dialog.get_check_out_datetime()
            reason = dialog.get_checkout_reason()
            notes = dialog.get_checkout_notes()
            
            if self.manager.check_out(selected_id, check_out_dt, reason, notes):
                self.refresh_table()
                self.refresh_total_guests()
            else:
                QMessageBox.warning(self, "Check-out Failed", 
                                  "Could not check out. The booking may already be checked out or the check-out time is before check-in.")

    def show_room_status(self):
        """Show available and unavailable rooms in a dialog."""
        available_rooms = self.manager.get_available_rooms()
        unavailable_rooms = self.manager.get_unavailable_rooms()

        message = "Available Rooms: " + ", ".join(map(str, sorted(available_rooms))) + "\n"
        message += "Unavailable Rooms: " + ", ".join(map(str, sorted(unavailable_rooms)))

        QMessageBox.information(self, "Room Status", message)

    def open_maintenance_dialog(self):
        """Open a dialog to mark a room under maintenance."""
        dialog = MaintenanceDialog(self.manager, self)
        dialog.exec_()
        self.refresh_table()

    def open_repaired_dialog(self):
        """Open a dialog to mark a room as repaired."""
        dialog = RepairedDialog(self.manager, self)
        dialog.exec_()
        self.refresh_table()

    def save_data(self):
        """Save current data to a file."""
        default_path = self.manager.get_default_data_path()
        filename, _ = QFileDialog.getSaveFileName(self, "Save Data", default_path, "JSON Files (*.json)")
        if filename:
            if self.manager.save_data(filename):
                QMessageBox.information(self, "Save Data", "Data saved successfully.")
            else:
                QMessageBox.warning(self, "Save Data", "Failed to save data.")

    def load_data(self):
        """Load data from a file."""
        default_path = self.manager.get_default_data_path()
        filename, _ = QFileDialog.getOpenFileName(self, "Load Data", default_path, "JSON Files (*.json)")
        if filename:
            if self.manager.load_data(filename):
                self.refresh_table()
                self.refresh_total_guests()
                QMessageBox.information(self, "Load Data", "Data loaded successfully.")
            else:
                QMessageBox.warning(self, "Load Data", "Failed to load data.")

    def clear_checked_out_data(self):
        """Clear all checked-out bookings after confirmation."""
        checked_out_count = len(self.manager.get_checked_out_bookings())
        
        if checked_out_count == 0:
            QMessageBox.information(self, "No Checked-Out Bookings", 
                                  "There are no checked-out bookings to clear.")
            return
            
        reply = QMessageBox.question(
            self, "Confirm Clear",
            f"Are you sure you want to clear all {checked_out_count} checked-out bookings?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            cleared_count = self.manager.clear_checked_out_bookings()
            self.refresh_table()
            QMessageBox.information(
                self, "Cleared Checked-Out Bookings",
                f"Successfully cleared {cleared_count} checked-out bookings."
            )

    def save_to_txt(self):
        """Save current data to a text file."""
        file_path = self.manager.save_to_txt()
        if file_path:
            QMessageBox.information(self, "Report Generated", 
                                   f"Report saved to:\n{file_path}")
        else:
            QMessageBox.warning(self, "Error", "Failed to generate report.")

    def refresh_table(self):
        """Update the table with all bookings, highlighting current ones."""
        self.table.setRowCount(0)
        
        for booking in self.manager.bookings:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            check_out_time = booking.check_out.strftime("%Y-%m-%d %H:%M:%S") if booking.check_out else "N/A"
            
            items = [
                QTableWidgetItem(str(booking.booking_id)),
                QTableWidgetItem(booking.check_in.strftime("%Y-%m-%d %H:%M:%S")),
                QTableWidgetItem(check_out_time),
                QTableWidgetItem(str(booking.num_guests)),
                QTableWidgetItem(str(booking.room_id)),
                QTableWidgetItem("Yes" if booking.is_paid else "No"),
                QTableWidgetItem(booking.checkout_status())
            ]
            
            for col, item in enumerate(items):
                self.table.setItem(row, col, item)
                
                # Color coding
                if booking.check_out:
                    # Gray for checked-out bookings
                    item.setBackground(QColor(220, 220, 220))
                elif booking.is_paid:
                    # Light green for paid current bookings
                    item.setBackground(QColor(200, 255, 200))
                else:
                    # Light red for unpaid current bookings
                    item.setBackground(QColor(255, 200, 200))
                
                # Highlight emergency checkouts
                if booking.checkout_reason == "Emergency":
                    item.setBackground(QColor(255, 255, 150))  # Yellow for emergency

    def refresh_total_guests(self):
        """Update the total guests label."""
        total = self.manager.get_total_guests()
        self.total_label.setText(f"Total guests currently staying: {total}")

### MaintenanceDialog Class
class MaintenanceDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Mark Room Under Maintenance")
        layout = QFormLayout(self)

        # Room ID input
        self.room_id_spin = QSpinBox(self)
        self.room_id_spin.setMinimum(1)
        self.room_id_spin.setMaximum(50)
        layout.addRow("Room ID:", self.room_id_spin)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.mark_room)
        button_box.rejected.connect(self.reject)

    def mark_room(self):
        """Mark the selected room as under maintenance."""
        room_id = self.room_id_spin.value()
        if room_id not in self.manager.available_rooms:
            QMessageBox.warning(self, "Error","This room is not available for maintenance (may already be booked or in maintenance).")
            return
            
        self.manager.mark_room_under_maintenance(room_id)
        QMessageBox.information(self, "Room Maintenance", f"Room {room_id} is now under maintenance.")
        self.accept()

### RepairedDialog Class
class RepairedDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Mark Room Repaired")
        layout = QFormLayout(self)

        # Room ID input
        self.room_id_spin = QSpinBox(self)
        self.room_id_spin.setMinimum(1)
        self.room_id_spin.setMaximum(50)
        layout.addRow("Room ID:", self.room_id_spin)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.mark_room)
        button_box.rejected.connect(self.reject)

    def mark_room(self):
        """Mark the selected room as repaired."""
        room_id = self.room_id_spin.value()
        if room_id not in self.manager.maintenance_rooms:
            QMessageBox.warning(self, "Error", "This room is not under maintenance.")
            return
            
        self.manager.mark_room_repaired(room_id)
        QMessageBox.information(self, "Room Repaired", f"Room {room_id} is now available.")
        self.accept()

### CheckInDialog Class
class CheckInDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Check In")
        layout = QFormLayout(self)

        # Number of guests input
        self.num_guests_spin = QSpinBox(self)
        self.num_guests_spin.setMinimum(1)
        self.num_guests_spin.setMaximum(10)  # Reasonable limit for a room
        layout.addRow("Number of guests:", self.num_guests_spin)

        # Check-in time input
        self.check_in_datetime_edit = QDateTimeEdit(self)
        self.check_in_datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.check_in_datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        layout.addRow("Check-in time:", self.check_in_datetime_edit)

        # Room ID input
        self.room_id_spin = QSpinBox(self)
        self.room_id_spin.setMinimum(1)
        self.room_id_spin.setMaximum(50)
        layout.addRow("Room ID:", self.room_id_spin)

        # Payment status input
        self.payment_status_combo = QComboBox(self)
        self.payment_status_combo.addItems(["Paid", "Not Paid"])
        layout.addRow("Payment Status:", self.payment_status_combo)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def get_num_guests(self):
        """Return the number of guests entered."""
        return self.num_guests_spin.value()

    def get_check_in_datetime(self):
        """Return the check-in datetime as a Python datetime object."""
        qdt = self.check_in_datetime_edit.dateTime()
        return datetime.fromtimestamp(qdt.toMSecsSinceEpoch() / 1000)

    def get_room_id(self):
        """Return the room ID entered."""
        return self.room_id_spin.value()

    def get_payment_status(self):
        """Return the payment status as a boolean."""
        return self.payment_status_combo.currentText() == "Paid"

### EnhancedCheckOutDialog Class
class EnhancedCheckOutDialog(QDialog):
    def __init__(self, booking_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Check Out")
        layout = QFormLayout(self)

        # Booking selection
        self.booking_combo = QComboBox(self)
        self.booking_combo.addItems(booking_ids)
        layout.addRow("Select booking:", self.booking_combo)

        # Check-out time input
        self.check_out_datetime_edit = QDateTimeEdit(self)
        self.check_out_datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.check_out_datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        layout.addRow("Check-out time:", self.check_out_datetime_edit)

        # Checkout reason
        self.reason_combo = QComboBox(self)
        self.reason_combo.addItems(["Normal", "Emergency"])
        self.reason_combo.currentTextChanged.connect(self.toggle_notes_field)
        layout.addRow("Checkout Reason:", self.reason_combo)

        # Notes field (initially hidden)
        self.notes_edit = QTextEdit(self)
        self.notes_edit.setPlaceholderText("Enter emergency details...")
        self.notes_edit.setMaximumHeight(100)
        self.notes_label = QLabel("Emergency Notes:")
        layout.addRow(self.notes_label, self.notes_edit)
        self.notes_label.hide()
        self.notes_edit.hide()

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.validate)
        button_box.rejected.connect(self.reject)

    def toggle_notes_field(self, reason):
        """Show/hide notes field based on reason selection."""
        if reason == "Emergency":
            self.notes_label.show()
            self.notes_edit.show()
        else:
            self.notes_label.hide()
            self.notes_edit.hide()

    def validate(self):
        """Validate the input before accepting."""
        if self.reason_combo.currentText() == "Emergency" and not self.notes_edit.toPlainText().strip():
            QMessageBox.warning(self, "Missing Information", "Please provide notes for emergency checkout.")
            return
        self.accept()

    def get_selected_booking_id(self):
        return self.booking_combo.currentText()

    def get_check_out_datetime(self):
        qdt = self.check_out_datetime_edit.dateTime()
        return datetime.fromtimestamp(qdt.toMSecsSinceEpoch() / 1000)

    def get_checkout_reason(self):
        return self.reason_combo.currentText()

    def get_checkout_notes(self):
        return self.notes_edit.toPlainText() if self.reason_combo.currentText() == "Emergency" else None

### Main Application Entry Point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set a consistent style for better appearance
    app.setStyle('Fusion')
    
    manager = HotelManager()
    window = MainWindow(manager)
    window.show()
    sys.exit(app.exec_())