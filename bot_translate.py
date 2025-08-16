import threading
import os
from http.server import SimpleHTTPRequestHandler
import socketserver
import discord
import requests
from langdetect import detect

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
    handler = SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Fake server running on port {port}")
        httpd.serve_forever()

# Bot の処理を別スレッドで動かす
threading.Thread(target=run_fake_server, daemon=True).start()

# Bot起動
client.run(Discord_Token)
