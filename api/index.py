import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import yt_dlp

PORT = 8000

class MusicRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.path = "/index.html" if self.path == "/" else self.path
        try:
            with open(self.path.lstrip("/"), "rb") as file:
                self.send_response(200)
                self.send_header("Content-Type", self.get_mime_type(self.path))
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        if self.path == "/search":
            self.handle_search(post_data.get("query"))
        elif self.path == "/stream":
            self.handle_stream(post_data.get("video_id"))
        else:
            self.send_error(404, "Endpoint not found")

    def handle_search(self, query):
        if not query:
            self.send_error(400, "Invalid query")
            return
        results = self.search_songs(query)
        if results:
            self.respond_json(results)
        else:
            self.send_error(500, "Failed to find songs")

    def handle_stream(self, video_id):
        if not video_id:
            self.send_error(400, "Invalid video ID")
            return
        stream_data = self.get_stream_url(video_id)
        if stream_data:
            self.respond_json(stream_data)
        else:
            self.send_error(500, "Failed to fetch stream URL")

    def search_songs(self, query):
        opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'extract_flat': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                entries = ydl.extract_info(f"ytsearch20:{query}", download=False).get('entries', [])
                return [{"title": v['title'], "video_id": v['id'], "thumbnail": f"https://img.youtube.com/vi/{v['id']}/hqdefault.jpg"} for v in entries]
            except Exception as e:
                print("Error during search:", e)
                return None

    def get_stream_url(self, video_id):
        opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return {"title": info['title'], "audio_url": info['url']} if info else None
            except Exception as e:
                print("Error during stream fetch:", e)
                return None

    def get_mime_type(self, path):
        return ("text/html" if path.endswith(".html") else 
                "text/css" if path.endswith(".css") else 
                "application/javascript" if path.endswith(".js") else 
                "application/octet-stream")

    def respond_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def run_server():
    print(f"Server running on http://localhost:{PORT}")
    HTTPServer(('localhost', PORT), MusicRequestHandler).serve_forever()

if __name__ == "__main__":
    run_server()