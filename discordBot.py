import discord
from discord.ext import commands
import mysql.connector
import os
import requests

sqlConnection = mysql.connector.connect(
    host=os.getenv("sqlDatabaseIP"),
    user=os.getenv("sqlUsername"),
    password=os.getenv("sqlPassword"),
    database=os.getenv("sqlUsername")
)

cursor = sqlConnection.cursor()

client = commands.Bot(command_prefix = '~')

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('MC Whitelist | ~help'))
    print('Bot is ready.')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.author.send("The command you've entered is invalid. To find the list of commands, type `~help` in the Discord channel.")

@client.command()
async def add(ctx, username):
    await ctx.channel.purge(limit=1)
    cursor.execute("SELECT EXISTS(SELECT * FROM `discord` WHERE `discordID` = '%s') as ex;" % ctx.author.id)

    if cursor.fetchone()[0] == 0:
        minecraftData = requests.get(url = "https://playerdb.co/api/player/minecraft/%s" % username)
        if minecraftData.status_code == 500:
            await ctx.author.send("The Minecraft username you specified is invalid. Make sure you typed it right before retrying in the Discord channel.")
            pass
        uuid = minecraftData.json().get("data").get("player").get("id")
        cursor.execute("SELECT EXISTS(SELECT * FROM `discord` WHERE `uuid` = '%s') as ex;" % uuid)
        if cursor.fetchone()[0] == 0:
            cursor.execute("SELECT EXISTS(SELECT * FROM `whitelist` where `uuid` = '%s') as ex;" % uuid)
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO `whitelist` (`uuid`, `name`, `whitelisted`) VALUES ('%s', '%s', 'true');" % (uuid, username))
            else:
                cursor.execute("UPDATE `whitelist` SET `whitelisted` = 'true' WHERE `uuid` = '%s';" % (uuid))
            sqlConnection.commit()
            cursor.execute("INSERT INTO `discord` (`discordID`, `uuid`) VALUES ('%s', '%s');" % (ctx.author.id, uuid))
            sqlConnection.commit()
            await ctx.author.send("You have successfully whitelisted your Minecraft account!")
        else:
            await ctx.author.send("The Minecraft username you've specified has already been linked to an account.")
    else:
        await ctx.author.send("You currently already have a Minecraft account linked to your Discord account. To remove that account, please type `~remove` in the Discord channel.")

@add.error
async def clear_error(ctx, error):
    await ctx.channel.purge(limit=1)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.author.send("You have forgotten to place the username argument. To add your Minecraft account to the whitelist, type `~add (username)` in the Discord channel.")

@client.command()
async def remove(ctx):
    await ctx.channel.purge(limit=1)
    cursor.execute("SELECT EXISTS(SELECT * FROM `discord` WHERE `discordID` = '%s') as ex;" % ctx.author.id)
    if cursor.fetchone()[0] == 0:
        await ctx.author.send("You currently don't have a Minecraft account linked to your Discord account.")
    else:
        cursor.execute("SELECT * FROM `discord` WHERE `discordID` = '%s';" % ctx.author.id)
        uuid = cursor.fetchone()[2]
        cursor.execute("DELETE FROM `discord` WHERE `discordID` = '%s';" % ctx.author.id)
        sqlConnection.commit()
        cursor.execute("UPDATE `whitelist` SET `whitelisted` = 'false' where `uuid` = '%s';" % uuid);
        sqlConnection.commit()
        await ctx.author.send("You have successfully unlinked your Minecraft account.")

client.run(os.getenv("discordToken"))