"""Launch the zero-dependency Travel Ops Agent Web Demo UI."""
import argparse

from travel_agent.web_demo import serve


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Travel Ops Agent Web Demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    serve(host=args.host, port=args.port)
