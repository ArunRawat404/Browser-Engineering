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
GET /path HTTP/1.0
Host: hostname

```

### Response Format
```
HTTP/1.0 200 OK
Header-Name: Header-Value
[more headers]

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
response = s.makefile("r", encoding="utf8", newline="\r\n")
```
- Wraps the socket into a file-like object
- Handles reading loops automatically
- Decodes bytes → string using UTF-8


## Implementation Steps

1. **Parse URL** into scheme, host, port, and path components
2. **Create socket** and connect to the host
3. **Wrap with SSL** if using HTTPS
4. **Send HTTP GET request** with proper Host header
5. **Parse HTTP response** into status line, headers, and body
6. **Filter HTML tags** and display only text content

## Code Structure

### Classes & Functions
```python
class URL:
    def __init__(self, url)    # Parse URL components
    def request()              # Send HTTP request, return body

def show(body)                 # Filter HTML tags, display text
def load(url)                  # Complete flow: request + show
```

### Core Implementation Flow

**`URL.__init__`:**
- Parse scheme, host, port, path from URL string
- Set default ports (80 for HTTP, 443 for HTTPS)
- Handle custom ports in hostname

**`URL.request`:**
- Create TCP socket with `AF_INET`, `SOCK_STREAM`, `IPPROTO_TCP`
- Connect to host:port
- Wrap with SSL context for HTTPS
- Send HTTP request with Host header
- Read and parse response (status line, headers, body)
- Return body content

**`show`:**
- Simple HTML tag filter using state machine
- Track `in_tag` boolean to skip content between `<` and `>`
- Print only text characters

**`load`:**
- Orchestrates the complete process
- Calls `url.request()` then `show(body)`

## Example Usage

```bash
python browser.py http://example.org/index.html
```