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


class SimpleCore(package="simple"):



    async  def get_guild_by_id(self, id):
        guild = await self.bot.get_guild(id)
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
            ch.send(embed=message)
        else:
            ch.send(message)

    async def globanban(self, userid, duration=0):
        banlist = self.bot.db['banned']
        if userid in banlist:
            raise ValueError("User Already Banned!")
        ct = round(time.time())
        nt = ct + duration
        self.bot.db['banned'].update({f'{userid}': nt})
        return True

    async def systemmsg(self, message, room):
        await self.bot.bridge.send(room, message, 'discord', system=True)
        for platform in self.bot.config['external']:
            await self.bot.bridge.send(room, message, platform, system=True)
        return True


def genembed(text, style="default", package="getfromconfig"):
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
       if style == "success":
           embed = nextcord.Embed(
               title=f"{package}: Success",
               description=text,
               color=nextcord.Color.green(),
           )
       if style == "error":
           embed = nextcord.Embed(
               title=f"{package}: Error",
               description=text,
               color=nextcord.Color.brand_red(),
           )
       return embed

    running = True

class Simple(commands.Cog):

    def __init__(self,bot):
        self.bot = bot
        self.bot.simple = SimpleCore(self)


    @commands.command()
    async def simple(self,ctx):
        await ctx.send('Running Simple v0.0.1!')

def setup(bot):
    bot.add_cog(Simple(bot))
