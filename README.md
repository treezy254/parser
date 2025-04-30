# Fast Concurrent File Search Server

This is a high-performance, multithreaded Python server that receives client queries and searches for a specified string inside a file. It returns `True` if the string is found, `False` otherwise, and logs the execution time of the search.

---

## 🧩 Features

- Multithreaded request handling
- Optimized file search
- Returns boolean result
- Records algorithm execution time
- Built to run as a Linux systemd service

---

## 📁 Project Structure

project/ ├── src/ │ └── main.py ├── setup.sh └── README.md

---

## 🛠 Requirements

- Linux (Ubuntu/Debian/CentOS/etc)
- Python 3.8+
- No third-party Python libraries needed

---

## ⚙️ Installation

````bash
    chmod +x setup.sh

    sudo ./setup.sh


This will:

    Set up the app to run as a background service (file-search-server.service)

    Place logs in /var/log/file_search_server.log


🧪 Testing
✅ Unit Tests

Run all unit tests:

python3 -m unittest discover -s tests/unit

✅ End-to-End Test

python3 tests/e2e.py
```
````
