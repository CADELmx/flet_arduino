"""Module for monitoring humidity and temperature"""
from json import JSONDecodeError, loads, dumps
from time import sleep
from threading import Thread
from flet import (
    Text,
    TextField,
    Dropdown,
    Row,
    Column,
    Page,
    app,
    MainAxisAlignment,
    CupertinoSlider,
    FilledButton,
    dropdown,
    ControlEvent,
)
from serial import SerialTimeoutException, SerialException, PortNotOpenError, Serial

DELAY = 5.0

def setup_serial(port:str="COM1") -> dict[str | None,Serial | None]:
    """Returns a serial object with serial and timeout already set"""
    serial_instance = {
        "error": None,
        "new_serial": None
    }
    try:
        serial_instance["new_serial"] = Serial(port,9600,timeout=DELAY)
        return serial_instance
    except PortNotOpenError:
        serial_instance["error"] = "Puerto serial no disponible"
        return serial_instance
    except SerialTimeoutException:
        serial_instance["error"] = "Tiempo de espera excedido"
        return serial_instance
    except SerialException:
        serial_instance["error"] = "Error en el puerto serial"
        return serial_instance

def setup_threads(func) -> Thread:
    """Returns an initialized thread targeting a function"""
    arduino_thread = Thread(target=func)
    arduino_thread.start()
    return arduino_thread

def change_field_status(fields:list[TextField], status=True) -> None:
    """Changes the status of a field"""
    map(lambda field: field.disabled == status, fields)

def update_arduino_values(
    serial_object:dict,
    humidity_field:TextField,
    temperature_field:TextField,
    page:Page
):
    """Updates the humidity and temperature fields with the values from the arduino"""
    serial_line = serial_object["new_serial"]
    while True:
        if serial_object["error"] is not None:
            continue
        try:
            serial_data = serial_line.readline().decode("utf-8")
            decoded_data = loads(serial_data)
            print(decoded_data)
            humidity_field.value = decoded_data["temperatura"]
            temperature_field.value = decoded_data["humedad"]
            page.update()
        except JSONDecodeError:
            pass
        sleep(2.0)


def rgb_component(page:Page,serial_object:dict[str | None,Serial | None]) -> tuple[Column,list[Text]]:
    red_text = Text("0",color="red")
    green_text = Text("0",color="green")
    blue_text = Text("0",color="blue")

    def change_red_value(event:ControlEvent):
        print(event.control.value)
        red_text.value = str(int(event.control.value)).zfill(3)
        page.update()

    def change_green_value(event:ControlEvent):
        print(event.control.value)
        green_text.value = str(int(event.control.value)).zfill(3)
        page.update()

    def change_blue_value(event:ControlEvent):
        print(event.control.value)
        blue_text.value = str(int(event.control.value)).zfill(3)
        page.update()

    def change_color():
        """Changes the color of the LED"""
        serial_line = serial_object["new_serial"]
        json_data = dumps({
            "red":red_text.value,
            "green":green_text.value,
            "blue":blue_text.value
        })
        if not serial_line is None:
            serial_line.write(json_data.encode("utf-8"))

    component = Column(
        [
            CupertinoSlider(
                on_change=change_red_value,
                value=0,
                divisions=255,
                min=0,
                max=255,
                active_color="red",
                thumb_color="red",
            ),
            CupertinoSlider(
                on_change=change_green_value,
                value=0,
                divisions=255,
                min=0,
                max=255,
                active_color="green",
                thumb_color="green",
            ),
            CupertinoSlider(
                on_change=change_blue_value,
                value=0,
                divisions=255,
                min=0,
                max=255,
                active_color="blue",
                thumb_color="blue",
            ),
            FilledButton(
                text='Enviar color',
                icon="send",
                icon_color="white",
                on_click=lambda e: change_color()
            )
        ],
    )
    rgb_textFields = [red_text,green_text,blue_text]
    return component, rgb_textFields

def main(page: Page) -> None:
    """This function setup the page and manages the page content"""
    serial_object = setup_serial(port="COM3")
    arduino_status = Text("Conecta el arduino y selecciona el puerto serial")
    rgb_controls, rgb_text_fields = rgb_component(page,serial_object)
    def add_error_message(error_message="Algo salió mal"):
        """Adds an error message to the page"""
        arduino_status.value = error_message
        page.update()

    page.title = "Valores de arduino"
    page.vertical_alignment = MainAxisAlignment.CENTER

    txt_humidity = TextField(value="Humedad",read_only=True,disabled=True)
    txt_temperature = TextField(value="Temperatura",read_only=True,disabled=True)

    if not serial_object["error"] is None:
        change_field_status([txt_temperature, txt_humidity], status=False)
        add_error_message(error_message=serial_object["error"])

    def change_serial_port(serial_obj:dict,event:ControlEvent):
        """Changes the serial port to the selected one"""
        serial_obj = setup_serial(event.control.value)
        if not serial_obj["error"] is None:
            add_error_message(error_message=serial_obj["error"])
            change_field_status([txt_temperature, txt_humidity], status=False)
        print(f"Serial port changed to {event.control.value}")

    page.add(
        Row(
            [
                arduino_status
            ],
            alignment=MainAxisAlignment.CENTER,
        ),
        Row(
            [
                Dropdown(
                    width=200,
                    options=[
                        dropdown.Option("COM1", "COM1"),
                        dropdown.Option("COM2", "COM2"),
                        dropdown.Option("COM3", "COM3"),
                        dropdown.Option("COM4", "COM4"),
                    ],
                    label="Puerto serial",
                    on_change=lambda e:
                        change_serial_port(serial_obj=serial_object,event=e)
                )
            ],
            alignment=MainAxisAlignment.CENTER,
        ),
        Row(
            [
                txt_humidity,
                txt_temperature
            ],
            alignment=MainAxisAlignment.CENTER,
        ),
        Row(
            rgb_text_fields,
            alignment=MainAxisAlignment.CENTER,
        ),
        Row(
            [
                rgb_controls
            ],
            alignment=MainAxisAlignment.CENTER,
        )
    )
    setup_threads(
        func=lambda:
            update_arduino_values(serial_object,txt_humidity,txt_temperature,page)
        )

app(main)
