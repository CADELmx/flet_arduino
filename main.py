import flet as ft
import json
import serial
from threading import Thread
import time

DELAY = 5.0
SERIAL_PORT = "COM3"

def setup_serial():
    return serial.Serial(SERIAL_PORT,9600,timeout=DELAY)

def setup_threads(func):
    arduino_thread = Thread(target=func)
    arduino_thread.start()
    return arduino_thread
    
def main(page: ft.Page):
    serial = setup_serial()
    page.title = "Valores de arduino"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)
    txt_humedad = ft.TextField(value="Humedad")
    txt_temperatura = ft.TextField(value="",label="Temperatura")

    def update_arduino_values():
        while True:
            try:  
                serial_data = serial.readline().decode("utf-8")
                decoded_data = json.loads(serial_data)
                txt_humedad.value = decoded_data["temperatura"]
                txt_temperatura.value = decoded_data["humedad"]
            except json.JSONDecodeError:
                txt_humedad.value = txt_temperatura.value = ""
            time.sleep(DELAY)

    def minus_click(e):
        txt_number.value = str(int(txt_number.value) - 1)
        page.update()

    def plus_click(e):
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
        )
    )
    
    setup_threads(func=update_arduino_values)
    


ft.app(main)
