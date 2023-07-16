from tkinter import messagebox as mb


def raise_error(title="Ошибка", message="Сообщение об ошибке"):
    mb.showerror(title=title, message=message)
