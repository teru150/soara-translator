import discord
import random

Discord_Token = "Discordトークンを入力"
admin_ID = 管理者IDを入力

Intents = discord.Intents.default()
Intents.message_content = True

client = discord.Client(intents=Intents)

#乱数を生成
def rand():
    dice = random.randint(1, 100)
    return dice

@client.event
async def on_ready():
    print("起動しました")

@client.event
async def on_message(message):
    #Bot自身のメッセージは無視
    if message.author == client.user:
        return
      
    if message.content.startswith("!dice"):
        dice = rand()
        await message.channel.send(f"ダイスの目は「{dice}」です。")
    
    #シャットダウンコマンド
    if message.content.startswith("おやすみ"):
        #管理者なら実行する    
        if message.author.id == admin_ID:
            await message.channel.send("おやすみ！また明日！")
            await client.close()
            exit()
        else:
            await message.channel.send("このコマンドは管理者のみ実行可能です")

client.run(Discord_Token)
