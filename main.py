import asyncio
from Frames.login_form import init_login_frame
from ttkthemes import ThemedTk


async def close_program(loop):
    loop.stop()


async def tkinter_mainloop(root_window):
    while True:
        root_window.update()
        await asyncio.sleep(0.01)


async def main():
    # Initialize the Tkinter root window
    root_window = ThemedTk(theme="arc")
    root_window.geometry("1200x800")
    root_window.title("Trackloisirs")

    # Initialize the login frame
    init_login_frame(root_window)

    # Define a function to stop the event loop and close the window
    async def on_close():
        await close_program(loop)
        root_window.destroy()

    # Bind the window close event to the on_close function
    root_window.protocol(
        "WM_DELETE_WINDOW", lambda: asyncio.create_task(on_close())
    )

    # Integrate Tkinter's main loop with asyncio
    await tkinter_mainloop(root_window)


if __name__ == "__main__":
    # Create a new event loop and set it as the current event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the main coroutine in the event loop
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
