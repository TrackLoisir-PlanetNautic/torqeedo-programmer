from tkinter import *

from tkinter import ttk

lst = ['C', 'C++', 'Java',
       'Python', 'Perl',
       'PHP', 'ASP', 'JS']


def check_input(event):
    value = event.widget.get()

    if value == '':
        combo_box['values'] = lst
    else:
        data = []
        for item in lst:
            if value.lower() in item.lower():
                data.append(item)

        combo_box['values'] = data


root = Tk()

# creating Combobox
combo_box = ttk.Combobox(root)
combo_box['values'] = lst
combo_box.bind('<KeyRelease>', check_input)
combo_box.pack()

root.mainloop()
