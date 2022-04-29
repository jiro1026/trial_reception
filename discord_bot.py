import os
import sys
import json
import configparser
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), './lib'))

import discord
from discord.ext import commands, tasks

import auto_web

# 設定ファイル関連（環境変数の方がいい気もするけどめんどくさいのでiniファイル）
config_ini = configparser.ConfigParser()
config_ini_path = "config.ini"
# 設定ファイル存在チェック
if not os.path.exists(config_ini_path):
    # 存在しない場合はエラーで終了
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), config_ini_path)
# 設定ファイル読み込み
config_ini.read(config_ini_path, encoding='utf-8')
TOKEN = config_ini['DEFAULT']['Token']
bot = commands.Bot(command_prefix='cmd')
file_name_list = [
    "cs-info_kanto.json"
    ,"cs-info_kinki.json"
    ,"cs-info_kyusyu.json"
    ,"cs-info_shikoku.json"
    ,"cs-info_tohoku.json"
    ,"cs-info_tyubu.json"
    ,"cs-info_tyugoku.json"
]
category_dict = {
    "kanto": "関東地方",
    "kinki": "近畿地方",
    "kyusyu": "九州地方",
    "shikoku": "四国地方",
    "tohoku": "北海道・東北地方",
    "tyubu": "中部地方",
    "tyugoku": "中国地方",
}
cs_info_dict = {}
today_cs_info = {}

# #bot起動完了時に実行される処理
@bot.event
async def on_ready():
    global cs_info_dict
    global today_cs_info
    now = datetime.datetime.now()
    for file_name in file_name_list:
        if os.path.exists("./cs-info/" + file_name):
            with open("./cs-info/" + file_name, "r") as f:
                today_cs_info_temp = {}
                cs_info = json.loads(f.read())
                cs_info_dict[file_name.split("_")[1].split(".")[0]] = cs_info
                for cs_info_item in cs_info.get(now.strftime("%Y/%m/%d"), []):
                    notice_datetime = None
                    if cs_info_item["reception_time"].startswith("24:"):
                        notice_datetime = datetime.datetime.strptime(cs_info_item["reception_date"] + " 00:" + cs_info_item["reception_time"].split(":")[1], "%Y/%m/%d %H:%M") + datetime.timedelta(days=1, minutes=-5)
                    else:
                        notice_datetime = datetime.datetime.strptime(cs_info_item["reception_date"] + " " + cs_info_item["reception_time"], "%Y/%m/%d %H:%M") + datetime.timedelta(minutes=-5)
                    if notice_datetime.strftime("%H:%M") in today_cs_info.keys():
                        if file_name.split("_")[1].split(".")[0] in today_cs_info[notice_datetime.strftime("%H:%M")].keys():
                            today_cs_info[notice_datetime.strftime("%H:%M")][file_name.split("_")[1].split(".")[0]].append(cs_info_item)
                        else:
                            today_cs_info[notice_datetime.strftime("%H:%M")][file_name.split("_")[1].split(".")[0]] = [cs_info_item]
                    else:
                        today_cs_info[notice_datetime.strftime("%H:%M")] = {
                            file_name.split("_")[1].split(".")[0]: [cs_info_item]
                        }
        
@bot.command()
async def update(ctx, *args):
    """
    手動実行用更新処理
    Args:
        ctx (_type_): _description_
    """
    global cs_info_dict
    global today_cs_info
    guild = ctx.guild
    categories = guild.categories
    now = datetime.datetime.now()
    
    await ctx.send("まずはCS情報更新を更新します。")

    auto_web.main()
    for file_name in file_name_list:
        with open("./cs-info/" + file_name, "r") as f:
            today_cs_info_temp = {}
            cs_info = json.loads(f.read())
            cs_info_dict[file_name.split("_")[1].split(".")[0]] = cs_info
            for cs_info_item in cs_info.get(now.strftime("%Y/%m/%d"), []):
                notice_datetime = None
                if cs_info_item["reception_time"].startswith("24:"):
                    notice_datetime = datetime.datetime.strptime(cs_info_item["reception_date"] + " 00:" + cs_info_item["reception_time"].split(":")[1], "%Y/%m/%d %H:%M") + datetime.timedelta(days=1, minutes=-5)
                else:
                    notice_datetime = datetime.datetime.strptime(cs_info_item["reception_date"] + " " + cs_info_item["reception_time"], "%Y/%m/%d %H:%M") + datetime.timedelta(minutes=-5)
                if notice_datetime.strftime("%H:%M") in today_cs_info.keys():
                    if file_name.split("_")[1].split(".")[0] in today_cs_info[notice_datetime.strftime("%H:%M")].keys():
                        today_cs_info[notice_datetime.strftime("%H:%M")][file_name.split("_")[1].split(".")[0]].append(cs_info_item)
                    else:
                        today_cs_info[notice_datetime.strftime("%H:%M")][file_name.split("_")[1].split(".")[0]] = [cs_info_item]
                else:
                    today_cs_info[notice_datetime.strftime("%H:%M")] = {
                        file_name.split("_")[1].split(".")[0]: [cs_info_item]
                    }
            
    await ctx.send("CS情報更新完了。カテゴリー関連を再生成します。")
    
    for category in categories:
        if category.name not in category_dict.values():
            continue
        for text_channel in category.text_channels:
            await text_channel.delete()
        await category.delete()
    
    for local_name in category_dict.keys():
        category = await guild.create_category(category_dict[local_name])
        await category.create_text_channel("通知用")
        for str_date in sorted(cs_info_dict.get(local_name, {}).keys()):
            date_item = str_date.split("/")
            category_name = date_item[1] + "月" + date_item[2] + "日"
            text_channel = await category.create_text_channel(category_name)
            await text_channel.send("==============================")
            for item in cs_info_dict[local_name][str_date]:
                await text_channel.send("大会名：" + item["event_name"] + "\n地域：" + item["prefecture"] + "\nフォーマット：" + item["format"] + "\n参加表明開始時刻：" + item["reception_time"] + "\n" + item["url"])
                await text_channel.send("==============================")
    await ctx.send("更新が終わりました。")
    
@bot.command()
async def update_category_only(ctx, *args):
    """_summary_
    手動実行用Discordのカテゴリー系の更新
    Args:
        ctx (_type_): _description_
    """
    global cs_info_dict
    guild = ctx.guild
    categories = guild.categories
    now = datetime.datetime().now()
    
    await ctx.send("カテゴリー関係のみの更新を実行します。")
    
    for category in categories:
        if category.name not in category_dict.values():
            continue
        for text_channel in category.text_channels:
            await text_channel.delete()
        await category.delete()
    
    for local_name in category_dict.keys():
        category = await guild.create_category(category_dict[local_name])
        await category.create_text_channel("通知用")
        for str_date in sorted(cs_info_dict.get(local_name, {}).keys()):
            date_item = str_date.split("/")
            category_name = date_item[1] + "月" + date_item[2] + "日"
            text_channel = await category.create_text_channel(category_name)
            await text_channel.send("==============================")
            for item in cs_info_dict[local_name][str_date]:
                await text_channel.send("大会名：" + item["event_name"] + "\n地域：" + item["prefecture"] + "\nフォーマット：" + item["format"] + "\n参加表明開始時刻：" + item["reception_time"] + "\n" + item["url"])
                await text_channel.send("==============================")
    await ctx.send("更新が終わりました。")
    
@bot.command()
async def debug(ctx, *args):
    """
    手動実行用デバッグコマンド
    中身見る用
    Args:
        ctx (_type_): _description_
    """
    print(cs_info_dict)
    print(today_cs_info)


@tasks.loop(seconds=60)
async def loop():
    """
    自動通知用の何か
    作りかけだった気がする、途中でやる気がなくなった。
    """
    global today_cs_info
    now = datetime.datetime.now()
    if now.strftime("%H:%M") in today_cs_info.keys():
        guild = bot.guilds[0]
        for local_name in today_cs_info[now.strftime("%H:%M")].keys():
            category = discord.utils.get(guild.categories, name=category_dict[local_name])
            text_channel = discord.utils.get(category.text_channels, name="通知用")
            await text_channel.send("==============================")
            for item in today_cs_info[now.strftime("%H:%M")][local_name]:
                await text_channel.send("大会名：" + item["event_name"] + "\n地域：" + item["prefecture"] + "\nフォーマット：" + item["format"] + "\n参加表明開始時刻：" + item["reception_time"] + "\n" + item["url"])
                await text_channel.send("==============================")

loop.start()

bot.run(TOKEN)