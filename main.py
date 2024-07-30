"""Module for monitoring humidity and temperature"""
from json import JSONDecodeError, dumps
from time import sleep
from os import environ
from threading import Thread
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from flet import (
    LineChart,
    LineChartData,
    LineChartDataPoint,
    ChartAxis,
    ChartAxisLabel,
    icons,
    NavigationBar,
    NavigationDestination,
    View,
    Text,
    TextField,
    Image,
    Dropdown,
    Row,
    Column,
    Page,
    app,
    MainAxisAlignment,
    CrossAxisAlignment,
    CupertinoSlider,
    FilledButton,
    dropdown,
    ControlEvent,
    RouteChangeEvent
)
from serial import SerialTimeoutException, SerialException, PortNotOpenError, Serial

DELAY = 5.0

class SetupSerial():
    """Creates a serial connection with the specified parameters."""
    error = False
    instance = None
    def __init__(self, port, baudrate, timeout):
        self.setup(port, baudrate, timeout)
    def setup(self, port='COM1', baudrate=9600, timeout=DELAY):
        """Sets the serial connection with the specified parameters."""
        print(f"Setting up serial connection with port {port}")
        try:
            self.instance = Serial(
                port,
                baudrate,
                timeout
                )
            print(f"Serial connection with port {port} established")
        except PortNotOpenError:
            self.error = "Error al abrir puerto"
        except SerialTimeoutException:
            self.error = "Tiempo de espera excedido"
        except SerialException:
            self.error = "Error en el puerto serial"
        return self
    def change_port(self, port):
        """Changes the serial port."""
        if (not self.error) and self.instance.port == port:
            return self
        self.close()
        self.setup(port=port)
        return self
    def read(self):
        """Reads the serial port."""
        if not self.error:
            try:
                print(self.instance.readline().decode("utf-8"))
                return self.instance.readline()
            except UnicodeDecodeError:
                return "Error al decodificar datos"
        return "Error al leer datos"
    def write(self, text:str):
        """Writes to the serial port."""
        if not self.error:
            self.instance.write(text.encode("utf-8"))
        return self
    def close(self):
        """Closes the serial port."""
        print("Closing serial connection")
        if not self.error:
            self.instance.close()

class SetupThread():
    """Creates a thread with the specified target function."""
    error = None
    instance = None
    def __init__(self, target: callable):
        self.setup(target)
    def setup(self, target: callable):
        """Sets the target function for the thread."""
        print(f"Setting up thread with target {target}")
        self.instance = Thread(target=target)
        self.start()
        return self

    def update(self, target: callable):
        """Updates the target function for the thread."""
        print(f"Updating thread with target {target}")
        self.join()
        self.instance = Thread(target=target)
        self.start()
        return self
    def start(self):
        """Starts the thread."""
        self.instance.start()
        return self
    def join(self):
        """Joins the thread."""
        print("stopping thread")
        self.instance.join(timeout=0.1)
        return self

class SetupDatabase():
    """Creates a mongo database connection."""
    error = None
    client = None
    connection_string = environ.get('MONGODB_URI')
    def __init__(self):
        self.setup()

    def setup(self):
        """Sets up the database connection."""
        try:
            print("Setting up database connection")
            self.client = MongoClient(self.connection_string)
            print("Database connection established")
            self.db = self.client.get_database("flet_database")
            self.collection = self.db.get_collection("data")
        except ConnectionFailure:
            self.error = "Error al establecer conexión"
            return self
        return self

    def insert(self, data: dict):
        """Inserts data into the database."""
        if not self.error:
            self.collection.insert_one(data)
        return self

class RgbComponent():
    """Component for controlling an RGB LED."""
    component = None
    red_text = Text("000",color="red")
    green_text = Text("000",color="green")
    blue_text = Text("000",color="blue")
    min=0
    max=255
    def __init__(self, page: Page, serial: SetupSerial):
        self.page = page
        self.ser = serial

    def strzfill(self, value):
        """Returns a string with the value filled with zeros."""
        return str(int(value)).zfill(3)

    def change_red_value(self, event: ControlEvent):
        """Updates the red text value when the red slider is changed."""
        self.red_text.value = self.strzfill(event.control.value)
        self.page.update()

    def change_green_value(self, event: ControlEvent):
        """Updates the green text value when the green slider is changed."""
        self.green_text.value = self.strzfill(event.control.value)
        self.page.update()

    def change_blue_value(self, event: ControlEvent):
        """Updates the blue text value when the blue slider is changed."""
        self.blue_text.value = self.strzfill(event.control.value)
        self.page.update()

    def change_color(self):
        """Sends the color to the serial port."""
        json_data = dumps({
            "red": self.red_text.value,
            "green": self.green_text.value,
            "blue": self.blue_text.value
        })
        self.ser.write(json_data)

    def build(self):
        """Builds the controls for the RGB component."""
        print("Building RGB component")
        self.component = Column(
            [
                CupertinoSlider(
                    min=self.min,
                    max=self.max,
                    divisions=self.max,
                    value=0,
                    active_color="red",
                    thumb_color="red",
                    on_change=self.change_red_value,
                ),
                CupertinoSlider(
                    min=self.min,
                    max=self.max,
                    divisions=self.max,
                    value=0,
                    active_color="green",
                    thumb_color="green",
                    on_change=self.change_green_value,
                ),
                CupertinoSlider(
                    min=self.min,
                    max=self.max,
                    divisions=self.max,
                    value=0,
                    active_color="blue",
                    thumb_color="blue",
                    on_change=self.change_blue_value,
                ),
                Row([
                    self.red_text,
                    self.green_text,
                    self.blue_text,
                ]),
                FilledButton(
                    text="Enviar color",
                    icon="send",
                    icon_color="white",
                    on_click=self.change_color(),
                )
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            alignment=MainAxisAlignment.CENTER,
        )
        return self.component

class MLXChart():
    """Chart for the MLX sensor."""
    data_line_1 = LineChartData(
        stroke_width=2,
        color="red",
        stroke_cap_round=True,
    )
    def __init__(self) -> None:
        pass

    def add_point(self, x,y):
        """Adds a point to the chart."""
        self.data_line_1.data_points.append(LineChartDataPoint(x=x, y=y))
        return self

    def build(self):
        """Builds the chart."""
        return LineChart(
            data=[self.data_line_1],
            left_axis=ChartAxis(
                title="Tiempo",
            ),
            bottom_axis=ChartAxis(
                labels=[
                    ChartAxisLabel(
                        value=0,
                        label="Tiempo",
                    )
                ],
                labels_interval=10,
            ),
            width=300,
            height=200,
        )

class MainPage():
    """Main page for the application."""
    component = None
    thread = None
    routes = {'/', '/mlx'}
    arduino_status = Text("Arduino desconectado",color="red")
    database_status = Text("Base de datos desconectada",color="red")
    port_selector = Dropdown(
        width=200,
        options=[
            dropdown.Option("COM1", "COM1"),
            dropdown.Option("COM2", "COM2"),
            dropdown.Option("COM3", "COM3"),
            dropdown.Option("COM4", "COM4"),
            ],
        label="Puerto serial"
    )
    nav_bar = NavigationBar(
        adaptive=True,
    )
    mlx_activator = FilledButton(
        text="Activar MLX",
        icon="power",
        icon_color="white",
    )
    mlx_field = TextField(value='MLX',read_only=True,disabled=True, min_lines=2)
    max_field = TextField(value='MAX',read_only=True,disabled=True, min_lines=2)
    temp_field = TextField(value='Humedad y temperatura',read_only=True,disabled=True, min_lines=2)

    max_img = Image('./img/max_oxygen.jpeg', width=50, height=50)
    mlx_img = Image('./img/mlx_temp.jpeg', width=50, height=50)

    def __init__(
            self, page: Page,
            serial: SetupSerial,
            thread: SetupThread,
            database: SetupDatabase
            ):
        self.serial = serial
        self.page = page
        self.thread = thread
        self.database = database
        self.port_selector.on_change = self.change_port
        self.nav_bar.on_change = self.change_route
        self.page.on_route_change = self.route_change
        self.mlx_activator.on_click = lambda _: self.activate_mlx()
        self.update_database_status()

    def update_from_serial(self, primary_field: TextField, secondary_field: TextField = None):
        """Updates the text from the serial port."""
        print("Updating from serial")
        while True:
            try:
                line = self.serial.read()
                if primary_field and str(line)[1]:
                    primary_field.value = ord(str(line)[1])
                    print(f"Updating text field with {ord(str(line)[1])}")
                    self.database.collection.insert_one({"max_medida": ord(str(line)[1])})
                if secondary_field and str(line)[3]:
                    secondary_field.value = ord(str(line)[3])
                    self.database.collection.insert_one({"mlx_medida": ord(str(line)[3])})
                    print(f"Updating text field with {ord(str(line)[1])}")
                self.page.update()
            except JSONDecodeError:
                pass
            sleep(0.5)

    def activate_mlx(self):
        """Activates the MLX sensor."""
        self.serial.write(text="MLX")

    def update_arduino_status(self):
        """Updates the arduino status."""
        if self.serial.error:
            self.arduino_status.value = self.serial.error
            self.arduino_status.color = "red"
        else:
            self.arduino_status.value = "Arduino conectado"
            self.arduino_status.color = "green"
        self.page.update()

    def update_database_status(self):
        """Updates the database status."""
        if self.database.error:
            self.database_status.value = self.database.error
            self.database_status.color = "red"
        else:
            self.database_status.value = "Base de datos conectada"
            self.database_status.color = "green"
        self.page.update()

    def fields_status(self, fields: list, status: bool = True):
        """Updates the field status."""
        map(lambda field: field.disabled == status, fields)
        self.page.update()

    def change_port(self, event: ControlEvent):
        """Changes the serial port."""
        self.fields_status([self.temp_field, self.mlx_field], self.serial.error)
        self.serial.change_port(event.control.value)
        self.update_arduino_status()

    def change_route(self, event: ControlEvent):
        """Changes the routes in the application."""
        control: NavigationBar = event.control
        destination = control.destinations[int(event.data)].data
        self.page.go(destination)

    def route_change(self, route_event: RouteChangeEvent):
        """Changes the route in the application."""
        print(f"Route changed to {route_event.route}")
        self.page.views.clear()
        if route_event.route == '/':
            self.thread.update(target=lambda: self.update_from_serial(self.temp_field))
            self.page.views.append(self.create_view(
                '/',
                fields=[
                    self.temp_field,
                    RgbComponent(self.page, self.serial).build(),
                ]
            ))
        if route_event.route == '/mlx':
            self.thread.update(
                target=lambda: self.update_from_serial(self.mlx_field, self.max_field)
                )
            self.page.views.append(self.create_view(
                '/mlx',
                fields=[
                    Row([self.mlx_img, self.mlx_field]),
                    Row([self.max_img, self.max_field]),
                    self.mlx_activator
                ]
            ))
        self.page.update()

    def create_view(self, route: str, fields: dict):
        """Creates the view for the main page."""
        print(f"Creating view for route {route}")
        if not route in self.routes:
            self.routes.add(route)
        self.nav_bar.destinations = [
            NavigationDestination(
                data=r,
                label=f"Ir a {r}",
                icon=icons.ROUTE
                ) for r in sorted(self.routes)
            ]
        return View(
            route,
            [
                Row(
                    [
                        Column(
                            [
                            self.arduino_status,
                            self.port_selector,
                            self.database_status
                            ],
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        )
                    ],
                    alignment=MainAxisAlignment.CENTER,
                ),
                Row(
                    [
                        Column(
                            fields,
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                        )
                    ],
                    alignment=MainAxisAlignment.CENTER,
                )
            ],
            navigation_bar=self.nav_bar
        )

def main(page: Page):
    """Main function for the application."""
    serial = SetupSerial(port='COM4', baudrate=9600, timeout=DELAY)
    thread = SetupThread(target=lambda: print("Thread started"))
    client = SetupDatabase()
    MainPage(page=page, serial=serial, thread=thread, database=client)
    page.go(page.route)
    def close():
        serial.close()
        thread.join()
    page.on_disconnect=close

if __name__ == "__main__":
    app(target=main)
