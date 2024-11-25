from tkinter import messagebox as mb


def raise_error(title="Ошибка", message="Сообщение об ошибке"):
    mb.showerror(title=title, message=message)


def sample_max_volume_reached_mb(max_volume, current_sample):
    answer = mb.askyesno(title="Достигнут максимальный объем пробы",
                         message=f"Достигнут максимальный объем {max_volume} мл для пробы {current_sample}\nПерейти к следующей пробе?")
    return answer


def sample_new_sample_button_mb(current_volume, current_sample):
    answer = mb.askyesno(title="Перейти к следующей пробе",
                         message=f"Собрано {current_volume} мл для пробы {current_sample}\nПерейти к следующей пробе?")
    return answer


def xview_event_handler(e):
    e.widget.update_idletasks()
    e.widget.xview('end')
    e.widget.unbind('<Expose>')
