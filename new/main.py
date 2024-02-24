import asyncio
import aiotkinter
from login_form import init_login_frame
from ttkthemes import ThemedTk

if __name__ == "__main__":
    asyncio.set_event_loop_policy(aiotkinter.TkinterEventLoopPolicy())
    loop = asyncio.get_event_loop()

    root_window = ThemedTk(theme="arc")
    root_window.geometry("1200x800")
    root_window.title("Trackloisirs")
    init_login_frame(root_window)

    loop.run_forever()
