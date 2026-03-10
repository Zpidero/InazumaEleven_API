# Inazuma Eleven VR API

The **Inazuma Eleven VR API** is a REST API built with **FastAPI** that provides structured data about players and teams from **Inazuma Eleven: Victory Road**.

This API allows developers to access detailed information about players, including their stats, archetypes, positions, elements, teams, and more.

The data is stored in CSV files and served through multiple endpoints designed for easy querying and filtering.

---

## Features

- Get all players
- Search players by:
  - Name
  - Nickname
  - ID
  - Game
  - Team
  - Archetype
  - Position
  - Element
  - Gender
  - Role
  - Age group
- Retrieve individual player stats (Power, Control, Technique, etc.)
- Access teams and their players
- Add new players or teams via POST endpoints

---

# Technologies

- **FastAPI**
- **Python**
- **Pandas**
- **Docker**

---

## Example Endpoints

- GET /players
- GET /players/{name}
- GET /players/id/{id}
- GET /teams
- GET /elements
- GET /positions
- GET /players/{name}/power

---

## Example Response

{
  "Name": "Mark Evans",
  "Position": "Goalkeeper",
  "Element": "Wood",
  "Team": "Raimon",
  "Power": 120
}

---

## Building from Source

You can build the API yourself using **Docker**.

Build the image and then run it:

```sh
docker build -t inazuma-eleven-api:latest .
docker run -p 8000:8000 --name inazuma-api inazuma-eleven-api:latest
```

Or use **Docker Compose**:

```sh
docker compose up
```
