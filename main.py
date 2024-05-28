"""Module for monitoring humidity and temperature"""
import json
import time
from threading import Thread
import serial
import flet as ft

DELAY = 5.0
SERIAL_PORT = "COM3"

"""Returns a serial object with serial and timeout already set"""
def setup_serial():
    new_serial = None
    try:
        new_serial = serial.Serial(SERIAL_PORT,9600,timeout=DELAY)
        return {
            "error": None,
            "new_serial": new_serial
        }
    except Exception as error:
        print(error)
        return {
            "error": "No se puede inicializar el serial",
            "new_serial": new_serial 
        }


"""Returns an initialized thread targeting a function"""
def setup_threads(func):
    arduino_thread = Thread(target=func)
    arduino_thread.start()
    return arduino_thread


"""This function setup the page and manages the page content"""
def main(page: ft.Page):
    serialobj = setup_serial()
    if serialobj["error"]:
        page.add(
            ft.Row(
                [
                    ft.Text("Para ver los valores conecta el arduino")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )
    page.title = "Valores de arduino"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)
    txt_humedad = ft.TextField(value="Humedad")
    txt_temperatura = ft.TextField(value="Temperatura")

    def update_arduino_values():
        serialcom = serialobj["serial"]
        while True:
            if serialobj["error"]:
                continue
            try:
                serial_data = serialcom.readline().decode("utf-8")
                decoded_data = json.loads(serial_data)
                txt_humedad.value = decoded_data["temperatura"]
                txt_temperatura.value = decoded_data["humedad"]
                page.update()
            except json.JSONDecodeError:
                pass
            time.sleep(DELAY)

    def minus_click(e):
        print(e)
        txt_number.value = str(int(txt_number.value) - 1)
        page.update()

    def plus_click(e):
        print(e)
        txt_number.value = str(int(txt_number.value) + 1)
        page.update()

    page.add(
        ft.Row(
            [
                ft.IconButton(ft.icons.REMOVE, on_click=minus_click),
                txt_number,
                ft.IconButton(ft.icons.ADD, on_click=plus_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        ft.Row(
            [
                txt_humedad,
                txt_temperatura
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )
    setup_threads(func=update_arduino_values)


ft.app(main)
