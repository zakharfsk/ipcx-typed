<div align="center">

# ipcx-typed


[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ipcx-typed?logo=python&logoColor=white&label=Python)](https://pypi.org/project/ipcx-typed/)
[![CodeQL](https://github.com/zakharfsk/ipcx-typed/actions/workflows/codeql.yml/badge.svg)](https://github.com/zakharfsk/ipcx-typed/actions/workflows/codeql.yml)
[![Tests](https://github.com/zakharfsk/ipcx-typed/actions/workflows/test.yml/badge.svg)](https://github.com/zakharfsk/ipcx-typed/actions/workflows/test.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/ipcx-typed?logo=pypi&logoColor=3775A9&label=PyPi%20Version)](https://pypi.org/project/ipcx-typed/)
[![License](https://img.shields.io/github/license/zakharfsk/ipcx-typed)](LICENSE)

<h3>A powerful, type-safe inter-process communication library for Python with type safety</h3>

</div>

## 🌟 Features

- ✨ Simple and intuitive API for IPC communication
- 🔒 Type-safe request/response handling with Pydantic models
- 🪶 Lightweight and efficient
- 📦 Efficient data serialization
- 🔌 Easy integration with any Python application

## 📦 Installation

Choose your preferred installation method:

```bash
# Using pip (recommended)
pip install ipcx-typed

# Using poetry
poetry add ipcx-typed

# Using pipenv
pipenv install ipcx-typed
```

### Requirements

- Python 3.9 or higher
- aiohttp >= 3.11.16
- pydantic >= 2.11.3

## 🚀 Quick Start

Here's a minimal example to get you started:

```python
from pydantic import BaseModel
from ipcx import Server, Client

# Define your data model
class Message(BaseModel):
    content: str

# Server
async def run_server():
    server = Server(host="localhost", port=8080)
    
    @server.route(param_model=Message, return_model=Message)
    async def echo(request: Message) -> Message:
        return Message(content=f"Echo: {request.content}")
    
    await server.start()

# Client
async def run_client():
    client = Client(host="localhost", port=8080)
    response = await client.request(
        "echo",
        Message(content="Hello, World!"),
        Message
    )
    print(response.content)  # Output: Echo: Hello, World!
```

### Basic Usage

Here's a simple calculator example demonstrating the usage of ipcx:

```python
from pydantic import BaseModel
from ipcx import Server, Client
from typing import List

# Define your data models
class AddRequest(BaseModel):
    numbers: List[float]

class AddResponse(BaseModel):
    sum: float

# Server
async def run_server():
    server = Server(host="localhost", port=8080)
    
    @server.route(param_model=AddRequest, return_model=AddResponse)
    async def add(request: AddRequest) -> AddResponse:
        result = sum(request.numbers)
        return AddResponse(sum=result)
    
    await server.start()

# Client
async def run_client():
    client = Client(host="localhost", port=8080)
    
    # Make a request
    numbers = [1.5, 2.5, 3.5, 4.5]
    response = await client.request(
        "add",
        AddRequest(numbers=numbers),
        AddResponse
    )
    print(f"Sum: {response.sum}")  # Output: Sum: 12.0
```

### Advanced Usage

### Type-Safe Routes with Pydantic

```python
from pydantic import BaseModel

class StatsRequest(BaseModel):
    numbers: List[float]

class StatsResponse(BaseModel):
    min: float
    max: float
    average: float

@server.route(param_model=StatsRequest, return_model=StatsResponse)
async def stats(request: StatsRequest) -> StatsResponse:
    if not request.numbers:
        raise ValueError("Empty list provided")
    
    return StatsResponse(
        min=min(request.numbers),
        max=max(request.numbers),
        average=sum(request.numbers) / len(request.numbers)
    )
```

### Error Handling

```python
try:
    response = await client.request("stats", StatsRequest(numbers=[]), StatsResponse)
except Exception as e:
    print(f"Error: {e}")
```

### Example Use Cases

1. **Microservices Architecture**
   - Communication between different service components
   - Load balancing and service discovery

2. **Distributed Computing**
   - Task distribution and result collection
   - Worker pool management

3. **Application Integration**
   - Connecting different parts of your application
   - Plugin systems and extensions

4. **Real-time Data Processing**
   - Stream processing
   - Event-driven architectures

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 💬 Support

Need help? Here are some ways to get support:

- 🐛 Found a bug? [Open an issue](https://github.com/zakharfsk/ipcx-typed/issues)
- 💡 Have a feature request? [Submit it here](https://github.com/zakharfsk/ipcx-typed/issues)
- 💌 Contact: [Create a discussion](https://github.com/zakharfsk/ipcx-typed/discussions)

## 🔗 Links

- [GitHub Repository](https://github.com/zakharfsk/ipcx-typed)
- [PyPI Package](https://pypi.org/project/ipcx-typed/)
- [Issue Tracker](https://github.com/zakharfsk/ipcx-typed/issues)
