# ♟️ Multiplayer Chess Game (Python + Socket Programming)

A fully functional multiplayer chess game implemented in Python using socket programming. This project showcases a real-time client-server architecture supporting game matchmaking, live updates, chat system, and spectator mode.

## 🚀 Features

- Real-time multiplayer chess with synchronized game state
- Client-server architecture with sockets
- Matchmaking lobby system
- Turn-based management with timer control
- Spectator mode to watch ongoing games
- Integrated chat system for player communication
- Legal move validation and game-end conditions (checkmate, stalemate)

## 🧠 Learning Objectives

- Gain hands-on experience in socket programming
- Implement networking protocols in a real-time game
- Understand game state management and data synchronization
- Develop multi-client communication in Python

## 🛠 Tech Stack

- **Language**: Python
- **Networking**: `socket` module
- **Data Handling**: `json`
- **Chess Logic**: `python-chess` library (for move validation and board state)

## 🧱 System Design

### Client Responsibilities
- Connect to server
- Send/receive move data
- Display chessboard (CLI or GUI)
- Participate in game chat
- Join lobby or spectate games

### Server Responsibilities
- Accept client connections
- Match players and manage game sessions
- Validate chess moves and update board state
- Forward state updates to players and spectators
- Manage chat messages and timers

## 🔄 Data Flow

1. Client connects to server via socket
2. Client joins or creates a game in the lobby
3. Server pairs players and initializes a game
4. Players take turns making moves
5. Server validates each move and updates all clients
6. Spectators can view real-time game state
7. Chat messages are transmitted during gameplay

## 📦 Installation

```bash
git clone https://github.com/ahmadijaz02/multiplayer-chess-socket-python.git
cd multiplayer-chess-socket-python
pip install python-chess
