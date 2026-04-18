# DotPaw 🐾

A simple configuration file parser for Python using `.paw` files.

![PyPI](https://img.shields.io/pypi/v/dotpaw?style=for-the-badge)
![Python](https://img.shields.io/pypi/pyversions/dotpaw?style=for-the-badge)
![License](https://img.shields.io/pypi/l/dotpaw?style=for-the-badge)
![Downloads](https://img.shields.io/pypi/dm/dotpaw?style=for-the-badge)

---

## ✨ Features

- Type casting (`[int]`, `[bool]`, `[dict]`, etc.)
- Environment variables override DotPaw configs
- Deep merge support for multiple configs
- Export to environment (can be used by `os.environ`)
- Dot-notation access (`a.b.c`, `server.local.port`)

---

## 📦 Installation

Install with `pip` or `pip3`:

```bash
pip install dotpaw
```

---

## 🧾 Example `.paw` file

```
app.name: MyWebsite
app.debug: true [bool]
app.port: 8080 [int]

db.host: localhost
db.port: 5432 [int]

list.values: 1, 2, 3
```

---

## 🚀 Usage

```python
from dotpaw import load, get

config = load("config.paw")

print(config["app"]["name"])
print(get("app.port", config))
```

---

## 💬 Comments

All comments are prefixed by Java-like `//` (double frontslash):

```
// This is a comment.

i.love: dotpaw // Another comment.
```

---

## 🔧 Type Casting

You can force types using square brackets:

```
value.int: 10 [int]
value.float: 3.14 [float]
value.bool: true [bool]
```

Supported types:

* `str`, `int`, `float`, `bool`, `none`
* `list`, `tuple`, `set`, `dict`
* `bytes`, `complex`, `range`

---

## 🌍 Environment Overrides

Environment variables override config values automatically:

```bash
export APP_PORT=9000
```

```
app.port: 8080
```

→ Result: `9000` (does not change)

---

## 🔁 Merge Multiple Files

```python
from dotpaw import multi

config = multi([
    "base.paw",
    "dev.paw"
])
```

---

## 📤 Export to Environment

```python
from dotpaw import env

env("config.paw")
```

---

## 💾 Save Config

```python
from dotpaw import save

save("output.paw", config)
```

---

## 📜 License

Licensed under the MIT License. Check `LICENSE` file.

<small>Copyright (c) 2026 Subhrajit Sain | https://anw.is-a.dev</small>
