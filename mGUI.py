import s_dygang
import s_rarbgmirror
import s_rrys
import tkinter as tk
import webbrowser
import threading
import socket
import pyperclip

class win:
    def __init__(self):
        '''GUI窗口框架'''
        global status    #程序状态，0：空闲；1：有后台线程运行中
        status = 0
        global mode      #搜索源引擎活动状态
        mode = 'free'

        self.version_number = '089'
        self.sep_ceil = 100  #线程信号量

        self.window = tk.Tk()
        self.window.title('海王星影视检索器v'+self.version_number[0]+'.'+self.version_number[1]+'.'+self.version_number[2])
        self.window.geometry('1280x720')
        self.window.resizable(width=False, height=False)
        self.window.iconbitmap('resources/neptune_icon.ico')

        tk.Label(self.window, text="海王星影视检索器v"+self.version_number[0]+'.'+self.version_number[1]+'.'+self.version_number[2]+"，仅用于非商业用途，作者：RyanXin，mail：xyz@ryanxin.cn", font=('Times New Roman', 16), width=70, height=1).pack()
        tk.Label(self.window, text="搜索关键字:", font=('Times New Roman', 16), width=12, height=1).place(x=30, y=50)

        self.resFrame = tk.Frame()
        self.resFrame.place(x=30, y=100)

        self.scroll = tk.Scrollbar(self.resFrame)

        self.text = tk.Text(self.resFrame, font=('Times New Roman', 16), width=110, height=26)
        self.text.config(state=tk.DISABLED, yscrollcommand=self.scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH)
        
        self.scroll.config(command=self.text.yview)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.kw = tk.Entry(self.window, show=None, font=('Times New Roman', 16), width=20)
        self.kw.place(x=170, y=50)
        self.kw.bind("<Return>", lambda x: self.thread_function(self.go, (self.kw.get().strip(),)))

        self.om_var = tk.StringVar()
        self.om_var.set('dygang')
        self.om = tk.OptionMenu(self.window, self.om_var, 'dygang', 'rarbg', 'rarbg(film only)', 'rrys', 'zimuzu')
        self.om.place(x=450, y=47)

        self.find = tk.Button(self.window, text="搜索", font=('Times New Roman', 10), command=lambda: self.thread_function(self.go, (self.kw.get().strip(),)))
        self.find.place(x=400, y=50)

        self.initiate = tk.Button(self.window, text="rarbg初始化", font=('Times New Roman', 10), command=lambda: self.thread_function(self.initialize))
        self.initiate.place(x=630, y=50)

        self.updater = tk.Button(self.window, text="检查更新", font=('Times New Roman', 10), command=lambda: self.thread_function(self.check_update, (1,)))
        self.updater.place(x=900, y=50)

        self.message = tk.Text(self.window, font=('Times New Roman', 10), width=30, height=5)
        self.message.place(x=1050, y=10)
        self.message.config(state=tk.DISABLED)

        tk.Label(self.window, text="rarbg数量上限(0=无限制):", font=('Times New Roman', 12), width=25, height=1).place(x=-10, y=5)
        self.constraint = tk.Entry(self.window, show=None, font=('Times New Roman', 12), width=5)
        self.constraint.place(x=195,y=5)
        self.constraint.insert(tk.END, '100')

        #启动自动检查更新
        self.thread_function(self.check_update, (0,))

        self.window.mainloop()

    def hypertext(self, words, schema, awg=None):
        '''超文本处理程序，文本格式：header\n文本---->url\n...
            模式0：超链接输出，支持额外参数指定显示内容；模式1：搜索结果显示；模式2：复制链接'''
        words = words.split('\n')
        header = words[0]
        name = []
        url = []
        for i in range(1,len(words)-1):
            name.append(words[i].split('---->')[0])
            url.append(words[i].split('---->')[1])
        
        def show_hand_cursor(event):
            self.text.config(cursor='arrow')
        def show_arrow_cursor(event):
            self.text.config(cursor='xterm')
        def browse(url, m=-1):
            webbrowser.open(url)
            if m != -1:
                self.text.config(state=tk.NORMAL)
                self.text.tag_config(m, foreground='purple', underline=True)
                self.text.config(state=tk.DISABLED)
                self.window.update()
        def copy(url, m):
            pyperclip.copy(url)
            self.text.config(state=tk.NORMAL)
            self.text.tag_config(m, foreground='purple', underline=True)
            self.text.config(state=tk.DISABLED)
            self.window.update()
        def handlerAdapter(fun, **kwds):
            return lambda event, fun=fun, kwds=kwds: fun(**kwds)
        def back(event):
            self.text.config(state=tk.NORMAL)
            self.text.delete('1.0', tk.END)
            self.hypertext(self.last_words, 1)
            self.text.config(state=tk.DISABLED)
            self.window.update()

        self.text.insert(tk.END, header+'\n')
        if schema == 0:
            for m in range(len(words)-2):
                self.text.insert(tk.END, name[m]+'    ')
                self.text.tag_config(m, foreground='blue', underline=True)
                self.text.tag_bind(m, '<Enter>', show_hand_cursor)
                self.text.tag_bind(m, '<Leave>', show_arrow_cursor)
                if not awg:
                    self.text.insert(tk.INSERT, url[m]+'\n', m)
                else:
                    self.text.insert(tk.INSERT, awg+'\n', m)
                self.text.tag_bind(m, '<Button-1>', handlerAdapter(browse, url=url[m]))
        elif schema == 1:
            for m in range(len(words)-2):
                self.text.insert(tk.END, name[m]+'    ')
                self.text.tag_config(m, foreground='blue', underline=True)
                self.text.tag_bind(m, '<Enter>', show_hand_cursor)
                self.text.tag_bind(m, '<Leave>', show_arrow_cursor)
                self.text.insert(tk.INSERT, '详细', m)
                self.text.tag_bind(m, '<Button-1>', handlerAdapter(browse, url=url[m], m=m))
                self.text.insert(tk.INSERT, '    ')
                self.text.tag_config(str(m)+'a', foreground='blue', underline=True)
                self.text.tag_bind(str(m)+'a', '<Enter>', show_hand_cursor)
                self.text.tag_bind(str(m)+'a', '<Leave>', show_arrow_cursor)
                self.text.insert(tk.INSERT, '下载链接\n', str(m)+'a')
                self.text.tag_bind(str(m)+'a', '<Button-1>', handlerAdapter(self.thread_function, function=self.download_address, args=(name[m], url[m])))
        elif schema == 2:
            self.text.tag_config('#0', foreground='blue', underline=True)
            self.text.tag_bind('#0', '<Enter>', show_hand_cursor)
            self.text.tag_bind('#0', '<Leave>', show_arrow_cursor)
            self.text.insert(tk.INSERT, '返回\n', '#0')
            self.text.tag_bind('#0', '<Button-1>', back)
            for m in range(len(words)-2):
                self.text.insert(tk.END, name[m])
                if url[m]:
                    self.text.insert(tk.INSERT, '    ')
                    self.text.tag_config(m, foreground='blue', underline=True)
                    self.text.tag_bind(m, '<Enter>', show_hand_cursor)
                    self.text.tag_bind(m, '<Leave>', show_arrow_cursor)
                    self.text.insert(tk.INSERT, '复制链接地址\n', m)
                    self.text.tag_bind(m, '<Button-1>', handlerAdapter(copy, url=url[m], m=m))
                else:
                    self.text.insert(tk.INSERT, '\n')

    def go(self, key):
        '''搜索主体流程程序'''
        self.text.config(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, '搜索中...\n')
        self.text.config(state=tk.DISABLED)
        self.message.config(state=tk.NORMAL)
        self.message.delete('1.0', tk.END)
        self.message.config(state=tk.DISABLED)
        self.window.update()
        if not key:
            words = '搜索内容不能为空'
        else:
            global mode
            mode = self.om_var.get()
            if mode == 'dygang':
                words = s_dygang.match(key, self)
            elif mode == 'rarbg':
                if self.constraint.get().strip().isdecimal():
                    words = s_rarbgmirror.match(key, int(self.constraint.get().strip()), 0, self)
                else:
                    words = '请正确输入数量上限'
            elif mode == 'rarbg(film only)':
                if self.constraint.get().strip().isdecimal():
                    words = s_rarbgmirror.match(key, int(self.constraint.get().strip()), 1, self)
                else:
                    words = '请正确输入数量上限'
            elif mode == 'rrys':
                words = s_rrys.search(key, 0, self)
            elif mode == 'zimuzu':
                words = s_rrys.search(key, 1, self)
        self.last_words = words

        self.text.config(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)
        self.hypertext(words, 1)
        self.text.config(state=tk.DISABLED)
        self.window.update()
        global status
        status = 0            #还原搜索状态

    def initialize(self):
        '''rarbg初始化程序'''
        mode = self.om_var.get()
        if mode == 'rarbg' or mode == 'rarbg(film only)':
            self.text.config(state=tk.NORMAL)
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, '等待rarbg初始化...\n')
            self.text.config(state=tk.DISABLED)
            self.window.update()
            words = s_rarbgmirror.get_cookie()
            self.text.config(state=tk.NORMAL)
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, words+'\n')
            self.text.config(state=tk.DISABLED)
            self.window.update()
        else:
            self.text.config(state=tk.NORMAL)
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, '请选择合适的搜索源再进行初始化\n')
            self.text.config(state=tk.DISABLED)
            self.window.update()
        global status
        status = 0

    def return_info(self, info):
        '''后台搜索状态消息返回'''
        self.message.config(state=tk.NORMAL)
        self.message.insert(tk.END, info+'\n')
        self.message.config(state=tk.DISABLED)
        self.window.update()

    def check_update(self, active):
        '''检查更新，用户主动触发传入1，被动运行传入0'''
        try:
            self.text.config(state=tk.NORMAL)
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, '正在检查版本更新...\n')
            self.text.config(state=tk.DISABLED)
            self.window.update()
            #socket连接
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect(('ryanxin.cn', 25345))
            server_data = sock.recv(1024*4).decode('utf-8')
            sock.close()
            server_data = server_data.split('\n')
            lateset_version_number = server_data[0]
            self.text.config(state=tk.NORMAL)
            self.text.delete('1.0', tk.END)
            #判断版本号
            if self.version_number[0] >= lateset_version_number[0] and self.version_number[1] >= lateset_version_number[1] and self.version_number[2] >= lateset_version_number[2]:
                if active == 1:
                    version_summary = '\n'.join(server_data[2:])
                    self.text.insert(tk.END, '恭喜，你正在使用最新版本！\n')
                    self.text.insert(tk.END, '\n新特色：\n' + version_summary + '\n')
            else:
                download_url = server_data[1]
                version_summary = '\n'.join(server_data[2:])
                words = '发现新版本！\n海王星影视检索器v'+lateset_version_number[0]+'.'+lateset_version_number[1]+'.'+lateset_version_number[2]+'---->'+download_url+'\n'
                self.hypertext(words, 0, '下载')
                self.text.insert(tk.END, '\n新特色：\n'+version_summary+'\n')
            self.text.config(state=tk.DISABLED)
            self.window.update()
        except:
            self.text.config(state=tk.NORMAL)
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, '检查更新失败')
            self.text.config(state=tk.DISABLED)
            self.window.update()
        finally:
            global status
            status = 0

    def download_address(self, name, url):
        '''获取影片下载地址'''
        self.text.config(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, '加载中...\n')
        self.text.config(state=tk.DISABLED)
        self.message.config(state=tk.NORMAL)
        self.message.delete('1.0', tk.END)
        self.message.config(state=tk.DISABLED)
        self.window.update()
        global mode
        words = ''
        if mode == 'dygang':
            words = s_dygang.get_download_address(url, self)
        elif mode == 'rarbg' or mode == 'rarbg(film only)':
            words = s_rarbgmirror.get_download_address(url, self)
        elif mode == 'rrys':
            words = s_rrys.get_download_address(url, self)
        elif mode == 'zimuzu':
            words = s_rrys.zimuzu_download_address(url, self)

        self.text.config(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)
        if not words:
            words = '很抱歉，此文档解析失败，请尝试手动查看详细信息或查看其他条目\n'
        elif '.../错误代码' not in words:
            words = name + ' 下载地址：\n' + words
        self.hypertext(words, 2)
        self.text.config(state=tk.DISABLED)
        self.window.update()
        global status
        status = 0            #还原搜索状态

    def thread_function(self, function, args=()):
        '''多线程包装，传入函数名和元组形式的参数'''
        global status
        if status == 0:            #确认没有正在进行中的任务
            status = 1
            t = threading.Thread(target=function, args=args)
            t.setDaemon(True)
            t.start()

if __name__ == "__main__":
    win()
