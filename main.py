"""Module for monitoring humidity and temperature"""
from json import JSONDecodeError, loads, dumps
from time import sleep
from threading import Thread
from flet import (
    WEB_BROWSER,
    icons,
    NavigationBar,
    NavigationDestination,
    View,
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

def setup_serial(port:str="COM1") -> dict:
    """Returns a serial object with serial and timeout already set"""
    serial_instance = {
        "error": None,
        "new_serial": None
    }
    try:
        new_serial = Serial(port,9600,timeout=DELAY)
        serial_instance.update({"new_serial":new_serial})
    except PortNotOpenError:
        serial_instance.update({"error":"Error al abrir puerto"})
    except SerialTimeoutException:
        serial_instance.update({"error":"Tiempo de espera excedido"})
    except SerialException:
        serial_instance.update({"error":"Error en el puerto serial"})
    return serial_instance


def update_serial_instance(
        old_instance:dict,
        new_instance:dict
        ) -> dict:
    """Updates the old serial object and sets new values from another serial object"""
    old_instance.update({"error":new_instance.get("error")})
    old_instance.update({"new_serial":new_instance.get("new_serial")})
    return old_instance

def setup_threads(func) -> Thread:
    """Returns an initialized thread targeting a function"""
    arduino_thread = Thread(target=func)
    arduino_thread.start()
    return arduino_thread

def join_threads(thread: Thread):
    """Joins a thread"""
    thread.join()

def change_field_status(fields:list, status=True) -> None:
    """Changes the status of a field"""
    map(lambda field: field.disabled == status, fields)

def update_arduino_mlx(
    serial_object:dict,
    data_field: TextField,
    page: Page
):
    """Updates the mlx sensor data with values from the arduino"""
    serial_line: Serial = serial_object.get("new_serial")
    while True:
        if serial_line is None:
            continue
        try:
            serial_data = serial_line.readline().decode("utf-8")
            decoded_data = loads(serial_data)
            print(decoded_data)
            data_field.value = decoded_data
            page.update()
        except JSONDecodeError:
            pass
        sleep(0.5)

def update_arduino_values(
    serial_object:dict,
    humidity_field:TextField,
    temperature_field:TextField,
    page:Page
    ):
    """Updates the humidity and temperature fields with the values from the arduino"""
    serial_line: Serial = serial_object.get("new_serial")
    while True:
        if serial_line is None:
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
        sleep(0.5)

def rgb_component(
        page:Page,
        serial_object:dict
        ):
    """Returns a component with RGB sliders and text fields"""
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
        serial_line: Serial = serial_object.get("new_serial")
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
    rgb_text_fields = [red_text,green_text,blue_text]
    return component, rgb_text_fields

def set_title(page:Page):
    """Sets the title and the alignment of the page"""
    page.title = "Valores de arduino"
    page.vertical_alignment = MainAxisAlignment.CENTER

def change_routes(event,page:Page):
    """Changes the routes of the page"""
    if event.data == 0:
        page.go('/')
    if event.data == 1:
        page.go('/mlx')
    page.update()

def main(page: Page) -> None:
    """This function setup the page and manages the page content"""
    def get_target():
        if page.route == "/":
            return update_arduino_values(
                serial_object=serial_object,
                humidity_field=txt_humidity,
                temperature_field=txt_temperature,
                page=page
                )
        if page.route == "/mlx":
            return update_arduino_mlx(
                serial_object=serial_object,
                data_field=txt_mlx,
                page=page
                )

    nav_bar = NavigationBar(
                            adaptive=True,
                            on_change=lambda e: change_routes(event=e,page=page),
                            destinations=[
                                NavigationDestination(label="Inicio",icon=icons.HOME),
                                NavigationDestination(label="MLX",icon=icons.CABLE)
                            ]
                        )
    serial_object = setup_serial(port="COM1")
    arduino_status = Text("Conecta el arduino y selecciona el puerto serial")
    rgb_controls, rgb_text_fields = rgb_component(page,serial_object)
    def add_error_message(error_message="Algo salió mal"):
        """Adds an error message to the page"""
        arduino_status.value = error_message
        page.update()

    set_title(page=page)
    def activate_mlx(_):
        serial_line: Serial = serial_object.get("new_serial")
        if serial_line is None:
            print("Activating MLX sensor")
            serial_line.write("run MODE-55\r\n".encode("utf-8"))

    txt_humidity = TextField(value="Humedad",read_only=True,disabled=True)
    txt_temperature = TextField(value="Temperatura",read_only=True,disabled=True)
    txt_mlx = TextField(value='MLX',read_only=True,disabled=True)
    activate_mlx_button = FilledButton(text='Activar MLX',on_click=activate_mlx)
    if not serial_object.get("error") is None:
        change_field_status([txt_temperature, txt_humidity], status=False)
        add_error_message(error_message=serial_object.get("error"))

    arduino_thread = setup_threads(func=get_target())

    def change_serial_port(serial_obj:dict,event:ControlEvent):
        """Changes the serial port to the selected one"""
        if not isinstance(event.control.value,str):
            return
        if not "COM" in event.control.value:
            return
        if not serial_obj.get('new_serial') is None:
            if serial_obj.get('new_serial').port == event.control.value:
                return
        new_instance = update_serial_instance(
            old_instance=serial_obj,
            new_instance=setup_serial(event.control.value)
            )
        if not new_instance.get("error") is None:
            change_field_status([txt_temperature, txt_humidity, txt_mlx], status=False)
            add_error_message(error_message=new_instance.get("error"))
        else:
            change_field_status([txt_temperature,txt_humidity, txt_mlx], status=True)
            add_error_message(error_message="Conectado al arduino")
            join_threads(thread=arduino_thread)
            setup_threads(func=get_target())
        print(f"Serial port changed to {event.control.value}")

    general_arduino_controls = [
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
    ]

    def route_change(route):
        print(f"Route changed to {route}")
        page.views.clear()
        page.views.append(
            View(
                '/',
                [
                    *general_arduino_controls,
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
                ],
                navigation_bar=nav_bar
            )
        )
        if page.route == "/mlx":
            page.views.append(
                View(
                    "/mlx",
                    [
                        *general_arduino_controls,
                        Row(
                            [
                                txt_mlx
                            ],
                            alignment=MainAxisAlignment.CENTER,
                        ),
                        Row(
                            [
                                activate_mlx_button,
                            ],
                            alignment=MainAxisAlignment.CENTER,
                        )
                    ],
                    navigation_bar=nav_bar
                )
            )
        page.update()

    def view_pop(view):
        print(f"View popped {view.route}")
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.navigation_bar = nav_bar
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go('/mlx')

app(target=main,view=WEB_BROWSER)
