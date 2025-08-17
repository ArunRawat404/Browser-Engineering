import socket
import ssl
import time
import gzip

# Will store socket connection {(host, port): socket}
open_sockets = {}

# Cache {url: (response_body, expiry_timestamp) }
cache = {}

class URL:
    def __init__(self, url):
        self.scheme, url_body = url.split(":", 1)
        assert self.scheme in ["http", "https", "file", "data", "view-source"], "Unsupported scheme"

        if self.scheme == "data":
            self.MIME_type, self.data = url_body.split(",", 1)
            return
        elif self.scheme == "view-source":
            self.actual_url = URL(url_body)
            return

        if url_body.startswith("//"):
            url_body = url_body[2:]

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        # For file URL the host and port are not needed so can be None
        if self.scheme == "file":
            self.host = None
            self.port = None
            self.path = url_body
        else:
            if "/" not in url_body:
                url_body =url_body + "/"
            self.host, path = url_body.split("/", 1)
            self.path = "/" + path

            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)

    def request(self, redirects=0):
        if self.scheme == "view-source":
            # Just forward request to actual URL
            return self.actual_url.request()
        elif self.scheme == "file":
            with open(self.path, "r", encoding="utf8") as file:
                return file.read()
        elif self.scheme == "data":
            return self.data
        else:
            socket_key = (self.host, self.port)
            if socket_key in open_sockets:
                s = open_sockets[socket_key]
            else:
                s = socket.socket(
                    family=socket.AF_INET,
                    type=socket.SOCK_STREAM,
                    proto=socket.IPPROTO_TCP
                )
                s.connect((self.host, self.port))

                if self.scheme == "https":
                    ctx = ssl.create_default_context()
                    s = ctx.wrap_socket(s, server_hostname=self.host)

                # Store socket connection for reuse
                open_sockets[socket_key] = s

            url = self.scheme + "://" + self.host + self.path
            now = time.time()

            if url in cache:
                body, expiry = cache[url]
                if expiry is None or now < expiry:
                    return body
                else:
                    del cache[url]

            headers = {
                "Host": self.host,
                "Connection": "keep-alive",
                "User-Agent": "ArunBrowser/0.1",
                "Accept-Encoding": "gzip",
            }

            request = f"GET {self.path} HTTP/1.1\r\n"
            for key, value in headers.items():
                request += f"{key}: {value}\r\n"
            request += "\r\n"
            s.send(request.encode("utf8"))

            # Read as raw bytes for accurate Content-Length
            response = s.makefile("rb")
            status_line = response.readline().decode("utf8")
            version, status, explanation = status_line.split(" ", 2)

            response_headers = {}
            while True:
                line = response.readline().decode("utf8")
                if line == "\r\n": break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            # redirect if status code is in 300 range
            if 300 <= int(status) < 400:
                if redirects >= 5:
                    raise Exception("Too many redirects")

                redirect_location = response_headers.get('location')
                if not redirect_location:
                    raise Exception("Redirect with no Location header")

                if "://" not in redirect_location:
                    # Handle relative URLs
                    if redirect_location.startswith("/"):
                        # Absolute path: /page.html
                        redirect_location = f"{self.scheme}://{self.host}{redirect_location}"
                    else:
                        # Relative path: page.html
                        if self.path.endswith("/"):
                            redirect_location = f"{self.scheme}://{self.host}{self.path}{redirect_location}"
                        else:
                            redirect_location = f"{self.scheme}://{self.host}{self.path}/{redirect_location}"

                redirect_url = URL(redirect_location)
                return redirect_url.request(redirects + 1)

            if response_headers.get("transfer-encoding") == "chunked":
                body_bytes = b""
                while True:
                    # Read chunk size line
                    size_line = response.readline().decode("utf8").strip()
                    chunk_size = int(size_line, 16)  # Parse hex to decimal

                    if chunk_size == 0:
                        # Last chunk
                        response.readline()  # Read final \r\n
                        break

                    # Read chunk data + \r\n
                    chunk_data = response.read(chunk_size)
                    response.read(2)  # Skip \r\n after chunk
                    body_bytes += chunk_data
            else:
                content_length = int(response_headers.get('content-length', 0))
                if content_length > 0:
                    body_bytes = response.read(content_length)  # Read exact bytes
                else:
                    body_bytes = response.read()

            content_encoding = response_headers.get("content-encoding", "")
            if content_encoding == "gzip":
                body_bytes = gzip.decompress(body_bytes)

            body = body_bytes.decode("utf8")

            if int(status) == 200:
                cache_control = response_headers.get("cache-control", '')

                expiry = None
                should_cache = False
                if "max-age=" in cache_control:
                    try:
                        for directive in cache_control.split(','):
                            directive = directive.strip()
                            if directive.startswith('max-age='):
                                max_age = int(directive.split('=')[1])
                                expiry = time.time() + max_age
                                should_cache = True
                                break
                    except (ValueError, IndexError):
                        pass

                if should_cache:
                    cache[url] = (body, expiry)

        return body


def decode_entities(text):
    ENTITIES = {
        "&lt;": "<",
        "&gt;": ">",
        "&copy;": "©",
        "&ndash;": "–",
        "&amp;": "&",
    }

    result = ""
    i = 0

    while i < len(text):
        if text[i] == "&":
            # Look for semicolon to end the entity
            semicolon_index = text.find(";", i+1)
            if semicolon_index != -1:
                entity = text[i:semicolon_index + 1]
                if entity in ENTITIES:
                    result += ENTITIES[entity]
                    i = semicolon_index + 1
                    continue

        # If no entity found, just add the character
        result += text[i]
        i += 1

    return result

    # we can use Python's built-in function and it handles all HTML entities 
    # import html
    # return html.unescape(text)

def show(body):
    # filter out HTML tags only
    text_only = ""
    in_tag = False

    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text_only += c

    # decode entities in the text content
    decoded_text = decode_entities(text_only)
    print(decoded_text, end="")

def load(url):
    body = url.request()

    if url.scheme == "view-source":
        # Print raw HTML instead of rendering
        pass
        print(body, end="")
    else:
        show(body)

DEFAULT_FILE = "file:///home/arun/Documents/Coding/Browser/Browser-Engineering/test.html"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        load(URL(sys.argv[1]))
    else:
        load(URL(DEFAULT_FILE))