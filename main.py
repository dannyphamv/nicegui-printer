import io
import base64
import json
import os
from datetime import datetime
from io import BytesIO
from typing import List, Optional

# Barcode & Image Libraries
import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image, ImageWin

# UI Library
from nicegui import ui, native, app

# Windows Printing
import win32print
import win32ui
import win32con

app.native.window_args["text_select"] = True

# --- File Constants ---
SETTINGS_FILE = "settings.json"
HISTORY_FILE = "history.json"


class StorageService:
    """Handles saving and loading application data to JSON."""

    @staticmethod
    def load_settings() -> dict:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    pass
        return {"printer": None, "dark_mode": True}

    @staticmethod
    def save_settings(printer: str, dark_mode: bool):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"printer": printer, "dark_mode": dark_mode}, f)

    @staticmethod
    def add_to_history(value: str):
        history = StorageService.get_history_raw()
        history.append(
            {
                "text": value,
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            }
        )
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)

    @staticmethod
    def get_history_raw() -> List[dict]:
        """Loads all entries from the history file in chronological order."""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    @staticmethod
    def get_history_sorted() -> List[dict]:
        """Returns history with the newest entries first."""
        return list(reversed(StorageService.get_history_raw()))


class BarcodeService:
    """Handles the generation of barcode and QR code images."""

    @staticmethod
    def generate(value: str, mode: str) -> bytes:
        buffer = io.BytesIO()
        if mode == "Barcode":
            code_class = barcode.get_barcode_class("code128")
            code = code_class(value, writer=ImageWriter())
            code.write(buffer)
        else:
            qr = qrcode.QRCode(version=None, box_size=20)
            qr.add_data(value)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            img.save(buffer, format="PNG")
        return buffer.getvalue()


class PrinterService:
    """Handles interaction with Windows printing hardware."""

    @staticmethod
    def get_printers() -> List[str]:
        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        return [p[2] for p in printers]

    @staticmethod
    def print_image(png_bytes: bytes, printer_name: str):
        img = Image.open(BytesIO(png_bytes))
        img_width, img_height = img.size
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        printable_w = hDC.GetDeviceCaps(win32con.HORZRES)
        printable_h = hDC.GetDeviceCaps(win32con.VERTRES)
        scale = min(printable_w / img_width, printable_h / img_height) * 0.95
        nw, nh = int(img_width * scale), int(img_height * scale)
        left, top = (printable_w - nw) // 2, (printable_h - nh) // 2
        hDC.StartDoc("NiceGUI Print Job")
        hDC.StartPage()
        dib = ImageWin.Dib(img)
        dib.draw(hDC.GetHandleOutput(), (left, top, left + nw, top + nh))
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()


class BarcodeApp:
    def __init__(self):
        self.settings = StorageService.load_settings()
        self.current_bytes: Optional[bytes] = None
        self.printers = PrinterService.get_printers()

        # Determine default printer (Saved vs System Default)
        self.default_printer = (
            self.settings.get("printer") or win32print.GetDefaultPrinter()
        )

        self.setup_ui()

    def handle_generation(self):
        val = self.barcode_input.value.strip()

        # If input is empty, hide the preview and stop
        if not val:
            self.preview.set_visibility(False)
            self.current_bytes = None
            return

        try:
            self.current_bytes = BarcodeService.generate(val, self.toggle.value)
            encoded = base64.b64encode(self.current_bytes).decode("utf-8")
            self.preview.set_source(f"data:image/png;base64,{encoded}")
            self.preview.set_visibility(True)
        except Exception as e:
            ui.notify(f"Generation Error: {e}", type="negative")

    def handle_print(self):
        val = self.barcode_input.value.strip()
        if not self.current_bytes:
            ui.notify("No barcode to print", type="warning")
            return
        try:
            PrinterService.print_image(self.current_bytes, self.printer_select.value)

            # Save to History and refresh table (Newest on Top)
            StorageService.add_to_history(val)
            self.history_table.rows = StorageService.get_history_sorted()
            self.history_table.update()

            ui.notify(f"Printed to {self.printer_select.value}")

            # Reset Input
            self.barcode_input.value = ""
            self.preview.set_visibility(False)
            self.current_bytes = None
            self.barcode_input.run_method("focus")
        except Exception as e:
            ui.notify(f"Print Error: {e}", type="negative")

    def save_app_settings(self):
        """Triggered when printer or theme changes. Check ensures UI is ready."""
        if hasattr(self, "printer_select"):
            StorageService.save_settings(self.printer_select.value, self.dark.value)

    def setup_ui(self):
        # Apply Saved Dark Mode
        self.dark = ui.dark_mode()
        self.dark.set_value(self.settings.get("dark_mode", True))

        with ui.column().classes("w-full items-center"):
            # Header
            with ui.row().classes("w-full items-center"):
                ui.element("div").classes("flex-1")
                ui.label("QR & Barcode Printer").classes(
                    "text-2xl text-center font-bold"
                )
                with ui.row().classes("flex-1 justify-end"):
                    ui.switch(
                        "Dark Mode",
                        on_change=lambda e: (
                            self.dark.set_value(e.value),
                            self.save_app_settings(),
                        ),
                    ).bind_value(self.dark, "value")

            # Controls
            self.toggle = ui.toggle(
                ["Barcode", "QR Code"],
                value="Barcode",
                on_change=self.handle_generation,
            )

            self.printer_select = ui.select(
                self.printers,
                label="Select Printer",
                value=self.default_printer,
                on_change=self.save_app_settings,
            ).classes("w-3/4")

            self.barcode_input = ui.input(
                label="Enter or Scan Barcode",
                on_change=self.handle_generation,
            ).classes("w-3/4")
            self.barcode_input.on("keydown.enter", self.handle_print)

            # Preview & Print Button
            self.preview = ui.image("").props("fit=contain").classes("w-3/4 max-h-46")
            self.preview.set_visibility(False)

            ui.button("Print Label", icon="print", on_click=self.handle_print).classes(
                "w-3/4 text-lg"
            ).bind_visibility_from(self.preview, "visible")

            # --- History Table ---
            ui.label("Print History").classes("text-xl font-semibold mt-10")
            columns = [
                {
                    "name": "text",
                    "label": "Barcode",
                    "field": "text",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "timestamp",
                    "label": "Time Printed",
                    "field": "timestamp",
                    "align": "right",
                    "sortable": True,
                },
            ]
            self.history_table = ui.table(
                columns=columns,
                rows=StorageService.get_history_sorted(),
                row_key="timestamp",
                pagination=5,
            ).classes("w-3/4")


def root():
    BarcodeApp()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        root,
        native=True,
        reload=False,
        title="QR & Barcode Printer",
        port=native.find_open_port(),
    )
