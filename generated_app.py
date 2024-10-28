import tkinter as tk
from tkinter import ttk

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simple GUI")
        self.geometry("300x200")

        # Create a dropdown menu
        self.options = ["Option 1", "Option 2", "Option 3"]
        self.variable = tk.StringVar()
        self.variable.set(self.options[0])
        dropdown = ttk.OptionMenu(self, self.variable, *self.options)
        dropdown.pack(pady=20)

        # Create a text box
        self.text_box = tk.Text(self, height=10, width=40)
        self.text_box.pack(pady=20)

        # Create a button
        self.button = ttk.Button(self, text="Click Me", command=self.button_click)
        self.button.pack(pady=10)

    def button_click(self):
        # Get the selected option and add it to the text box
        selected_option = self.variable.get()
        self.text_box.insert(tk.END, f"You selected: {selected_option}\n")

if __name__ == "__main__":
    app = Application()
    app.mainloop()