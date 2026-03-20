# 🚄 SNCF MCP Server

An MCP (Model Context Protocol) server for searching French train schedules using real SNCF data (TGV, TER, Intercités).

Compatible with **any MCP client**: Claude Desktop, Cursor, GitHub Copilot, and more.

---

## Requirements

- Python 3.10+
- A free SNCF API token — register at [api.sncf.com](https://api.sncf.com)
- Authentication: HTTP Basic Auth (username = token, password = empty)

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/diegoesqui/sncf-mcp.git
cd sncf-mcp
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS / Linux
# .venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your API token

Create a `.env` file in the project root (never commit this file):

```
NAVITIA_TOKEN=your_token_here
```

Or export it directly:

```bash
export NAVITIA_TOKEN="your_token_here"
```

### 5. Start the server

```bash
python server.py
```

---

## Claude Desktop Integration

Edit the Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sncf-trains": {
      "command": "/absolute/path/to/sncf-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/sncf-mcp/server.py"],
      "env": {
        "NAVITIA_TOKEN": "your_token_here"
      }
    }
  }
}
```

Fully restart Claude Desktop (Cmd+Q on macOS). You should see a 🔧 tools icon in the chat when the server is active.

---

## Docker Deployment (Synology NAS or any server)

### Build the image

```bash
docker build -t sncf-mcp:latest .
```

### Configure the token

```bash
echo "NAVITIA_TOKEN=your_token_here" > .env
```

### Start the container

```bash
docker compose up -d
```

### Connect Claude Desktop to the container

```json
{
  "mcpServers": {
    "sncf-trains": {
      "command": "docker",
      "args": ["exec", "-i", "sncf-mcp", "python", "server.py"],
      "env": {
        "NAVITIA_TOKEN": "your_token_here"
      }
    }
  }
}
```

> **Synology DSM:** import `docker-compose.yml` directly via Container Manager → Projects.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `search_station` | Search for a French station by name, returns IDs |
| `search_trains` | Find trains between two cities on a given date and time |
| `search_trains_detailed` | Full itinerary breakdown: stops, connections, leg durations |
| `next_departures` | List all departures for a full day between two stations |

---

## Usage Examples

Once connected to Claude, just ask naturally:

```
What trains are there from Toulouse to Marseille on April 6th in the afternoon?
Show me all trains from Lyon to Paris next Thursday.
Give me the full details of the second train from Toulouse to Marseille on August 13th.
List all departures from Bordeaux to Toulouse next Tuesday.
```

---

## Project Structure

```
sncf-mcp/
├── server.py           # MCP server (tools + SNCF API client)
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Container deployment
├── .env                # API token — DO NOT commit
├── .gitignore          # Excludes .env and .venv
└── README.md           # This file
```

---

## Notes

- **Schedules are real-time** — data comes directly from SNCF via the Navitia engine
- **Prices are not available** — the free SNCF API covers schedules only, not ticketing
- The server uses **stdio transport**, the standard MCP mode for local clients
- For remote access via claude.ai web, SSE/HTTP mode would need to be added
