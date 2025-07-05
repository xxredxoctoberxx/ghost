import customtkinter
import tkinter
from tkinter import messagebox
from PIL import ImageTk,Image
import requests
import json
from datetime import date,datetime,time, timedelta
import lxml
from bs4 import BeautifulSoup
import regex as re
import pandas as pd
import platform
import yfinance as yf
import threading
import time
import webbrowser
from queue import Queue
from enum import Enum, auto

from ghost_signal_bv02 import *
from ghost_bv05 import *
import ghost_global

#Setting the basic programm params
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")

class TicketPurpose(Enum):
    UPDATE_LOG_LINE = auto()
    PROGRESS_BAR = auto()
    PROGRESS_BAR_END = auto()
    PAGE_COUNT = auto()
    UPDATE_BUTTONS = auto()

class Ticket:
    def __init__(self,
                 ticket_type : TicketPurpose,
                 ticket_value : str):
        
        self.ticket_type = ticket_type
        self.ticket_value = ticket_value

class ToplevelWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iconbitmap(r'C:\Users\danil\OneDrive\שולחן העבודה\py4e\zerogravity_v0.2beta\graphics\zerogravityicon.ico')
        self.geometry("300x100")
        self.protocol("WM_DELETE_WINDOW", self.on_closing) 

    def on_closing(self, event=0):
        self.destroy() 

class App(customtkinter.CTk):

    WIDTH = 775 
    HEIGHT = 550
    LOG_LIST = []
    SELF_SIGNAL_STATE = 0

    def __init__(self):
        super().__init__()

        self.title('Ghost System - Version beta 0.6')
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}+1200+500")
        self.iconbitmap(r'C:\Users\danil\OneDrive\שולחן העבודה\py4e\zerogravity_v0.2beta\graphics\zerogravityicon.ico')
        self.resizable(False,False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.queue_message = Queue() #thread queue

        #Check for events
        self.bind("<<CheckQueue>>", self.check_queue)

        #GUI image
        image = Image.open(r"C:\Users\danil\PythonFiles\Ghost\banner.png")
        self.my_image = ImageTk.PhotoImage(image)
        self.image_label = tkinter.Label(master=self, image=self.my_image)
        self.image_label.grid(row=0,column=0)

        #Signal production button
        self.button = customtkinter.CTkButton(master=self, text="Produce Signal", command= self.open_estimate_window,state="normal")
        self.button.place(relx=0.80, rely=0.82)

        self.optionmenu = customtkinter.CTkOptionMenu(master=self, values=["Time Frame", "1 day", "2 days", "3 days",
                                                                      "4 days", "5 days"], anchor="center")
        self.optionmenu.set("Time Frame")
        self.optionmenu.place(relx=0.8, rely=0.88)

        #Top level window/ signal loading estimate & Kill switch
        self.toplevel_window = None
        self.kill_window = None

        #Run Ghost button
        self.runbutton = customtkinter.CTkButton(master=self, text="Run Ghost", command= self.run_button)
        self.runbutton.place(relx=0.80, rely=0.7)

        #Economic Calendar button
        self.ecobutton = customtkinter.CTkButton(master=self, text="Economic Calendar", command= self.eco_button)
        self.ecobutton.place(relx=0.80, rely=0.76)       

        #Logger
        self.textbox = customtkinter.CTkTextbox(self, width=600, height=150)
        self.textbox.insert("0.0", f":::Ghost System Version Beta 0.6, Ghost Signal Version Beta 0.2 ,Python {platform.python_version()}:::")
        self.textbox.place(relx=0.01, rely=0.7)

        #Kill-Switch
        self.killswitch = customtkinter.CTkButton(master=self, text="⭘ Kill Switch", command= self.kill_switch,
                                                  width = 140, height = 8, fg_color = 'transparent', font = (None, 8))
                                                  
        self.killswitch.place(relx=0.80, rely=0.94)

        #Signal Estimate top level window
        self.toplevel_window = ToplevelWindow(self)
        self.toplevel_window.title('Producing Signal')
        self.toplevel_window.geometry('300x50+2100+800')
        self.toplevel_window.resizable(False,False)
        self.label = customtkinter.CTkLabel(self.toplevel_window, text="Estimating time, please wait...", fg_color="transparent")
        self.label.pack()
        self.toplevel_window.withdraw()

        #Kill-Window
        self.kill_window = ToplevelWindow(self)  # create window if its None or destroyed
        self.kill_window.title('Kill all operations?')
        self.kill_window.geometry('300x50+2100+800')
        self.kill_window.resizable(False,False)
        kill_button = customtkinter.CTkButton(self.kill_window, text="Yes", fg_color='red', command=self.kill_yes)
        kill_button.place(relx=0.02, rely=0.3)
        no_kill_button = customtkinter.CTkButton(self.kill_window, text="No", command=self.kill_no)
        no_kill_button.place(relx=0.52, rely=0.3)
        self.kill_window.deiconify()
        self.kill_window.withdraw()
    
    def check_queue(self,event):
        '''
        Read the Queue.
        '''
        msg : Ticket
        msg = self.queue_message.get()

        if msg.ticket_type == TicketPurpose.UPDATE_LOG_LINE:
            self.textbox.insert("0.0", msg.ticket_value)
        elif msg.ticket_type == TicketPurpose.PROGRESS_BAR:
            self.label.configure(text = msg.ticket_value)
        elif msg.ticket_type == TicketPurpose.PROGRESS_BAR_END:
            self.label.configure(text = msg.ticket_value)
        elif msg.ticket_type == TicketPurpose.PAGE_COUNT:
            self.label.configure(text= msg.ticket_value)
        elif msg.ticket_type == TicketPurpose.UPDATE_BUTTONS:
            self.button.configure(state="normal")
            self.optionmenu.configure(state="normal")
            self.runbutton.configure(state="normal")
            
    def produce_button(self):
        '''
        this function starts the production of the firs signal of the day.
        '''

        value = self.optionmenu.get()
        if value == "Time Frame":
            return None
        elif int(value[0]) in [1,2,3,4,5]:
            signal_value = int(value[0])
            self.SELF_SIGNAL_STATE = signal_value
            self.button.configure(state="disabled")
            self.optionmenu.configure(state="disabled")
            self.runbutton.configure(state="disabled")

        self.get_signal(signal_value)
        self.SELF_SIGNAL_STATE = 0
        self.optionmenu.set("Time Frame")
    
    def run_button(self):
        self.button.configure(state="disabled")
        self.optionmenu.configure(state="disabled")
        self.runbutton.configure(state="disabled")
        thread_4 = threading.Thread(target=ghost_main, daemon=True)
        thread_4.start()

    def eco_button(self):
        '''Open Investing.com economic calander in default browser'''
        webbrowser.open_new(r'C:\Users\danil\OneDrive\Documents\calendar_investing.htm')

    def update_log(self):
        '''Update function for handling callbacks
        from logger function, buttons and more'''

        while True:

            #logger update
            with open('info.log') as file:
                try:
                    lines = file.readlines()
                except Exception:
                    lines = ['']
                for line in lines[-20:]:
                    if line in self.LOG_LIST:
                        pass
                    else:
                        ticket = Ticket(ticket_type=TicketPurpose.UPDATE_LOG_LINE,ticket_value=line)
                        self.queue_message.put(ticket)
                        self.event_generate("<<CheckQueue>>") #creating virtual event to tell tkinter to check to queue
                        self.LOG_LIST.append(line)
            
            #check button's status.

            #signal lable value: green or red if working or not

            #balance and pnl lable value update

    def update_log_thread(self):
        '''
        this function threads the upate log function feature.
        '''
        thread_1 =threading.Thread(target=self.update_log, daemon=True)
        thread_1.start()
    
    def open_estimate_window(self):
        '''
        this thread starts the production of the first signal of the day.
        '''
        self.toplevel_window.deiconify()
        thread_2 = threading.Thread(target=self.produce_button)
        thread_2.start()

    def loading_bar(self,page_count):
        '''
        This function holds all the info for the first signal loading bar feature.
        '''
        try:
            progressbar = customtkinter.CTkProgressBar(self.toplevel_window, orientation="horizontal")
            progressbar.pack()
            estimated_time_delta = page_count * 3 + 9 #3minutes per page, and 9 extra minutes on top
            now = datetime.today()
            end_time_time = now + timedelta(minutes=estimated_time_delta)
            time_delta = end_time_time - now
            denomimetor = time_delta.total_seconds()
            now = now.strftime("%H:%M:%S")
            end_time_str = end_time_time.strftime("%H:%M:%S")
            while now < end_time_str:
                now = datetime.today()
                time_delta = end_time_time - now
                numerator = time_delta.total_seconds()
                progress = numerator/denomimetor
                progress = 1 - progress
                progress_ticket = Ticket(TicketPurpose.PROGRESS_BAR, f'Estimated end time: {end_time_str} ... progress: {round(progress*100,2)}%')
                self.queue_message.put(progress_ticket)
                self.event_generate("<<CheckQueue>>")
                progressbar.set(progress)
                now = now.strftime("%H:%M:%S")
            progressbar.set(1)
            end_progress_ticket = Ticket(TicketPurpose.PROGRESS_BAR_END, f'Estimated end time: {end_time_str} ... progress: 100% ')
            self.queue_message.put(end_progress_ticket)
            self.event_generate("<<CheckQueue>>")
            self.label.configure(text = f'Estimated end time: {end_time_str} ... progress: 100% ')
        except Exception:
            pass
    
    def loading_bar_thread(self, t_delta):
        '''
        This thread holds all the info for the signal loading bar feature.
        '''
        status = False
        today = date.today()
        strt_date = today - timedelta(days=t_delta)
        strt_date = strt_date.strftime("%Y-%m-%d")
        try:
            status, page_count = estimate_runtime(strt_date)
            if status == False:
                ticket = Ticket(TicketPurpose.PAGE_COUNT,f"{page_count}")
                self.queue_message.put(ticket)
                self.event_generate("<<CheckQueue>>")
        except Exception:
            status = False
            page_count = 20
        thread_4 = threading.Thread(target = self.loading_bar, args=(page_count,), daemon=True)
        thread_4.start()
    
    def get_signal(self,t_delta):
        '''
        The function that goes and generates the first signal of the day when 'Produce Signal' is pressed.
        '''
        thread_2 = threading.Thread(target = self.loading_bar_thread, args=(t_delta,), daemon=True)
        thread_2.start()
        today = date.today()
        strt_date = today - timedelta(days=t_delta)
        strt_date = strt_date.strftime("%Y-%m-%d")
        thread_3 = threading.Thread(target = signal_main, args=(strt_date,), daemon=True)
        thread_3.start()
        thread_6 = threading.Thread(target = self.check_signal_creation, daemon = True)
        thread_6.start()

    def check_signal_creation(self):
        '''
        This helper function checks for when signal is created, and enables the buttons back.
        '''
        while ghost_global.signal_mode == 0:
            time.sleep(2)
        ticket = Ticket(ticket_type=TicketPurpose.UPDATE_BUTTONS, ticket_value='NONE')
        self.queue_message.put(ticket)
        self.event_generate("<<CheckQueue>>")
        
    def kill_switch(self):
        '''
        Open kill-switch top level window.
        '''

        thread_5 = threading.Thread(target = self.kill_window.deiconify(),daemon=True)
        thread_5.start
        
    def kill_yes(self):
        '''
        Trigger kill-switch.
        '''
        playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\kill_switch.mp3')
        il.ghost_log('KILL SWITCH TRIGGERED',30)
        ghost_global.kill_mode = 1
        self.kill_window.withdraw()

    def kill_no(self):
        '''
        Dont trigger kill-swritch.
        '''
        
        self.kill_window.withdraw()
        #lock.release()

    def on_closing(self, event=0):
        '''
        Destroy window when clicking on X.
        '''
        self.destroy() 

if __name__ == "__main__":
    app = App()
    app.update_log_thread()
    app.mainloop()