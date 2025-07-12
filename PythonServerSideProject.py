import socket
import threading
import datetime
import time
from cryptography.fernet import Fernet
Host='127.0.0.1'
Port=3819
Listener_Limit=5
active_users=[] # all active users connected to the server
key=b'xLOm_woklKyAHcs4X3kbYRjQKeHhv87Rz0fApWdW09M='
fernet = Fernet(key)
# send message to all clients in the server, or if a new client joins, send all users the new updated users list
def send_message_to_all(message:bytes,update_users=False):
    for user in active_users:
        if update_users:
            user_list = ",".join([u[0] for u in active_users]) 
            send_message_to_client(user, f"USERLIST:{user_list}".encode())
        else:
            send_message_to_client(user, message)

       
#send message to one client 
def send_message_to_client(client,message:bytes):
    if(not message.decode().startswith("USERLIST")):
        dec_message=fernet.decrypt(message).decode()
        fully_enc=_message=fernet.encrypt(dec_message.encode()).decode()
        log_text=open(f"ServerMessages/{client[0]}.txt","a")
        log_text.write(fully_enc+"\n")
        log_text.close()
    client[1].sendall(message)
       
def send_user_message_log(username, client_socket):
    try:
        log_file_path = f"ServerMessages/{username}.txt"#folder with all user messages
        with open(log_file_path, "r") as log_file:
            for line in log_file:
                client_socket.sendall(line.encode())
                time.sleep(0.1)
    except Exception as e:
        print(f"Error sending message log to {username}: {e}")
   
#listen for upcoming messages from clients
def listen_for_messages(Client, username):
    while True:
        try:
            # Receive a message from the client
            message = Client.recv(2048).decode('utf-8')
            
            if not message:
                break  # If message is empty, exit the loop
            
            # Handle disconnection
            if message == "DISCONNECT":
                print("a user disconnected")
                for user in active_users:
                    if user[1] == Client:
                        active_users.remove(user)
                        break
                leaving_message=f"SERVER: {username} has left the chat at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                send_message_to_all(fernet.encrypt(leaving_message.encode()))
                send_message_to_all("", update_users=True)
                Client.close()
                break

            # Handle private messages
            if message.startswith("PRIVATE:"):
                parts = message.split(":", 2)
                if len(parts) < 3:
                    send_message_to_client((username, Client), "ERROR: Invalid private message format".encode())
                    continue
                recipient = parts[1]
                private_message = parts[2]
                timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                decoded_message=fernet.decrypt(private_message.encode()).decode()
                final_message =fernet.encrypt(f"[PRIVATE] {username} [{timestamp}]: {decoded_message}".encode())
                
                # Find the recipient
                recipient_found = False
                for user in active_users:
                    if user[0] == recipient:
                        send_message_to_client(user, final_message)  # Send to recipient
                        send_message_to_client((username, Client), fernet.encrypt(f"[SENT TO {recipient}] {decoded_message}".encode()))  # send back to sender
                        recipient_found = True
                        break
                
                if not recipient_found:
                    send_message_to_client((username, Client), f"ERROR: User {recipient} not found")
                continue

            # handle broadcast messages
            if message:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                final_message =fernet.encrypt( f'{username} [{timestamp}]: {fernet.decrypt(message).decode()}'.encode())
                send_message_to_all(final_message)

        except Exception as e:
            print(f"Error handling message from {username}: {e}")
            Client.close()
            break
            
#handle one of the users connected, and give each one his own listening thread
def Client_Handler(Client):
    while True:
        try:
            initial_message = Client.recv(2048).decode('utf-8')
            print(f"Received initial message: {initial_message}")  # Debug line
            
            if initial_message == "GETUSERLIST":
                user_list = ",".join([u[0] for u in active_users])  
                send_message_to_client((None, Client), f"USERLIST:{user_list}".encode())
                continue

            username = initial_message
            if any(u[0] == username for u in active_users):
                Client.sendall("USERNAME_TAKEN".encode())
                Client.close()
                return
            else:
                Client.sendall("USERNAME_UNTAKEN".encode())
            active_users.append((username, Client))
            send_user_message_log(username, Client)
            joining_message = fernet.encrypt(f"SERVER: {username} joined the experience".encode())
            send_message_to_all(joining_message)
            send_message_to_all("", update_users=True)

            # Send the user's previous message log

            threading.Thread(target=listen_for_messages, args=(Client, username)).start()
            break
        except Exception as e:
            print(f"Error handling client: {e}")
            Client.close()
            break
def main():
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        server.bind((Host,Port))
    except:
        print(f"Cannot Bind To Host {Host} in Port {Port}")

    server.listen(5)
    
    while True:
        client,address=server.accept()
        print(f"successfully connected to client {address[0]},{address[1]}")
        
        threading.Thread(target=Client_Handler,args=(client, )).start()
        
if __name__=='__main__':
    main()