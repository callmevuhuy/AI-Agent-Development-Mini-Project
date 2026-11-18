"""Launch the demo and open a browser when ready."""
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser


def main():
    try:
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        print("Cổng phải là số từ 1 đến 65535.")
        return 1
    url = f"http://127.0.0.1:{port}"
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            print(f"Cổng {port} đang được dùng hoặc không khả dụng.")
            print(f"Nếu demo đã chạy, mở {url}. Hoặc chạy: run_demo.bat 8081")
            return 1
    process = subprocess.Popen([sys.executable, "-m", "travel_agent.app", "web", "--port", str(port)])
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(120):
            if process.poll() is not None:
                return process.returncode or 1
            try:
                with opener.open(url, timeout=0.5) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.25)
        else:
            print("Server chưa sẵn sàng. Xem thông báo phía trên.")
            return 1
        print(f"Demo: {url}\nNhấn Ctrl+C để dừng.", flush=True)
        webbrowser.open(url)
        return process.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
