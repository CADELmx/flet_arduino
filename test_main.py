"""test for the arduino-flet application"""
from time import sleep
from flet import app, Page
from main import SetupThread, SetupSerial, MainPage

def test_main():
    """Test the main function"""
    print("Testing main function")
    def main(page: Page):
        serial = SetupSerial(port='COM1', baudrate=9600, timeout=5.0)
        thread = SetupThread(target=lambda: print("Thread started"))
        MainPage(page=page, serial=serial, thread=thread)
        page.window_close()
        sleep(1)
        thread.join()
        serial.close()
    app(target=main)

test_main()
