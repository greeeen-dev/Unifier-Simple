"""
Simple - A simple plugin to make dev life easier.
Copyright (C) 2024 ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import nextcord
from nextcord.ext import commands
import time
import json


class SimpleCore:
    def __init__(self, bot):
        self.bot = bot

    async def get_guild_by_id(self, id):
        guild = self.bot.get_guild(id)
        return guild

    async def user_has_role(self, user_id, role_id, guild_id):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return False

        user = guild.get_member(user_id)
        if user is None:
            return False

        role = nextcord.utils.get(guild.roles, id=role_id)
        if role is None:
            return False

        return role in user.roles

    async def channellog(self, message, is_embed=False):
        guild = self.bot.get_guild(self.bot.config['home_guild'])
        ch = guild.get_channel(self.bot.config['logs_channel'])
        if is_embed:
            await ch.send(embed=message)
        else:
            await ch.send(message)

    async def global_ban(self, user_id, duration=0):
        banlist = self.bot.db['banned']
        if user_id in banlist:
            raise ValueError("User Already Banned!")
        current_time = round(time.time())
        end_time = current_time + duration
        self.bot.db['banned'].update({str(user_id): end_time})
        return True

    async def system_message(self, message, room):
        await self.bot.bridge.send(room, message, 'discord', system=True)
        for platform in self.bot.config['external']:
            await self.bot.bridge.send(room, message, platform, system=True)
        return True


def gen_embed(text, style="default", package="getfromconfig"):
    with open('config.json', 'r') as file:
        data = json.load(file)
    if package == "getfromconfig":
        package = data['package']
        package = package.title()
    if style == "default":
        embed = nextcord.Embed(
            title=f"{package}",
            description=text,
            color=nextcord.Color.blurple(),
        )
    elif style == "success":
        embed = nextcord.Embed(
            title=f"{package}: Success",
            description=text,
            color=nextcord.Color.green(),
        )
    elif style == "error":
        embed = nextcord.Embed(
            title=f"{package}: Error",
            description=text,
            color=nextcord.Color.red(),
        )
    return embed


class Simple(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.simple = SimpleCore(bot)
        self.bot.simple.running = True
        self.bot.simple.version = [1, "v0.0.1"]

    @commands.command()
    async def simple(self, ctx):
        await ctx.send('Running Simple v0.0.1!')


def setup(bot):
    bot.add_cog(Simple(bot))
