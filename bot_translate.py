import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import discord
import requests
from langdetect import detect
import json
import datetime

# 環境変数から取得
Discord_Token = os.getenv("Discord_Token")
DeepL_Token = os.getenv("Deepl_Token")

# 動作指定チャンネル（数値で記入）
# Discord_channel_ID = 123456789012345678  

Intents = discord.Intents.default()
Intents.message_content = True
client = discord.Client(intents=Intents)

# Bot の動作状態を管理
bot_active = True

# カスタムHTTPハンドラー
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_data = {
            "status": "alive",
            "bot_status": "active" if bot_active else "inactive",
            "timestamp": datetime.datetime.now().isoformat(),
            "message": "Discord Translator Bot is running"
        }
        
        self.wfile.write(json.dumps(response_data).encode())
        print(f"Keep-alive GET received at {datetime.datetime.now()}")
    
    def do_POST(self):
        # POSTリクエストも適切に処理
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    print(f"Received POST data: {data}")
                except:
                    print(f"Non-JSON POST data received: {post_data.decode('utf-8', errors='ignore')}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                "status": "received",
                "bot_status": "active" if bot_active else "inactive",
                "timestamp": datetime.datetime.now().isoformat(),
                "message": "POST request processed"
            }
            
            self.wfile.write(json.dumps(response_data).encode())
            print(f"Keep-alive POST received at {datetime.datetime.now()}")
            
        except Exception as e:
            print(f"POST処理エラー: {e}")
            self.send_error(400, f"Bad Request: {e}")
    
    def do_HEAD(self):
        # HEADリクエストにも対応
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        print(f"Keep-alive HEAD received at {datetime.datetime.now()}")
    
    def log_message(self, format, *args):
        # ログを簡潔にする（必要に応じてコメントアウト）
        return

# 言語判別関数
def language(text):
    lang = detect(text)
    return lang

# 起動時動作
@client.event
async def on_ready():
    print("起動しました")

# 翻訳関連動作
@client.event
async def on_message(message):
    global bot_active
    
    # 指定チャンネル以外からのメッセージは無視
    # if message.channel.id != Discord_channel_ID:
    #     return
    
    # Bot自身のメッセージは無視
    if message.author == client.user:
        return
    
    # Bot停止コマンド
    if message.content.startswith("おやすみ"):
        bot_active = False
        await message.channel.send("翻訳機能を停止しました💤\n「おはよう」で再開できます。")
        return
    
    # Bot再開コマンド
    if message.content.startswith("おはよう"):
        bot_active = True
        await message.channel.send("翻訳機能を再開しました！☀️")
        return
    
    # Bot状態確認コマンド
    if message.content.startswith("状態"):
        status = "動作中" if bot_active else "停止中"
        await message.channel.send(f"翻訳Bot状態: {status}")
        return
    
    # ヘルプコマンド
    if message.content.startswith("ヘルプ") or message.content.startswith("help"):
        help_text = """
**翻訳Bot コマンド一覧**
• `おやすみ` - 翻訳機能を停止
• `おはよう` - 翻訳機能を再開
• `状態` - 現在の動作状態を確認
• `完全終了` - botを完全終了（管理者のみ）
• `ヘルプ` - このメッセージを表示

通常のメッセージは自動で翻訳されます（日本語↔英語）
        """
        await message.channel.send(help_text)
        return
    
    # Bot完全終了コマンド（管理者用）
    if message.content.startswith("完全終了"):
        await message.channel.send("botを完全終了します。再起動にはサーバーの再起動が必要です。")
        await client.close()
        exit()
    
    # 翻訳機能が無効な場合は処理しない
    if not bot_active:
        return
    
    # 翻訳処理
    DeepL_API_URL = "https://api-free.deepl.com/v2/translate"
    
    try:
        # 言語を自動判定する
        source_lang = language(message.content)
        if source_lang == "ja":
            target_lang = "EN"
        else:
            target_lang = "JA"
        
        params = {
            "auth_key": DeepL_Token,
            "text": message.content,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        
        response = requests.post(DeepL_API_URL, data=params)
        
        # HTTPリクエストが成功した場合
        if response.status_code == 200:
            response_json = response.json()
            translated_text = response_json["translations"][0]["text"]
            await message.channel.send(translated_text)
        else:
            print(f"DeepL API エラー: {response.status_code}")
            
    except Exception as e:
        print(f"翻訳エラー: {e}")

def run_fake_server():
    port = int(os.environ.get("PORT", 10000))  # Render が割り当てる PORT を取得
    
    server = HTTPServer(("", port), KeepAliveHandler)
    print(f"Keep-alive server running on port {port}")
    server.serve_forever()

# Keep-alive function for free hosting (改良版)
def keep_alive():
    import time
    import requests
    
    app_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not app_url:
        print("RENDER_EXTERNAL_URL not set, skipping internal keep-alive")
        return
    
    def ping():
        while True:
            try:
                response = requests.get(app_url, timeout=30)
                if response.status_code == 200:
                    print(f"Internal keep-alive successful: {datetime.datetime.now()}")
                else:
                    print(f"Keep-alive warning: status {response.status_code}")
            except Exception as e:
                print(f"Keep-alive error: {e}")
            time.sleep(600)  # 10分ごとに内部ping（GASと併用で重複を避ける）
    
    threading.Thread(target=ping, daemon=True).start()

# Bot の処理を別スレッドで動かす
threading.Thread(target=run_fake_server, daemon=True).start()
keep_alive()  # Keep-alive機能を開始

# Bot起動（エラーハンドリング付き）
async def main():
    while True:
        try:
            await client.start(Discord_Token)
        except discord.ConnectionClosed:
            print("Connection closed, attempting to reconnect...")
            await client.close()
        except Exception as e:
            print(f"Unexpected error: {e}")
            await client.close()
        
        # 5秒待ってから再接続を試行
        import asyncio
        await asyncio.sleep(5)

# 非同期実行
if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        # 通常の起動方法にフォールバック
        client.run(Discord_Token)
