import socket
import threading
import protocol as proto

HOST = "0.0.0.0"
PORT = 5555

clients = {}
clients_lock = threading.Lock()

rooms = {"lobby": []}
rooms_lock = threading.Lock()


def broadcast(command, text, include: list, exclude=None):
    payload = text.encode("utf-8")
    targets= []
    with clients_lock:
        for client_sock, client_name in clients.items():
            if client_sock != exclude and client_name in include:
                targets.append(client_sock)
    for sock in targets:
        try:
            proto.send_message(sock, command, payload)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


def handle_client(sock, addr):
    username = None
    room = None

    try:
        first = proto.recv_message(sock)
        if first is None or first[0] != "JOIN":
            proto.send_message(sock, "ERRO", b"first command must be JOIN")
            return

        username, room_name = first[1].decode("utf-8", errors="replace").strip().split("_")
        room = room_name
        with clients_lock:
            if not username or username in clients.values():
                proto.send_message(sock, "ERRO", b"invalid or taken username")
                return
            clients[sock] = username

        with rooms_lock:
            if room_name in rooms:
                rooms[room_name].append(username)
            else:
                rooms[room_name] = [username]

        proto.send_message(sock, "TEXT", f"* вы вошли как {username}".encode())
        broadcast("TEXT", f"* {username} присоединился", include=rooms[room_name], exclude=sock)
        print(f"[+] {username} присоединился ({addr})")

        while True:
            msg = proto.recv_message(sock)
            if msg is None:
                print(f"[i] {username} отключился без QUIT")
                break

            command, payload = msg
            if command == "TEXT":
                text = payload.decode("utf-8", errors="replace")
                broadcast("TEXT", f"{username}: {text}", include=rooms[room_name], exclude=sock)
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
                if room_name == 'lobby':
                    proto.send_message(sock, "ERRO", "эту комнату нельзя удалить".encode())
                else:
                    with rooms_lock:
                        for user in rooms[room_name]:
                            rooms['lobby'].append(user)
                        old_room = rooms[room_name]
                        del rooms[room_name]
                    broadcast("TEXT", "* вы были перемещены в комнату lobby", include=old_room)
                    print(f"[-] {room_name} была удалена. Список доступных комнат: {', '.join(rooms)}")
            elif command == "ROOM":
                room_name = payload.decode("utf-8", errors="replace")
                with rooms_lock:
                    if room is not None:
                        rooms[room].remove(username)
                    if payload in rooms:
                        rooms[room_name].append(username)
                    else:
                        rooms[room_name] = [username]
                room = room_name
                print(f"[*] {username} перешёл в комнату {room}")
                proto.send_message(sock, "TEXT", f"* вы теперь в комнате {room}".encode())
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
        if username and room:
            broadcast("TEXT", f"* {username} покинул чат", include=rooms[room])


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
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
