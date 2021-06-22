import reapy

import tkinter as tk

reapy.configure_reaper()

window=tk.Tk()

text=tk.Text(window,width=20,height=20)
text.pack(fill=tk.X,side=tk.BOTTOM)
text.insert(tk.END, 'this Row finished...\n') 
text.see(tk.END)
text.update()

window.mainloop()
