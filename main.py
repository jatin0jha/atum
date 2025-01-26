from http.server import BaseHTTPRequestHandler
import yt_dlp
import json
from urllib.parse import parse_qs, urlparse

def search_songs(query):
    opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            # Add "music" to the query to prioritize songs
            entries = ydl.extract_info(f"ytsearch20:music {query}", download=False).get('entries', [])
            return [{"title": v['title'], "video_id": v['id'], "thumbnail": f"https://img.youtube.com/vi/{v['id']}/hqdefault.jpg"} for v in entries]
        except Exception as e:
            print("Error during search:", e)
            return None

def get_stream_url(video_id):
    opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return {"title": info['title'], "audio_url": info['url']} if info else None
        except Exception as e:
            print("Error during stream fetch:", e)
            return None

def handler(event, context):
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    
    if method == 'GET':
        if path == '/':
            path = '/index.html'
        try:
            with open(f".{path}", "rb") as file:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'text/html' if path.endswith('.html') else
                                      'text/css' if path.endswith('.css') else
                                      'application/javascript' if path.endswith('.js') else
                                      'application/octet-stream'
                    },
                    'body': file.read().decode('utf-8')
                }
        except FileNotFoundError:
            return {'statusCode': 404, 'body': 'File Not Found'}

    elif method == 'POST':
        try:
            body = json.loads(event.get('body', '{}'))
            
            if path == '/search':
                query = body.get('query')
                if not query:
                    return {'statusCode': 400, 'body': 'Invalid query'}
                
                results = search_songs(query)
                if results:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps(results)
                    }
                return {'statusCode': 500, 'body': 'Failed to find songs'}

            elif path == '/stream':
                video_id = body.get('video_id')
                if not video_id:
                    return {'statusCode': 400, 'body': 'Invalid video ID'}
                
                stream_data = get_stream_url(video_id)
                if stream_data:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps(stream_data)
                    }
                return {'statusCode': 500, 'body': 'Failed to fetch stream URL'}

        except Exception as e:
            return {'statusCode': 500, 'body': str(e)}

    return {'statusCode': 404, 'body': 'Endpoint not found'}
