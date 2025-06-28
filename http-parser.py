from http.server import BaseHTTPRequestHandler, HTTPServer
import numpy as np
from datetime import datetime as dt
import os

class imageDataHandler(BaseHTTPRequestHandler):
    image_counter = 0  # Initialize class variable
    
    def do_POST(self):
        if self.path == '/upload':
            try:
                # Get content length
                content_length = int(self.headers.get('Content-Length', 0))
                
                if content_length == 0:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'No data received')
                    return
                
                # Read JPEG data
                jpeg_data = self.rfile.read(content_length)
                
                # Create from-esp directory if it doesn't exist
                os.makedirs('from-esp', exist_ok=True)
                
                # Generate filename with counter
                imageDataHandler.image_counter += 1
                filename = f"from-esp/image_{imageDataHandler.image_counter:04d}.jpg"
                
                # Save JPEG file
                with open(filename, 'wb') as f:
                    f.write(jpeg_data)
                
                print(f"Image saved: {filename} ({len(jpeg_data)} bytes)")
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Image saved successfully: {filename}'.encode())
                
            except Exception as e:
                print(f"Error handling request: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
        else:
            # Handle other paths
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        # Custom logging to show timestamp
        print(f"[{dt.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

if __name__ == "__main__":
    # Server configuration to match ESP32-CAM code
    server_address = ('172.20.10.5', 8080)  # Listen on all interfaces, port 8080
    httpd = HTTPServer(server_address, imageDataHandler)
    
    print(f"Starting HTTP server on {server_address[0]}:{server_address[1]}")
    print("Waiting for images from ESP32-CAM...")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()