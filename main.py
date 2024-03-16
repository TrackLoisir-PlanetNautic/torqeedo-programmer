import asyncio
import aiotkinter
from Frames.login_form import init_login_frame
from ttkthemes import ThemedTk

async def close_program(loop):
    loop.stop()

if __name__ == "__main__":
    asyncio.set_event_loop_policy(aiotkinter.TkinterEventLoopPolicy())

    # Create a new event loop and set it as the current event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    root_window = ThemedTk(theme="arc")
    root_window.geometry("1200x800")
    root_window.title("Trackloisirs")

    # Initialize the login frame
    init_login_frame(root_window)

    # Define a function to stop the event loop and close the window
    def on_close():
        asyncio.create_task(close_program(loop))
        root_window.destroy()

    # Bind the window close event to the on_close function
    root_window.protocol("WM_DELETE_WINDOW", on_close)

    try:
        loop.run_forever()
    finally:
        loop.close()
