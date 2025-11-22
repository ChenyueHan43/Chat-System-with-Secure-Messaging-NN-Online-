#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# import all the required  modules
import threading
import select
from tkinter import *
from tkinter import font
from tkinter import ttk
from chat_utils import *
from client_state_machine import ClientSM
import json
import socket
from PIL import Image, ImageTk, ImageGrab
import io
import torch
from CNN import load_model, predict_digit
from torchvision import transforms 
import base64


# GUI class for the chat
class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = load_model().to(self.device)  # 确保模型加载到正确设备

    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Login")
        self.login.resizable(width = False, 
                             height = False)
        self.login.configure(width = 400,
                             height = 350)
        # create a Label
        self.pls = Label(self.login, 
                       text = "Please login to continue",
                       justify = CENTER, 
                       font = "Helvetica 14 bold")
          
        self.pls.place(relheight = 0.1,
                       relx = 0.2, 
                       rely = 0.05)
        # create a Label
        self.labelName = Label(self.login,
                               text = "Name: ",
                               font = "Helvetica 12")
          
        self.labelName.place(relheight = 0.1,
                             relx = 0.1, 
                             rely = 0.2)
          
        # create a entry box for 
        # tyoing the message
        self.entryName = Entry(self.login, 
                             font = "Helvetica 14")
          
        self.entryName.place(relwidth = 0.7, 
                             relheight = 0.12,
                             relx = 0.25,
                             rely = 0.2)
          
        # set the focus of the curser
        self.entryName.focus()

        self.labelPass = Label(self.login,
                               text="Password: ",
                               font="Helvetica 12")
        self.labelPass.place(relheight=0.1,relx=0.1,rely=0.35)

        self.entryPass = Entry(self.login,font="Helvetica 14",show="*")
        self.entryPass.place(relwidth=0.7,relheight=0.12,relx=0.25,rely=0.35)
          
        # create a Continue Button 
        # along with action
        self.go = Button(self.login,
                         text = "CONTINUE", 
                         font = "Helvetica 14 bold", 
                         command = lambda: self.goAhead(self.entryName.get(),self.entryPass.get()))
          
        self.go.place(relx = 0.35,
                      rely = 0.55)
        self.errorLabel= Label(self.login,text="",fg="red",font="Helvatica 12")
        self.errorLabel.place(relx=0.35, rely=0.55)
        self.Window.mainloop()
  
    def goAhead(self, name , password):
        if len(name) > 0 and len(password)>0:
            msg = json.dumps({"action":"login", "name": name,"password":password})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'ok':
                self.login.destroy()
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name)
                self.textCons.config(state = NORMAL)
                # self.textCons.insert(END, "hello" +"\n\n")   
                self.textCons.insert(END, menu +"\n\n")      
                self.textCons.config(state = DISABLED)
                self.textCons.see(END)
                # while True:
                #     self.proc()
        # the thread to receive messages
                process = threading.Thread(target=self.proc)
                process.daemon = True
                process.start()
            elif response["status"] == 'wrong-password':
                self.errorLabel.config(text="Wrong username or password")
            elif response["status"] == 'duplicate':
                self.errorLabel.config(text="User already logged in")
        else:
            self.errorLabel.config(text="Username and password cannot be empty")
    def layout(self,name):
        
        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width = False,
                              height = False)
        self.Window.configure(width = 1000,
                              height = 700,
                              bg = "#FFFFFF")
        self.labelHead = Label(self.Window,
                             bg = "#17202A", 
                              fg = "#EAECEE",
                              text = self.name ,
                               font = "Helvetica 13 bold",
                               pady = 5)
          
        self.labelHead.place(relwidth = 1)
        self.line = Label(self.Window,
                          width = 450,
                          bg = "#ABB2B9")
          
        self.line.place(relwidth = 1,
                        rely = 0.07,
                        relheight = 0.012)
        chat_frame = Frame(self.Window, bg="#17202A")
        chat_frame.place(relwidth=0.6, relheight=0.9, rely=0.08)
          
        self.textCons = Text(chat_frame,
                             width = 20, 
                             height = 2,
                             bg = "#17202A",
                             fg = "#EAECEE",
                             font = "Helvetica 14", 
                             padx = 5,
                             pady = 5)
          
        self.textCons.place(relheight = 0.8,
                            relwidth = 1 )
        self.textCons.tag_configure("white", foreground="#EAECEE")
        self.textCons.insert(END, "Initial message\n", "white")
          
        self.labelBottom = Frame(self.Window, bg="#ABB2B9")
        self.labelBottom.place(relwidth=1, rely=0.8, relheight=0.2)
          
        self.entryMsg = Entry(self.labelBottom,
                              bg = "#2C3E50",
                              fg = "#EAECEE",
                              font = "Helvetica 13")
          
        # place the given widget
        # into the gui window
        self.entryMsg.place(relwidth = 0.65,
                            relheight = 0.3,
                            rely = 0.1,
                            relx = 0.01)
          
        self.entryMsg.focus()

        
          
        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text = "Send",
                                font = "Helvetica 10 bold", 
                                width=8,
                                bg="#3A5F9A",fg="#FFFFFF",
                                command = lambda : self.sendButton(self.entryMsg.get()))
        self.buttonMsg.place(relx = 0.5,
                             rely = 0.1,
                             relheight = 0.3, 
                             relwidth = 0.15)

    


        button_frame = Frame(self.labelBottom, bg="#ABB2B9")
        button_frame.place(rely=0.5, relwidth=1, relheight=0.5)
    
    # Time button
        self.timeButton = Button(button_frame,
                           text="Time",
                           font="Helvetica 10 bold",
                           width=8,
                           bg="#3A5F9A",
                           fg="#FFFFFF",
                           command=self.get_time)
        self.timeButton.grid(row=0, column=0, padx=5, pady=5,sticky="nsew")
    
    # Who button (lists online users)
        self.whoButton = Button(button_frame,
                          text="Who",
                          font="Helvetica 10 bold",
                          width=8,
                          bg="#3A5F9A",
                          fg="#FFFFFF",
                          command=self.get_who)
        self.whoButton.grid(row=0, column=1, padx=5, pady=5,sticky="nsew")
    
    # Poem button
        self.poemButton = Button(button_frame,
                           text="Poem",
                           font="Helvetica 10 bold",
                           width=8,
                           bg="#3A5F9A",
                           fg="#FFFFFF",
                           command=self.get_poem)
        self.poemButton.grid(row=0, column=2, padx=5, pady=5,sticky="nsew")
    
    # Search button
        self.searchButton = Button(button_frame,
                             text="Search",
                             font="Helvetica 10 bold",
                             width=8,
                             bg="#3A5F9A",
                             fg="#FFFFFF",
                             command=self.get_search)
        self.searchButton.grid(row=0, column=3, padx=5, pady=5,sticky="nsew")

        digit_frame = Frame(self.Window, bg="#17202A")
        digit_frame.place(relx=0.61, relwidth=0.39, relheight=0.9, rely=0.08)

    # 手写区域标题
        Label(digit_frame,
         text="Handwritten Digit Recognition",
         bg="#17202A",
         fg="#EAECEE",
         font="Helvetica 12 bold").pack(pady=10)

    # 画布区域
        self.canvas = Canvas(digit_frame,
                        width=300,
                        height=300,
                        bg="white",
                        highlightthickness=1,
                        highlightbackground="gray")
        self.canvas.pack(pady=10)

    # 控制按钮区域
        btn_frame = Frame(digit_frame, bg="#17202A")
        btn_frame.pack()

        self.clear_btn = Button(btn_frame,
                          text="Clear",
                          font="Helvetica 10 bold",
                          width=10,
                          bg="#4A6FA5",
                          fg="#EAECEE",
                          command=self.clear_canvas)
        self.clear_btn.grid(row=0, column=0, padx=20, pady=10)

        self.recognize_btn = Button(btn_frame,
                              text="Recognize",
                              font="Helvetica 10 bold",
                              width=10,
                              bg="#4A6FA5",
                              fg="#EAECEE",
                              command=self.recognize_digit)
        self.recognize_btn.grid(row=0, column=1, padx=20, pady=10)


        
        # create a scroll bar
        scrollbar = Scrollbar(self.textCons)
          
        # place the scroll bar 
        # into the gui window
        scrollbar.place(relheight = 1,
                        relx = 0.974)
          
        scrollbar.config(command = self.textCons.yview)
          
        self.textCons.config(state = DISABLED)

        self.setup_digit_recognition()
    
    def get_time(self):
        msg = json.dumps({"action": "time"})  # 发送请求
        self.send(msg)

    def get_who(self):
        msg = json.dumps({"action": "list"})
        self.send(msg)

    def get_poem(self):
    # Create a popup to ask for poem number
        poem_popup = Toplevel()
        poem_popup.title("Get Poem")
        poem_popup.resizable(width=False, height=False)
    
        Label(poem_popup, text="Enter poem number:").pack(pady=5)
        poem_entry = Entry(poem_popup)
        poem_entry.pack(pady=5)
    
        def send_poem_request():
            try:
                poem_num = int(poem_entry.get())
                msg = json.dumps({"action": "poem", "target": poem_num})
                self.send(msg)
                poem_popup.destroy()

            except ValueError:
                Label(poem_popup, text="Please enter a valid number!", fg="red").pack()
    
        Button(poem_popup, text="Get Poem", command=send_poem_request).pack(pady=5)

    def get_search(self):
    # Create a popup to ask for search term
        search_popup = Toplevel()
        search_popup.title("Search")
        search_popup.resizable(width=False, height=False)
    
        Label(search_popup, text="Enter search term:").pack(pady=5)
        search_entry = Entry(search_popup)
        search_entry.pack(pady=5)
    
        def send_search_request():
            term = search_entry.get()
            if term:
                msg = json.dumps({"action": "search", "target": term})
                self.send(msg)
                search_popup.destroy()
    
        Button(search_popup, text="Search", command=send_search_request).pack(pady=5) 
    
    def setup_digit_recognition(self):
        
        # 绑定鼠标事件
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.config(width=280, height=280)  # 更接近MNIST比例
        # 加载模型
        try:
            self.model = load_model()  # 从CNN.py导入的函数
        except:
            self.textCons.insert(END, "Model loading failed!\n")
    
    def draw(self, event):
        x, y = event.x, event.y
        r = 5
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="black", outline="black")
    
    def clear_canvas(self):
        self.canvas.delete("all")
    
    def recognize_digit(self):
        import numpy as np
        from PIL import ImageOps

        if len(self.canvas.find_all()) == 0:  # 没有绘制内容
            self.display_message("请先书写数字再识别")
            return
        # 1. 使用PostScript获取画布内容
        ps = self.canvas.postscript(colormode='mono')
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
    
    # 2. 转换为灰度并反色（黑底白字）
        img = img.convert('L')
        img = ImageOps.invert(img)
    
    # 3. 找到数字的边界并裁剪
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        
        # 保持宽高比的同时缩放到20像素高
            w, h = img.size
            new_h = 20
            new_w = int(w * (new_h / h))
            img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # 放入28x28的中心
            new_img = Image.new('L', (28, 28), 0)
            offset = ((28 - new_w) // 2, (28 - new_h) // 2)
            new_img.paste(img, offset)
        else:
            new_img = Image.new('L', (28, 28), 0)
    
    # 4. 保存调试图像
        new_img.save("debug_preprocessed.png")
    
    # 5. 转换为模型输入
        img_array = np.array(new_img) / 255.0
        img_tensor = torch.from_numpy(img_array).float()
        img_tensor = (img_tensor - 0.1307) / 0.3081  # MNIST标准化
        img_tensor = img_tensor.unsqueeze(0).unsqueeze(0).to(self.device)
    
    # 6. 预测
        with torch.no_grad():
            output = self.model(img_tensor)
            pred = output.argmax(dim=1, keepdim=True)
            digit = pred.item()
        self.display_message(f"Predicted digit: {digit}")

        img_bytes = io.BytesIO()
        new_img.save(img_bytes, format='PNG')
        img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    # 发送识别结果给服务器
        msg = {
        "action": "digit_recognition",
        "digit": digit,
        "image": img_base64,
        "timestamp": time.time()
        }
        self.send(json.dumps(msg))
         
  
    # function to basically start the thread for sending messages
    def sendButton(self, msg):
        self.display_message(f"me: {msg}")
        self.textCons.config(state = DISABLED)
        self.my_msg = msg
        # print(msg)
        self.entryMsg.delete(0, END)

    def proc(self):
        # print(self.msg)
        while True:
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg = []
            # print(self.msg)
            if self.socket in read:
                peer_msg = self.recv()
            if len(self.my_msg) > 0 or len(peer_msg) > 0:
                # print(self.system_msg)
                self.system_msg += self.sm.proc(self.my_msg, peer_msg)
                self.my_msg = ""
                self.textCons.config(state = NORMAL)
                self.textCons.insert(END, self.system_msg +"\n\n")      
                self.textCons.config(state = DISABLED)
                self.textCons.see(END)
            if peer_msg:
                try:
                    response = json.loads(peer_msg)
                    # 处理time响应
                    if response.get("action") == "time":
                        self.display_message(f"current time: {response['results']}")
                    # 处理who/list响应
                    elif response.get("action") == "list":
                        self.display_message(f"online users:\n{response['results']}")
                    # 处理poem响应
                    elif response.get("action") == "poem":
                        self.display_message(f"poem {response.get('target','')}:\n{response['results']}")
                    # 处理search响应
                    elif response.get("action") == "search":
                        self.display_message(f"search result:\n{response['results']}")
                    elif response.get("action") == "digit_result":
                        img_data = base64.b64decode(response["image"])
                        img = Image.open(io.BytesIO(img_data))
                        
                        # 显示识别结果
                        self.display_message(
                            f"{response['from']} recognize digit: {response['digit']}\n"
                            f"recognize time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(response['timestamp']))}")
                    elif response.get("action") == "exchange":
                         encrypted_b64 = response["message"]
                         encrypted = base64.b64decode(encrypted_b64)
                         decrypted = rsa_decrypt(encrypted, self.sm.rsa_private_key)
                         plaintext = decrypted.decode('utf-8')
                    
                         self.display_message(
                        f"{response['from']} (decrypted): {plaintext}"
                    )
                    else:
                        self.display_message(f"message: {peer_msg}")
                except json.JSONDecodeError:
                    self.display_message(f"原始响应: {peer_msg}")
                
                
    def display_message(self, msg):
        self.textCons.config(state=NORMAL)
        self.textCons.insert(END, msg + "\n\n")
        self.textCons.config(state=DISABLED)
        self.textCons.see(END)
                
    def run(self):
        self.login()
# create a GUI class object
if __name__ == "__main__": 
    from CNN import load_model
    model = load_model()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(SERVER) 
    sm = ClientSM(s)
    g = GUI(lambda msg: mysend(s, msg), 
        lambda: myrecv(s), 
        sm, s)
    g.model = model 
    g.run()
