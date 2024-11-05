import tkinter as tk
from tkinter import simpledialog

def get_user_input(initial_value):
    # 创建一个新窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 弹出一个对话框，让用户输入新的值
    new_value = simpledialog.askstring("输入", "请输入新的值：", initialvalue=initial_value)

    # 如果用户点击了取消或者关闭了窗口，new_value将会是None
    if new_value is None:
        return initial_value  # 返回初始值
    else:
        return new_value

# 假设这是脚本计算出的结果
result = "这是初始结果"

# 弹出窗口让用户修改结果
updated_result = get_user_input(result)

# 打印修改后的结果
print("修改后的结果：", updated_result)