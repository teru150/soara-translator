import discord
import  requests
from langdetect import detect

Discord_Token = "Discordトークンを入力"

#動作指定チャンネル
Discord_channel_ID = チャンネルIDを入力

Intents = discord.Intents.default()
Intents.message_content = True

client = discord.Client(intents=Intents)

#言語判別関数
def language(text):
    lang = detect(text)
    return lang

#起動時動作
@client.event
async def on_ready():
    print("起動しました")

#翻訳関連動作
@client.event
async def on_message(message):
    #指定チャンネル以外からのメッセージは無視
    if message.channel.id != Discord_channel_ID:
        return

    #Bot自身のメッセージは無視
    if message.author == client.user:
        return

    #Bot終了コマンド
    if message.content.startswith("おやすみ"):
        await message.channel.send("おやすみ！また明日！")
        await client.close()
        exit()

    DeepL_Token = "DeepLトークンを入力"
    DeepL_API_URL = "https://api-free.deepl.com/v2/translate"

    #言語を自動判定する
    source_lang = language(message.content)

    if source_lang == "ja":
        target_lang = "EN"
    else:
        target_lang = "JA"

    params = {
        "auth_key" : DeepL_Token,
        "text" : message.content,
        "source_lang": source_lang,
        "target_lang": target_lang
    }

    response = requests.post(DeepL_API_URL, data=params)

    #HTTPリクエストが成功した場合
    if response.status_code == 200:
        response_json = response.json()
        translated_text = response_json["translations"][0]["text"]
        await message.channel.send(translated_text)

    #エラーメッセージ
    else:
        await message.channel.send(response.status_code)
        await message.channel.send(response.text)

client.run(Discord_Token)
