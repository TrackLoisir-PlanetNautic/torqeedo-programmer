from tkinter import Tk
import asyncio
import aiotkinter
from loginform import init_login_window

if __name__ == "__main__":
    asyncio.set_event_loop_policy(aiotkinter.TkinterEventLoopPolicy())
    loop = asyncio.get_event_loop()

    login_window = Tk()
    init_login_window(login_window)

    loop.run_forever()
