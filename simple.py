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
import os
import re
import subprocess


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


def install_plugin(bot, url):
    # Normalize URL
    if url.endswith('/'):
        url = url[:-1]
    if not url.endswith('.git'):
        url = url + '.git'

    # Clean up any existing plugin installation
    subprocess.run(['rm', '-rf', os.path.join(os.getcwd(), 'plugin_install')], check=True)

    # Clone the repository
    subprocess.run(['git', 'clone', url, os.path.join(os.getcwd(), 'plugin_install')], check=True)

    try:
        with open('plugin_install/plugin.json', 'r') as file:
            new = json.load(file)
        
        if not bool(re.match("^[a-z0-9_-]*$", new['id'])):
            print('Invalid plugin.json file: Plugin IDs must be alphanumeric and may only contain lowercase letters, numbers, dashes, and underscores.')
            return
        
        if f"{new['id']}.json" in os.listdir('plugins'):
            with open(f'plugins/{new["id"]}.json', 'r') as file:
                current = json.load(file)
            print(f'Plugin already installed!\n\nName: `{current["name"]}`\nVersion: `{current["version"]}`')
            return

        plugin_id = new['id']
        name = new['name']
        desc = new['description']
        version = new['version']
        minimum = new['minimum']
        modules = new['modules']
        utilities = new['utils']
        services = new.get('services', [])

        with open('plugins/system.json', 'r') as file:
            vinfo = json.load(file)

        if vinfo['release'] < minimum:
            print(f'Failed to install plugin: Your system does not support this plugin. Release `{minimum}` or later is required.')
            return

        conflicts = []
        for module in modules:
            if module in os.listdir('cogs'):
                conflicts.append('cogs/' + module)
        for util in utilities:
            if util in os.listdir('utils'):
                conflicts.append('utils/' + util)
        if f'{plugin_id}.json' in os.listdir('emojis') and 'emojis' in services:
            conflicts.append(f'emojis/{plugin_id}.json')
        if conflicts:
            print('Conflicting files were found:\n' + '\n'.join(f'\n`{conflict}`' for conflict in conflicts))
            return

        # Proceed with installation
        try:
            if 'requirements' in new:
                print('Installing dependencies')
                newdeps = new['requirements']
                if newdeps:
                    print('Installing: ' + ' '.join(newdeps))
                    subprocess.run(['python3', '-m', 'pip', 'install', '--no-dependencies'] + newdeps, check=True)

            print('Installing Plugin')
            for module in modules:
                subprocess.run(['cp', os.path.join(os.getcwd(), 'plugin_install', module), os.path.join(os.getcwd(), 'cogs', module)], check=True)
            for util in utilities:
                subprocess.run(['cp', os.path.join(os.getcwd(), 'plugin_install', util), os.path.join(os.getcwd(), 'utils', util)], check=True)

            if 'emojis' in services:
                print('Installing Emoji Pack')
                home_guild = bot.get_guild(bot.config['home_guild'])
                with open('plugin_install/emoji.json', 'r') as file:
                    emojipack = json.load(file)
                for emojiname in list(emojipack['emojis'].keys()):
                    file = os.path.join('plugin_install', 'emojis', emojipack['emojis'][emojiname][0])
                    with open(file, 'rb') as img:
                        emoji = home_guild.create_custom_emoji(name=emojiname, image=img.read())
                    emojipack['emojis'][emojiname][0] = f'<a:{emoji.name}:{emoji.id}>' if emoji.animated else f'<:{emoji.name}:{emoji.id}>'
                emojipack['installed'] = True
                with open(f'emojis/{plugin_id}.json', 'w+') as file:
                    json.dump(emojipack, file, indent=2)

            print('Registering plugin')
            subprocess.run(['cp', os.path.join(os.getcwd(), 'plugin_install', 'plugin.json'), os.path.join(os.getcwd(), 'plugins', f'{plugin_id}.json')], check=True)
            with open(f'plugins/{plugin_id}.json') as file:
                plugin_info = json.load(file)
                plugin_info.update({'repository': url})
            with open(f'plugins/{plugin_id}.json', 'w') as file:
                json.dump(plugin_info, file)

            print('Activating extensions')
            for module in modules:
                modname = 'cogs.' + module[:-3]
                bot.load_extension(modname)
            
            print('Installation complete')
        except Exception as e:
            print(f'Install failed: {e}')
            return



class Simple(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.simple = SimpleCore(bot)
        self.bot.simple.running = True
        self.bot.simple.version = [1, "v0.0.1"]

    @commands.command()
    async def simple(self, ctx):
        embed = nextcord.Embed(
            title="Simple v0.0.1",
            description="By ItsAsheer.",
            color=nextcord.Color.red()
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Simple(bot))
