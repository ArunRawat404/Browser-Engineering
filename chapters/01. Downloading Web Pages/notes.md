# Chapter 1 – Downloading HTTP

## Overview
This chapter covers the fundamentals of downloading web pages using HTTP requests. We build a basic browser that can parse URLs, establish connections, send HTTP requests, and display the text content of web pages.

## Key Concepts

### URL Structure
URL stands for Uniform Resource Locator, meaning that it is a portable (uniform) way to identify web pages (resources) and also that it describes how to access those files (locator).

URLs (Uniform Resource Locators) have a standardized format that tells us how to reach a resource on the web.

**Example:** `http://example.org:8080/index.html`

**Components:**
- **Scheme:** `http`, `https` - Protocol to use
- **Hostname:** `example.org` - Server address
- **Port:** `80` (HTTP default), `443` (HTTPS default), `8080` (custom)
- **Path:** `/index.html` - Resource location on server

## HTTP Request/Response Flow

HTTP (HyperText Transfer Protocol) is the language browsers and servers use to communicate.

### Request Format
```
GET /path HTTP/1.1
Host: hostname
Connection: keep-alive
User-Agent: ArunBrowser/0.1
Accept-Encoding: gzip
```

### Response Format
```
HTTP/1.1 200 OK
Header-Name: Header-Value
Content-Length: 1234
Content-Encoding: gzip
Cache-Control: max-age=3600

[body content]
```

### Sockets
Sockets are endpoints for network communication - they allow programs on different computers to talk to each other over a network. Think of them as telephone connections for computers.

Sockets are the foundation of network communication in programming.

**Address Families:**
- `AF_INET`: IPv4 internet addresses
- `AF_INET6`: IPv6 internet addresses
- `AF_BLUETOOTH`: Bluetooth connections

**Socket Types:**
- `SOCK_STREAM`: Stream-oriented, reliable (TCP) - like a phone call with guaranteed delivery
- `SOCK_DGRAM`: Datagram/packet-oriented (UDP) - like sending postcards, faster but no guarantee

**Protocols:**
- `IPPROTO_TCP`: Reliable TCP connections with error checking and ordering

### Encoding and Data Types
Computers store text as numbers, so we need encoding to convert between human-readable text and computer bytes.

Network communication requires converting between strings and bytes.

**String to Bytes:**
```python
>>> type("text")
<class 'str'>
>>> type("text".encode("utf8"))
<class 'bytes'>
```

**Reading Server Response:**
```python
response = s.makefile("rb")  # Raw bytes for compression support
```
- Wraps the socket into a file-like object
- Handles reading loops automatically
- Works with both text and binary data

## Enhanced Features Implementation

### HTTP/1.1 Headers
Modern browsers use HTTP/1.1 with specific headers for better communication:

```python
headers = {
    "Host": self.host,
    "Connection": "keep-alive",  # Reuse connections
    "User-Agent": "ArunBrowser/0.1",  # Browser identification
    "Accept-Encoding": "gzip",  # Support compression
}
```

Why these headers matter:
- **Host:** Required in HTTP/1.1, allows virtual hosting
- **Connection:** Controls socket reuse for performance
- **User-Agent:** Identifies browser to servers
- **Accept-Encoding:** Enables compression for faster transfers

### URL Schemes Beyond HTTP

#### File URLs
Access local files directly without network requests:

```python
if self.scheme == "file":
    with open(self.path, "r", encoding="utf8") as file:
        return file.read()
```
Example: `file:///home/user/page.html`

#### Data URLs
Embed content directly in the URL:

```python
if self.scheme == "data":
    self.MIME_type, self.data = url_body.split(",", 1)
    return self.data
```
Example: `data:text/html,<h1>Hello World!</h1>`

#### View-Source URLs
Display raw HTML instead of rendered content:

```python
if self.scheme == "view-source":
    return self.actual_url.request()  # Forward to actual URL
```
Example: `view-source:http://example.com`

### Connection Keep-Alive
Reusing socket connections dramatically improves performance by avoiding the overhead of establishing new connections for each request.

```python
# Global socket storage
open_sockets = {}

socket_key = (self.host, self.port)
if socket_key in open_sockets:
    s = open_sockets[socket_key]  # Reuse existing connection
else:
    s = socket.socket(...)  # Create new connection
    open_sockets[socket_key] = s  # Store for future use
```

Key considerations:
- Must read exact Content-Length bytes to avoid mixing responses
- Use `makefile("rb")` for accurate byte counting
- Connection reuse works across multiple requests to same server

### HTTP Redirects
Handle 3xx status codes by following Location header:

```python
if 300 <= int(status) < 400:
    if redirects >= 5:  # Prevent infinite loops
        raise Exception("Too many redirects")
    
    redirect_location = response_headers.get('location')
    # Handle relative vs absolute URLs
    if "://" not in redirect_location:
        if redirect_location.startswith("/"):
            redirect_location = f"{self.scheme}://{self.host}{redirect_location}"
    
    return URL(redirect_location).request(redirects + 1)
```

Redirect types:
- **Absolute:** `Location: https://example.com/newpage`
- **Relative:** `Location: /newpage` (same host)
- **Path-relative:** `Location: newpage` (same directory)

### Caching System
Avoid re-downloading unchanged resources by implementing HTTP caching:

```python
# Global cache storage
cache = {}  # {url: (response_body, expiry_timestamp)}

# Check cache before making request
if url in cache:
    body, expiry = cache[url]
    if expiry is None or time.time() < expiry:
        return body  # Serve from cache
    else:
        del cache[url]  # Remove expired entry
```

Cache-Control header support:
```python
if "max-age=" in cache_control:
    for directive in cache_control.split(','):
        if directive.strip().startswith('max-age='):
            max_age = int(directive.split('=')[1])
            expiry = time.time() + max_age
            should_cache = True
```

Caching rules:
- Only cache successful 200 responses
- Respect max-age directive for expiration
- Conservative approach: don't cache unknown directives
- Cache improves performance for repeated requests

### HTTP Compression
Enable gzip compression to reduce bandwidth and improve loading speed:

Request compression support:
```python
"Accept-Encoding": "gzip"  # Tell server we can handle compressed data
```

Handle compressed responses:
```python
content_encoding = response_headers.get("content-encoding", "")
if content_encoding == "gzip":
    body_bytes = gzip.decompress(body_bytes)  # Decompress received data
```

Benefits:
- Reduces bandwidth usage significantly (often 60-80% compression)
- Faster page loads over slow connections
- Server CPU trade-off for network speed

### Chunked Transfer Encoding
Handle variable-length responses when servers can't determine content size in advance (common with compression):

```python
if response_headers.get("transfer-encoding") == "chunked":
    body_bytes = b""
    while True:
        # Read chunk size in hexadecimal
        size_line = response.readline().decode("utf8").strip()
        chunk_size = int(size_line, 16)
        
        if chunk_size == 0:  # Final chunk
            response.readline()  # Read final \r\n
            break
        
        # Read chunk data
        chunk_data = response.read(chunk_size)
        response.read(2)  # Skip \r\n after chunk
        body_bytes += chunk_data
```

Chunked format:
```
[size-in-hex]\r\n
[data]\r\n
[next-size]\r\n
[next-data]\r\n
0\r\n
\r\n
```

Why chunked encoding:
- Server doesn't know final compressed size
- Can start sending data immediately
- Common with dynamic content and compression

### HTML Entity Decoding
Convert HTML entities back to readable characters:

```python
ENTITIES = {
    "&lt;": "<",
    "&gt;": ">", 
    "&copy;": "©",
    "&ndash;": "–",
    "&amp;": "&",
}
```

Why entities matter:
- `&lt;` and `&gt;` prevent HTML interpretation of `<` and `>`
- Allows displaying HTML code safely
- Essential for view-source functionality

## Implementation Flow

### Core Classes & Functions
```python
class URL:
    def __init__(self, url)    # Parse URL components (all schemes)
    def request()              # Send HTTP request, handle all features

def show(body)                 # Filter HTML tags, decode entities
def load(url)                  # Complete flow: request + show
def decode_entities(text)      # Convert HTML entities to characters
```

### Request Processing Pipeline
1. **URL Parsing:** Extract scheme, host, port, path
2. **Scheme Handling:** Route to appropriate handler (HTTP/file/data/view-source)
3. **Connection Management:** Reuse existing sockets when possible
4. **Cache Check:** Return cached response if valid
5. **HTTP Request:** Send with appropriate headers
6. **Response Reading:** Handle both chunked and content-length
7. **Decompression:** Decompress gzip content if needed
8. **Redirect Following:** Handle 3xx responses recursively
9. **Caching:** Store successful responses with expiration
10. **Content Display:** Filter HTML and decode entities

## Example Usage

```bash
python browser.py http://example.org/index.html
```