from pyngrok import ngrok

def start_tunnel(port):
    http_tunnel = ngrok.connect(proto='http', addr=port)
    return http_tunnel.public_url

def close_tunnel(public_url):
    ngrok.disconnect(public_url)
    ngrok.kill()