import socket
import threading
import protocol as proto

HOST = "0.0.0.0"
PORT = 5555

clients = {}
clients_lock = threading.Lock()

rooms = {'main': []}
rooms_lock = threading.Lock()


def broadcast(command, text, room: str, exclude=None):
    payload = text.encode("utf-8")

    with rooms_lock:
        members = rooms[room]

    with clients_lock:
        targets = [s for s in clients if s is not exclude and s in members]

    for sock in targets:
        try:
            proto.send_message(sock, command, payload)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


def handle_client(sock, addr):
    username = None
    room  = 'main'

    try:
        first = proto.recv_message(sock)
        if first is None or first[0] != "JOIN":
            proto.send_message(sock, "ERRO", b"first command must be JOIN")
            return

        username = first[1].decode("utf-8", errors="replace").strip()
        with clients_lock:
            if not username or username in clients.values():
                proto.send_message(sock, "ERRO", b"invalid or taken username")
                return
            clients[sock] = username

        with rooms_lock:
            rooms[room].append(sock)

        proto.send_message(sock, "TEXT", f"* вы вошли как {username}".encode())
        broadcast("TEXT", f"* {username} присоединился", room, exclude=sock)
        print(f"[+] {username} присоединился ({addr})")

        while True:
            msg = proto.recv_message(sock)
            if msg is None:
                print(f"[i] {username} отключился без QUIT")
                break

            command, payload = msg
            if command == "TEXT":
                text = payload.decode("utf-8", errors="replace")
                broadcast("TEXT", f"{username}: {text}", room, exclude=sock)
            elif command == "LIST":
                with clients_lock:
                    names = list(clients.values())
                proto.send_message(sock, "LIST", "\n".join(names).encode())
            elif command == "QUIT":
                proto.send_message(sock, "TEXT", b"* bye")
                print(f"[-] {username} вышел через QUIT")
                break
            elif command == "DELR":
                room_name = payload.decode("utf-8", errors="replace")
                if room_name == 'main':
                    proto.send_message(sock, "ERRO", f"Основную комнату main удалить нельзя".encode())
                else:
                    with rooms_lock:
                        if room_name in rooms:
                            if rooms[room_name]:
                                proto.send_message(sock, "ERRO", f"комната {room_name} содержит участников".encode())
                            else:
                                del rooms[room_name]
                                proto.send_message(sock, "TEXT", f"* комната {room_name} была удалена".encode())
                        else:
                            proto.send_message(sock, "ERRO", f"комната {room_name} не существует".encode())

            elif command == "ROOM":
                room_name = payload.decode("utf-8", errors="replace")
                with rooms_lock:
                    if room_name in rooms:
                        rooms[room_name].append(sock)
                        rooms[room].remove(sock)
                    else:
                        rooms[room_name] = [sock]

                broadcast("TEXT", f"* {username} покинул комнату", room, exclude=sock)
                room = room_name
                broadcast("TEXT", f"* {username} присоединился", room, exclude=sock)
                proto.send_message(sock, "TEXT", f"* вы зашли в комнату {room}".encode())
                print(f"[i] {username} перешёл в комнату {room}")
                with rooms_lock:
                    room_names = list(rooms.keys())
                print(f"[i] доступные комнаты: {', '.join(room_names)}")
            else:
                proto.send_message(sock, "ERRO", f"unknown command {command}".encode())

    except ConnectionResetError:
        print(f"[!] {username or addr} - соединение сброшено (RST)")
    except BrokenPipeError:
        print(f"[!] {username or addr} - не удалось отправить, соединение разорвано")
    finally:
        with clients_lock:
            clients.pop(sock, None)
        sock.close()
        if username:
            broadcast("TEXT", f"* {username} покинул чат", room)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] сервер слушает {HOST}:{PORT}")
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] сервер остановлен")
