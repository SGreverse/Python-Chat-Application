import socket
import threading
import datetime
import tkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
from cryptography.fernet import Fernet

Host='127.0.0.1'
Port=3819

DARK_GREY='#121212'
Median_GREY='#1F1B24'
OCEAN_BLUE='#464EBB'
WHITE='white'
FONT=("Helventica",17)
SMALL_FONT=("Helventica",13)
root=tk.Tk()
root.geometry("600x600")
root.title("Messenger Client")
root.resizable(False,False)

root.grid_rowconfigure(0,weight=1)
root.grid_rowconfigure(1,weight=4)
root.grid_rowconfigure(2,weight=1)

key=b'xLOm_woklKyAHcs4X3kbYRjQKeHhv87Rz0fApWdW09M='
fernet = Fernet(key)
client=None

top_frame=tk.Frame(root,width=600,height=100,bg=DARK_GREY)
top_frame.grid(row=0,column=0,sticky=tk.NSEW)
middle_frame=tk.Frame(root,width=600,height=400,bg=Median_GREY)
middle_frame.grid(row=1,column=0,sticky=tk.NSEW)
bottom_frame=tk.Frame(root,width=600,height=100,bg=DARK_GREY)
bottom_frame.grid(row=2,column=0,sticky=tk.NSEW)

user_listbox = tk.Listbox(bottom_frame, font=SMALL_FONT, bg=Median_GREY, fg=WHITE, height=5, width=15)
user_listbox.pack(side=tk.RIGHT, padx=10)
user_listbox.insert(0, "All")

def add_message(message):
    message_box.config(state=tk.NORMAL)
    message_box.insert(tk.END,message+ '\n')
    message_box.config(state=tk.DISABLED)

def connect():
    global client

    if client is None:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((Host, Port))
        except Exception as e:
            messagebox.showerror("Unable to connect", f"Cannot connect to server {Host}:{Port}. Server might be down.\nError: {e}")
            root.quit()
            root.destroy()
            return

    username = username_textbox.get()

    client.sendall("GETUSERLIST".encode())
    userlist_message = client.recv(2048).decode()
    if userlist_message.startswith("USERLIST:"):
        userlist = userlist_message.split(":", 1)[1].split(",")
        if username == '' or username in userlist:
            messagebox.showerror("Undetermined username", "Please enter an untaken username")
            client.close()
            client = None
            return

    client.sendall(username.encode())
    response = client.recv(2048).decode()
    if response == "USERNAME_TAKEN":
        messagebox.showerror("Username Error", "This username is already taken. Please try another.")
        client.close()
        client = None
        return

    add_message("[SERVER] Successfully connected to the server")
    threading.Thread(target=Listen_for_messages_from_server, args=(client,)).start()

    username_button.config(state=tk.DISABLED)
    username_textbox.config(state=tk.DISABLED)
    
def send():
    message = message_textbox.get()
    if message != '':
        encMessage = fernet.encrypt(message.encode())
        recipient = user_listbox.get(user_listbox.curselection()) if user_listbox.curselection() else "All"
        if recipient == "All":
            client.sendall(encMessage)
        else:
            client.sendall(f"PRIVATE:{recipient}:{encMessage.decode()}".encode())
        message_textbox.delete(0, tk.END) 
    else:
        messagebox.showerror("Error", "Empty message")

username_label=tk.Label (top_frame,text="ENTER USERNAME:",font=FONT,bg=DARK_GREY,fg=WHITE)
username_label.pack(side=tk.LEFT,padx=10)

username_textbox=tk.Entry(top_frame,font=FONT,bg=Median_GREY,fg=WHITE,width=21)
username_textbox.pack(side=tk.LEFT,padx=5)

username_button=tk.Button(top_frame,text="Join",font=FONT,bg=OCEAN_BLUE,fg=WHITE,command=connect)
username_button.pack(side=tk.LEFT)

message_textbox=tk.Entry(bottom_frame,font=FONT,bg=Median_GREY,width=28)
message_textbox.pack(side=tk.LEFT,padx=10)

message_button=tk.Button(bottom_frame,text="Send",font=FONT,bg=OCEAN_BLUE,fg=WHITE,command=send)
message_button.pack(side=tk.LEFT,padx=5)

message_box=scrolledtext.ScrolledText(middle_frame,font=SMALL_FONT,bg=Median_GREY,fg=WHITE,width=67,height=23)
message_box.config(state=tk.DISABLED)
message_box.pack(side=tk.LEFT,padx=5)


def on_closing():
    try:
        client.sendall("DISCONNECT".encode())  # Notify the server
        client.close()  
    except:
        pass
    root.destroy()


def Listen_for_messages_from_server(Client):
    while True:
        try:
            message = Client.recv(2048).decode()
            if message.startswith("USERLIST:"):
                # Update the user list
                user_list = message.split(":", 1)[1].split(",")
                user_listbox.delete(1, tk.END)  
                for user in user_list:
                    if user != username_textbox.get():  # Exclude yourself
                        user_listbox.insert(tk.END, user)
            else:
                dec_message=fernet.decrypt(message.encode()).decode()
                add_message(dec_message)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            break
    
def main():
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
      
    print("Sevrer is running")
    
if __name__=='__main__':
    main()