"""Module for monitoring humidity and temperature"""
import json
import time
from threading import Thread
import serial
import flet as ft
from serial import SerialTimeoutException, SerialException, PortNotOpenError

DELAY = 5.0

def setup_serial(port="COM1"):
    """Returns a serial object with serial and timeout already set"""
    new_serial = None
    try:
        new_serial = serial.Serial(port,9600,timeout=DELAY)
        return {
            "error": None,
            "new_serial": new_serial
        }
    except PortNotOpenError as error:
        print(error.errno)
        return {
            "error": "No se pudo abrir el puerto serial",
            "new_serial": new_serial 
        }
    except SerialTimeoutException as error:
        print(error.errno)
        return {
            "error": "Tiempo de espera excedido",
            "new_serial": new_serial
        }
    except SerialException as error:
        print(error.errno)
        return {
            "error": "Error en el puerto serial",
            "new_serial": new_serial
        }


def setup_threads(func):
    """Returns an initialized thread targeting a function"""
    arduino_thread = Thread(target=func)
    arduino_thread.start()
    return arduino_thread


def main(page: ft.Page,is_testing=False):
    """This function setup the page and manages the page content"""
    disabled_fields = True
    serial_port = "COM1"
    serial_object = setup_serial()
    print(serial_object)
    arduino_status = ft.Text("Conecta el arduino y selecciona el puerto serial")

    page.add(
        ft.Row(
            [
                arduino_status
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

    def add_error_message(error_message="Algo salió mal"):
        """Adds an error message to the page"""
        arduino_status.value = error_message
        page.update()

    if serial_object["error"] is not None:
        disabled_fields = True
        add_error_message(error_message=serial_object["error"])
    page.title = "Valores de arduino"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_humidity = ft.TextField(value="Humedad",read_only=True,disabled=disabled_fields)
    txt_temperature = ft.TextField(value="Temperatura",read_only=True,disabled=disabled_fields)

    def update_arduino_values():
        serial_line = serial_object["new_serial"]
        while True:
            if serial_object["error"] is not None:
                continue
            try:
                serial_data = serial_line.readline().decode("utf-8")
                decoded_data = json.loads(serial_data)
                txt_humidity.value = decoded_data["temperatura"]
                txt_temperature.value = decoded_data["humedad"]
                page.update()
            except json.JSONDecodeError:
                pass
            time.sleep(DELAY)

    def change_serial_port(event):
        """Changes the serial port to the selected one"""
        print(event)
        serial_port = selector.value
        serial_object = setup_serial()
        if serial_object["error"] is not None:
            add_error_message(error_message=serial_object["error"])
        print(serial_port)

    selector = ft.Dropdown(
        width=200,
        options=[
            ft.dropdown.Option("COM1", "COM1"),
            ft.dropdown.Option("COM2", "COM2"),
            ft.dropdown.Option("COM3", "COM3"),
            ft.dropdown.Option("COM4", "COM4"),
        ],
        value=serial_port,
        label="Puerto serial",
        on_change=change_serial_port
    )

    page.add(
        ft.Row(
            [
                selector
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        ft.Row(
            [
                txt_humidity,
                txt_temperature
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )
    thread = setup_threads(func=update_arduino_values)

    def close_window():
        """Closes the serial port and finishes the thread"""
        if serial_object["new_serial"] is not None:
            serial_object["new_serial"].close()
        thread.join()

    page.on_close=close_window

ft.app(main)