import threading
import pygame
import sys
import os
import time

from client.client import ChessClientSocket
from client.gui import ChessGUI
from lobby_menu import LobbyMenu
from common.message import Message
from player_id_screen import PlayerIDScreen

class ChessClient:
    def __init__(self):
        self.socket = ChessClientSocket()
        self.player_id = None
        self.game_id = None
        self.color = None
        self.gui = None
        self.is_spectator = False
        self.running = True
        self.message_thread = None
        self.chat_thread = None

    def start(self):
        # Initialize pygame first
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Multiplayer Chess")

        # Show connecting message
        font = pygame.font.Font(None, 36)
        screen.fill((255, 255, 255))
        connecting_text = font.render("Connecting to server...", True, (0, 0, 0))
        screen.blit(connecting_text, (screen.get_width() // 2 - connecting_text.get_width() // 2,
                                     screen.get_height() // 2 - connecting_text.get_height() // 2))
        pygame.display.flip()

        # Try to connect to the server
        self.socket.connect()
        if not self.socket.connected:
            # Show error message
            screen.fill((255, 255, 255))
            error_text = font.render("Failed to connect to the server!", True, (255, 0, 0))
            error_text2 = font.render("Make sure the server is running.", True, (0, 0, 0))
            error_text3 = font.render("Press any key to exit...", True, (0, 0, 0))

            screen.blit(error_text, (screen.get_width() // 2 - error_text.get_width() // 2,
                                    screen.get_height() // 2 - 50))
            screen.blit(error_text2, (screen.get_width() // 2 - error_text2.get_width() // 2,
                                     screen.get_height() // 2))
            screen.blit(error_text3, (screen.get_width() // 2 - error_text3.get_width() // 2,
                                     screen.get_height() // 2 + 50))
            pygame.display.flip()

            # Wait for key press
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                        waiting = False

            pygame.quit()
            sys.exit(1)

        # Show player ID input screen
        player_id_screen = PlayerIDScreen(screen)
        self.player_id = player_id_screen.run()

        if not self.player_id:
            print("No player ID entered. Exiting...")
            self.shutdown()
            return

        # Start message and chat threads
        self.message_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.chat_thread = threading.Thread(target=self.receive_chat, daemon=True)
        self.message_thread.start()
        self.chat_thread.start()

        # Show lobby menu
        pygame.display.set_caption("Chess Lobby")
        lobby_menu = LobbyMenu(self, screen, 800, 600)
        action = lobby_menu.run()

        if action == "QUIT":
            self.shutdown()
            return
        elif action == "NEW_GAME":
            print("Joining lobby...")
            self.join_lobby()
        elif action == "JOIN":
            self.game_id = lobby_menu.get_selected_game()
            print(f"Joining game {self.game_id}")
            self.join_lobby()
        elif action == "SPECTATE":
            self.game_id = lobby_menu.get_selected_game()
            self.is_spectator = True
            print(f"Spectating game {self.game_id}")
            self.spectate_game()

        # Check if the connection is still active after lobby actions
        if not self.socket.connected:
            print("Connection lost after lobby action. Exiting...")
            self.shutdown()
            return

        # Proceed to game GUI if connection is still active
        if not self.is_spectator:
            self.gui = ChessGUI(self)
            self.gui.run()
        else:
            self.gui = ChessGUI(self)
            self.gui.run()

        # Clean up after GUI exits
        self.shutdown()

    def join_lobby(self):
        if not self.socket.connected:
            print("Cannot join lobby: Not connected to server")
            return
        message = Message("JOIN_LOBBY", {"player_id": self.player_id})
        self.socket.send_message(message)

    def spectate_game(self):
        if not self.socket.connected:
            print("Cannot spectate game: Not connected to server")
            return
        message = Message("SPECTATE", {"game_id": self.game_id})
        self.socket.send_message(message)

    def receive_messages(self):
        while self.running and self.socket.connected:
            try:
                message = self.socket.receive()
                if not message:
                    print("Connection to server lost.")
                    self.socket.connected = False
                    self.running = False
                    if self.gui:
                        self.gui.shutdown()
                    break
                print(f"Received message: {message.type}")
                if message.type == "WAITING":
                    print(message.data["message"])
                elif message.type == "GAME_START" or message.type == "SPECTATE_START":
                    self.game_id = message.data["game_id"]
                    if not self.is_spectator:
                        self.color = message.data["color"]
                        print(f"Game started! You are {self.color}")
                    else:
                        print(f"Spectating game {self.game_id}")
                    if self.gui:
                        self.gui.update_board(message.data["board"])
                elif message.type == "GAME_UPDATE":
                    if self.gui:
                        self.gui.update_board(message.data["board"])
                        if message.data["game_over"]:
                            winner = message.data["winner"]
                            print(f"Game Over! Winner: {winner}")
                            self.gui.show_game_over(winner)
                elif message.type == "INVALID_MOVE":
                    print(message.data["message"])
                elif message.type == "ERROR":
                    print(message.data["message"])
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.socket.connected = False
                self.running = False
                if self.gui:
                    self.gui.shutdown()
                break
        print("Message thread stopped.")

    def receive_chat(self):
        while self.running and self.socket.connected:
            try:
                message = self.socket.receive_chat()
                if not message:
                    print("Chat connection closed.")
                    self.socket.connected = False
                    self.running = False
                    break
                print(f"Received chat message: {message.type}")
                if message.type == "CHAT":
                    print(f"Chat: {message.data['message']}")
                    if self.gui:
                        # Extract timestamp if available, otherwise use current time
                        timestamp = message.data.get("timestamp", time.time())
                        print(f"Received message with timestamp: {timestamp}")  # Debug print
                        self.gui.display_chat(message.data["message"], timestamp)
            except Exception as e:
                print(f"Error receiving chat: {e}")
                self.socket.connected = False
                self.running = False
                break
        print("Chat thread stopped.")

    def send_move(self, move):
        if not self.is_spectator and self.socket.connected:
            message = Message("MOVE", {"move": move})
            self.socket.send_message(message)
        else:
            print("Cannot send move: Not connected or in spectator mode")

    def send_chat(self, message_text, timestamp=None):
        if self.socket.connected:
            if timestamp is None:
                timestamp = time.time()

            # Timestamp will be used by the GUI to display the time

            # Include timestamp in the message data
            message = Message("CHAT", {
                "game_id": self.game_id,
                "message": f"{self.player_id}: {message_text}",
                "timestamp": timestamp
            })
            self.socket.send_chat(message)
        else:
            print("Cannot send chat: Not connected to server")

    def shutdown(self):
        if not self.running:
            return  # Prevent multiple shutdown calls
        self.running = False
        # Wait for threads to exit
        if self.message_thread and self.message_thread.is_alive():
            self.message_thread.join(timeout=1.0)
        if self.chat_thread and self.chat_thread.is_alive():
            self.chat_thread.join(timeout=1.0)
        self.socket.close()
        if self.gui:
            self.gui.shutdown()
        pygame.quit()
        print("Client shutdown complete.")
        sys.exit(0)

def start_client():
    client = ChessClient()
    client.start()
