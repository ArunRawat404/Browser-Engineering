import socket
import ssl
import tkinter

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in url:
            url += "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    
    def request(self):
        s = socket.socket(family= socket.AF_INET,
                        type= socket.SOCK_STREAM,
                        proto= socket.IPPROTO_TCP
                        )
        s.connect((self.host, self.port))

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        s.send(("GET {} HTTP/1.0\r\n".format(self.path) + "Host: {}\r\n\r\n".format(self.host)).encode("utf8"))

        response = s.makefile("r", encoding= "utf8", newline="\r\n")
        status_line = response.readline()
        version, status, explanation = status_line.split(" ", 2)

        response_headers = {}   
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        body = response.read()
        s.close()

        return body
    

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, 
                                    width=WIDTH, 
                                    height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Up>", self.scroll_up)

        # Linux: Binding to <Button-4> and <Button-5> is being used
        self.canvas.bind('<Button-4>', self.scroll_up)
        self.canvas.bind('<Button-5>', self.scroll_down)

    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scroll_down(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scroll_up(self, e):
        if self.scroll > 0:
            self.scroll -= SCROLL_STEP
            self.draw()

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == '\n':
            cursor_y += VSTEP
            cursor_x = HSTEP
        else:
            display_list.append((cursor_x, cursor_y, c))
            cursor_x += HSTEP

        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP

    return display_list

def lex(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text

if __name__ == "__main__":
    import sys
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()