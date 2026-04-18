import ast
import os
import re

# (Dot) Paw configuration file format
# Extension: .paw
# By Subhrajit Sain, aka ANW (https://anw.is-a.dev)
# v1.0

def cast(item, forced_type: str) -> str | int | float | bool | None | list | tuple | set | dict | bytes | complex | range:
    """Casts a forced datatype to a value"""
    if forced_type == 'str':
        return str(item)
    elif forced_type == 'int':
        return int(float(item))
    elif forced_type == 'float':
        return float(item)
    elif forced_type == 'bool':
        return item.lower() in ('true', '1', 'yes', 'on')
    elif forced_type == 'none':
        return None
    elif forced_type in ('list', 'tuple', 'set', 'dict'):
        try:
            parsed = ast.literal_eval(item)
        except Exception:
            def auto_cast(x):
                if x.lower() == 'true': return True
                if x.lower() == 'false': return False
                if x.isdigit(): return int(x)
                try: return float(x)
                except: return x
            parsed = [auto_cast(x.strip()) for x in item.split(',')]
        if forced_type == 'list':
            return list(parsed) if not isinstance(parsed, list) else parsed
        elif forced_type == 'tuple':
            return tuple(parsed)
        elif forced_type == 'set':
            return set(parsed)
        elif forced_type == 'dict':
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Invalid dict format")
    elif forced_type == 'bytes':
        return bytes(item, 'utf-8')
    elif forced_type == 'complex':
        return complex(item)
    elif forced_type == 'range':
        parts = [int(x) for x in item.split(':')]
        if not 1 <= len(parts) <= 3:
            raise ValueError("range expects 1-3 args")
        return range(*parts)
    return item

def load(filepath: str, use_env_overrides: bool = True) -> dict:
    """Parses a .paw file and returns as dict"""
    config = {}
    if not filepath.endswith(".paw"):
        raise ValueError(f"DotPaw filename must end with '.paw', got {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"DotPaw file {filepath} not found")

    cast_re = re.compile(r"^(.*)\s*\[\s*(\w+)\s*\]$")

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//') or ':' not in line:
                continue

            path, raw_val = line.split(':', 1)
            path, raw_val = path.strip(), raw_val.strip()

            match = cast_re.match(raw_val)
            global_type = None

            if match:
                raw_val, global_type = match.groups()
                raw_val = raw_val.strip()

            env_key = path.replace('.', '_').upper()
            if use_env_overrides and env_key in os.environ:
                env_val = os.environ[env_key]
                if global_type:
                    raw_val = f"{env_val} [{global_type}]"
                else:
                    raw_val = env_val

            def smart_split(val: str):
                items, current, depth = [], "", 0
                for ch in val:
                    if ch in "[({":
                        depth += 1
                    elif ch in "])}":
                        depth = max(0, depth - 1)
                    if ch == ',' and depth == 0:
                        items.append(current.strip())
                        current = ""
                    else:
                        current += ch
                if current:
                    items.append(current.strip())
                return items

            raw_items = smart_split(raw_val)
            processed_items = []

            for item in raw_items:
                item = re.sub(r'\$(?:(\w+)|\{(\w+)\})', lambda m: os.getenv(m.group(1) or m.group(2), m.group(0)), item)

                match = cast_re.match(item)
                forced_type, val = None, item
                if match:
                    item, forced_type = match.groups()
                    item = item.strip()

                try:
                    ftype = forced_type or global_type

                    if ftype:
                        val = cast(item, ftype)
                    else:
                        if item.lower() == 'true':
                            val = True
                        elif item.lower() == 'false':
                            val = False
                        elif item.endswith('.') or (item.startswith('.') and item != '.0'):
                            val = str(item)
                        elif item == '.0':
                            val = 0.0
                        elif item.replace('.', '', 1).isdigit() and '.' in item:
                            val = float(item)
                        elif item.isdigit():
                            val = int(item)
                        elif item.startswith(('{', '[', '(')) and item.endswith(('}', ']', ')')):
                            try:
                                parsed = ast.literal_eval(item)
                                if isinstance(parsed, (list, tuple, set, dict)):
                                    val = parsed
                                else:
                                    val = str(item)
                            except Exception:
                                val = str(item)
                        else:
                            val = str(item)
                except ValueError as e:
                    raise ValueError(f"Failed to parse '{item}': {e}")

                processed_items.append(val)

            if global_type:
                final_val = processed_items[0] if len(processed_items) == 1 else processed_items
            elif len(processed_items) > 1:
                final_val = processed_items
            else:
                final_val = processed_items[0]

            keys = path.split('.')
            current = config
            for i, key in enumerate(keys):
                if i == len(keys) - 1:
                    current[key] = final_val
                else:
                    current = current.setdefault(key, {})
    return config

def merge(base_dict: dict, override_dict: dict) -> dict:
    """Deeply merges two dictionaries and returns dict"""
    for key, value in override_dict.items():
        if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
            merge(base_dict[key], value)
        else:
            base_dict[key] = value
    return base_dict

def multi(filepaths: list[str], use_env_overrides: bool = True) -> dict:
    """Merges multiple .paw files in sequence and returns as dict"""
    final_config = {}
    for path in filepaths:
        if not path.endswith(".paw"):
            raise ValueError(f"DotPaw filename must end with '.paw', got {path}")
        new_config = load(path, use_env_overrides=use_env_overrides)
        final_config = merge(final_config, new_config)
    return final_config

def get(path: str, config_dict: dict, default = None) -> str | int | float | bool | None | list | tuple | set | dict | bytes | complex | range:
    """Gets a value via dot notation with a safe default"""
    keys = path.split('.')
    current = config_dict
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default

def env(filepath: str) -> None:
    """Injects .paw values into os.environ with error handling"""
    if not filepath.endswith(".paw"):
        raise ValueError(f"DotPaw filename must end with '.paw', got {filepath}")
    config = load(filepath)
    def flatten(d, prefix=""):
        for k, v in d.items():
            key = f"{prefix}_{k}".upper() if prefix else k.upper()
            if isinstance(v, dict): flatten(v, key)
            else:
                try: os.environ[key] = str(v)
                except (OSError, PermissionError): pass
    flatten(config)

def save(filepath: str, config_dict: dict, prefix: str = "") -> None:
    """Saves a nested dict back to a .paw file"""
    if not filepath.endswith(".paw"):
        raise ValueError(f"DotPaw filename must end with '.paw', got {filepath}")
    with open(filepath, 'w') as f:
        def write(d, prefix=""):
            for k, v in d.items():
                key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    write(v, key)
                elif isinstance(v, list):
                    f.write(f"{key}: {', '.join(map(str, v))}\n")
                else:
                    f.write(f"{key}: {v}\n")
        write(config_dict)