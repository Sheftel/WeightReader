from tkinter import messagebox as mb


def raise_error(title="Ошибка", message="Сообщение об ошибке"):
    mb.showerror(title=title, message=message)


def xview_event_handler(e):
    e.widget.update_idletasks()
    e.widget.xview('end')
    e.widget.unbind('<Expose>')
