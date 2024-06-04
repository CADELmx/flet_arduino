"""Module for monitoring humidity and temperature"""
from json import JSONDecodeError, loads
from time import sleep
from threading import Thread
import serial
import flet as ft
from serial import SerialTimeoutException, SerialException, PortNotOpenError

DELAY = 5.0

def setup_serial(port="COM1"):
    """Returns a serial object with serial and timeout already set"""
    serial_ = {
        "error": None,
        "new_serial": None
    }
    try:
        serial_["new_serial"] = serial.Serial(port,9600,timeout=DELAY)
        return serial_
    except PortNotOpenError:
        serial_["error"] = "Puerto serial no disponible"
        return serial_
    except SerialTimeoutException:
        serial_["error"] = "Tiempo de espera excedido"
        return serial_
    except SerialException:
        serial_["error"] = "Error en el puerto serial: "
        return serial_


def setup_threads(func):
    """Returns an initialized thread targeting a function"""
    arduino_thread = Thread(target=func)
    arduino_thread.start()
    return arduino_thread


def main(page: ft.Page):
    """This function setup the page and manages the page content"""
    disabled_fields = True
    serial_port = "COM3"
    serial_object = setup_serial(port=serial_port)
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
                decoded_data = loads(serial_data)
                print(decoded_data)
                txt_humidity.value = decoded_data["temperatura"]
                txt_temperature.value = decoded_data["humedad"]
                page.update()
            except JSONDecodeError:
                pass
            sleep(DELAY)

    def change_serial_port(serial_obj):
        """Changes the serial port to the selected one"""
        serial_port = selector.value
        serial_obj = setup_serial(serial_port)
        if serial_obj["error"] is not None:
            add_error_message(error_message=serial_obj["error"])
        print(f"Serial port changed to {serial_port}")

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
        on_change=lambda e: change_serial_port(serial_object)
    )

    red_text = ft.Text("0",color="red")
    green_text = ft.Text("0",color="green")
    blue_text = ft.Text("0",color="blue")

    def change_red_value(e):
        print(e.control.value)
        red_text.value = str(int(e.control.value)).zfill(3)
        page.update()

    def change_green_value(e):
        print(e.control.value)
        green_text.value = str(int(e.control.value)).zfill(3)
        page.update()

    def change_blue_value(e):
        print(e.control.value)
        blue_text.value = str(int(e.control.value)).zfill(3)
        page.update()

    red_slider = ft.CupertinoSlider(
        on_change=change_red_value,
        value=0,
        divisions=255,
        min=0,
        max=255,
        active_color="red",
        thumb_color="red",
    )

    blue_slider = ft.CupertinoSlider(
        on_change=change_blue_value,
        value=0,
        divisions=255,
        min=0,
        max=255,
        active_color="blue",
        thumb_color="blue",
    )

    green_slider = ft.CupertinoSlider(
        on_change=change_green_value,
        value=0,
        divisions=255,
        min=0,
        max=255,
        active_color="green",
        thumb_color="green",
    )

    def change_color():
        """Changes the color of the LED"""
        serial_line = serial_object["new_serial"]
        print(f"{red_text.value}{green_text.value}{blue_text.value}")
        if serial_line is not None:
            line_text = f"{red_text.value}{green_text.value}{blue_text.value}"
            serial_line.write(line_text.encode("utf-8"))

    send_color_button = ft.FilledButton(
        text='Enviar color',
        icon="send",
        icon_color="white",
        on_click=lambda e: change_color()
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
        ),
        ft.Row(
            [
                red_text,
                green_text,
                blue_text
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        ft.Row(
            [
                ft.Column(
                    [
                        red_slider,
                        green_slider,
                        blue_slider,
                        send_color_button
                    ],
                ),
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
