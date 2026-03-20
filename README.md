# 🚄 SNCF MCP Server

Servidor MCP para búsqueda de trenes en Francia (datos SNCF/TGV/TER).

Compatible con **cualquier cliente MCP**: Claude Desktop, Cursor, Copilot, etc.

---

## Setup rápido (local)

### 1. Consigue tu API key gratis

Regístrate en https://api.sncf.com — recibes el token por email.  
Autenticación: HTTP Basic Auth (usuario = token, contraseña vacía).

### 2. Entorno virtual Python (recomendado)

```bash
cd navitia-mcp
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
```

### 3. Configura el token

Crea un fichero `.env` en la carpeta (no lo subas a Git):
```
NAVITIA_TOKEN=tu_token_aquí
```

### 4. Arranca el servidor

```bash
python server.py
```

---

## Integración con Claude Desktop

Edita el fichero de configuración:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sncf-trains": {
      "command": "/ruta/absoluta/navitia-mcp/.venv/bin/python",
      "args": ["/ruta/absoluta/navitia-mcp/server.py"],
      "env": {
        "NAVITIA_TOKEN": "tu_token_aquí"
      }
    }
  }
}
```

Reinicia Claude Desktop completamente (Cmd+Q en macOS).

---

## Despliegue en Synology NAS (Docker)

### 1. Construye la imagen

```bash
docker build -t sncf-mcp:latest .
```

### 2. Crea el fichero de entorno

```bash
echo "NAVITIA_TOKEN=tu_token_aquí" > .env
```

### 3. Arranca con docker-compose

```bash
docker compose up -d
```

### 4. Conecta Claude Desktop al contenedor

```json
{
  "mcpServers": {
    "sncf-trains": {
      "command": "docker",
      "args": ["exec", "-i", "sncf-mcp", "python", "server.py"],
      "env": {
        "NAVITIA_TOKEN": "tu_token_aquí"
      }
    }
  }
}
```

> **Synology DSM:** importa el `docker-compose.yml` desde Container Manager → Projects.

---

## Tools disponibles

| Tool | Descripción |
|------|-------------|
| `search_station` | Busca estaciones por nombre, devuelve IDs |
| `search_trains` | Busca trenes entre dos ciudades en una fecha/hora |
| `search_trains_detailed` | Detalle completo: paradas, correspondencias, duración |
| `next_departures` | Lista todos los trenes de un día completo |

---

## Ejemplos de uso

```
¿Qué trenes hay de Toulouse a Marsella el 6 de abril por la tarde?
Lista todos los trenes del jueves de Lyon a París.
Dame el detalle del segundo tren de Toulouse a Marsella el 13 de agosto.
```

---

## Estructura de archivos

```
navitia-mcp/
├── server.py           # Servidor MCP principal
├── requirements.txt    # Dependencias Python
├── Dockerfile          # Imagen Docker
├── docker-compose.yml  # Despliegue en NAS/servidor
├── .env                # Token (NO subir a Git)
├── .gitignore          # Excluye .env y .venv
└── README.md           # Este fichero
```
