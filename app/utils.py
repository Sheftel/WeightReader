from tkinter import messagebox as mb

from tkinter import *
from tkinter import ttk

from config import STATIC_PATH


def raise_error(title="Ошибка", message="Сообщение об ошибке", layout=None):
    mb.showerror(title=title, message=message,
                 parent=layout.root)


def sample_max_volume_reached_mb(max_volume, current_sample, layout=None):
    answer = mb.askyesno(title="Достигнут максимальный объем пробы",
                         message=f"Достигнут максимальный объем {max_volume} мл для пробы {current_sample}\nПерейти к следующей пробе?",
                         parent=layout.root
                         )
    return answer


def sample_new_sample_button_mb(current_volume, current_sample, layout=None):
    answer = mb.askyesno(title="Перейти к следующей пробе",
                         message=f"Собрано {current_volume} мл для пробы {current_sample}\nПерейти к следующей пробе?",
                         parent=layout.root)
    return answer

def sample_pack_mb(layout=None):
    answer = mb.askokcancel(
        title="Новый лоток",
        message="Замена лотка и переход к следующей пробе",
        parent=layout.root
    )
    return answer

def xview_event_handler(e):
    e.widget.update_idletasks()
    e.widget.xview('end')
    e.widget.unbind('<Expose>')


class DialogLayout:
    def __init__(self, root, parent, title, message,
                 command1=None, command2=None, command3=None,
                 buttontext1="button1", buttontext2="button2", buttontext3="button3"):
        self.root = root
        self.parent = parent
        self.window = Toplevel(self.root)
        self.window.title(title)
        self.window.iconbitmap(STATIC_PATH / "icon.ico")
        self.window.resizable(FALSE, FALSE)

        self.command1 = command1
        self.command2 = command2
        self.command3 = command3
        frame = ttk.Frame(self.window, padding=(5, 5, 5, 5))
        self.frame = frame
        frame.grid(row=0,column=0)
        message = message
        label = ttk.Label(frame, text=message)
        label.grid(row=0, column=0, columnspan=3, sticky=N)

        new_sample_button = ttk.Button(frame, text=buttontext1, command=self.buttoncommand1)
        new_sample_button.grid(row=1, column=0, sticky=N)

        new_sample_pack_button = ttk.Button(frame, text=buttontext2, command=self.buttoncommand2)
        new_sample_pack_button.grid(row=1, column=1, sticky=N)

        cancel_button = ttk.Button(frame, text=buttontext3, command=self.buttoncommand3)
        cancel_button.grid(row=1, column=2, sticky=N)


        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        height = self.root.winfo_height()
        width = self.root.winfo_width()

        self.window.update()
        dialog_height = self.window.winfo_height()
        dialog_width = self.window.winfo_width()

        self.window.geometry("+%d+%d" % (x + (width/2) - (dialog_width/2), y + (height/2) - (dialog_height/2)))
        self.window.update()

        self.window.grab_set()

    def buttoncommand1(self):
        if self.command1:
            self.command1()
        self.window.grab_release()
        self.window.destroy()

    def buttoncommand2(self):
        if self.command2:
            self.command2()
        self.window.grab_release()
        self.window.destroy()

    def buttoncommand3(self):
        if self.command3:
            self.command3()
        self.window.grab_release()
        self.window.destroy()
