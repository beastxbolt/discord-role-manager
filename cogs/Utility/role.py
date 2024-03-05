import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui
from typing import Literal
from sqlite3 import connect
from discord import Colour
from checkslashrole import check_slash_role
import yaml
from discord import Colour, TextStyle
from checkslashrole import check_slash_role
from discord.ui import TextInput, Modal
import datetime
import random
import json

db = connect('./database.db', check_same_thread = False)
cursor = db.cursor()

class role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        async def saved_roles(self, guild, member, user_roles):
            result = cursor.execute(f"SELECT channel_id FROM role_persistence_logs_channel WHERE guild_id = {guild.id}").fetchone()
            if result is not None:
                roles = ""
                if len(user_roles) > 0 and '' not in user_roles:
                    for role_id in user_roles:
                        try:
                            roles += guild.get_role(int(role_id)).mention + ", "
                        except:
                            continue
                    roles = roles[:len(roles) - 2]

                    embed = discord.Embed(description=f"{member.mention}'s Roles Have Been Saved.\nRoles saved:\n{roles}", color=0x7575fc)
                    try:
                        channel = guild.get_channel(result[0])
                        await channel.send(embed=embed)
                        return True
                    except discord.NotFound:
                        return False
                return False
            else:
                return False

        async def db_update_roles(self, interaction, check_role):
            for member in interaction.guild.members:

                if check_role not in member.roles:
                    continue

                result = cursor.execute(f"SELECT role_id FROM role_persistence_monitored_roles WHERE guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    roles_id_list = list(result[0].split(", "))

                    user_roles_name = ""
                    for role in member.roles:
                        if str(role.id) in roles_id_list:
                            user_roles_name += str(role.name) + ", "
                        else:
                            continue
                    user_roles_name = user_roles_name[:len(user_roles_name) - 2]

                    user_roles_id = ""
                    for role in member.roles:
                        if str(role.id) in roles_id_list:
                            user_roles_id += str(role.id) + ", "
                        else:
                            continue
                    user_roles_id = user_roles_id[:len(user_roles_id) - 2]

                    user_roles_id_in_monitored_list = list(user_roles_id.split(", "))

                    result = cursor.execute(f"SELECT role_id FROM role_persistence WHERE guild_id = {interaction.guild_id} AND user_id = {member.id}").fetchone()
                    if result is not None:
                        check_save_status = cursor.execute(f"SELECT is_save_role FROM role_persistence WHERE guild_id = {interaction.guild_id} AND user_id = {member.id}").fetchone()
                        if check_save_status is not None and check_save_status[0] == "True":
                            user_roles_in_db = list(result[0].split(", "))
                            if user_roles_id_in_monitored_list != user_roles_in_db:
                                if len(user_roles_id) == 0:
                                    cursor.execute("DELETE FROM role_persistence WHERE guild_id = ? AND user_id = ?", (interaction.guild_id, member.id,))
                                    db.commit()
                                else:
                                    cursor.execute("UPDATE role_persistence SET rolename = ?, role_id = ? WHERE guild_id = ? AND user_id = ?", (user_roles_name, user_roles_id, interaction.guild_id, member.id))
                                    db.commit()
                                await self.saved_roles(interaction.guild, member, user_roles_id_in_monitored_list)
                            else:
                                continue
                        else:
                            continue
                    else:
                        cursor.execute("INSERT INTO role_persistence (guild_id, username, user_id, rolename, role_id, is_save_role) VALUES (?,?,?,?,?,?)", (interaction.guild_id, str(member), member.id, user_roles_name, user_roles_id, "True"))
                        db.commit()
                        await self.saved_roles(interaction.guild, member, user_roles_id_in_monitored_list)
                else:
                    try:
                        cursor.execute("DELETE FROM role_persistence WHERE guild_id = ? AND user_id = ?", (interaction.guild_id, member.id,))
                        db.commit()
                    except:
                        pass
                    continue

        @app_commands.guild_only()
        class role(app_commands.Group):
            persistence = app_commands.Group(name="persistence", description="Sub group of role group.")
            linking = app_commands.Group(name="linking", description="Sub group of role group.")
            message = app_commands.Group(name="message", description="Sub group of role group.")
            
            @persistence.command(description="Adds persisted roles")
            async def add(self, interaction: Interaction, role: discord.Role):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return

                result = cursor.execute(f"SELECT role_id, role_name FROM role_persistence_monitored_roles WHERE guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    roles_id_list = list(result[0].split(", "))
                    roles_name_list = list(result[1].split(", "))

                    if str(role.id) in roles_id_list:
                        await interaction.response.send_message(f"{role.mention} is already added to the list.", ephemeral=True)
                    else:
                        roles_id_list.append(str(role.id))
                        new_roles_id = ""
                        for role_id in roles_id_list:
                            new_roles_id += role_id + ", "
                        new_roles_id = new_roles_id[:len(new_roles_id) - 2]

                        roles_name_list.append(role.name)
                        new_roles_name = ""
                        for role_name in roles_name_list:
                            new_roles_name += role_name + ", "
                        new_roles_name = new_roles_name[:len(new_roles_name) - 2]

                        cursor.execute("UPDATE role_persistence_monitored_roles SET role_id = ?, role_name = ? WHERE guild_id = ?", (new_roles_id, new_roles_name, interaction.guild_id))
                        db.commit()
                        await interaction.response.send_message(f"{role.mention} role has been added to the list.", ephemeral=True)
                        await self.db_update_roles(interaction, role)
                else:
                    new_roles_id = str(role.id)
                    new_roles_name = role.name
                    cursor.execute("INSERT INTO role_persistence_monitored_roles (guild_id, role_id, role_name) VALUES (?,?,?)", (interaction.guild_id, new_roles_id, new_roles_name))
                    db.commit()
                    await interaction.response.send_message(f"{role.mention} role has been added to the list.", ephemeral=True)
                    await self.db_update_roles(interaction, role)


            @persistence.command(description="Remove persisted roles")
            async def remove(self, interaction: Interaction, role: discord.Role):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return

                result = cursor.execute(f"SELECT role_id, role_name FROM role_persistence_monitored_roles WHERE guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    roles_id_list = list(result[0].split(", "))
                    roles_name_list = list(result[1].split(", "))

                    if str(role.id) not in roles_id_list:
                        await interaction.response.send_message(f"{role.mention} is NOT added to the list.", ephemeral=True)
                    else:
                        role_name_to_remove = roles_id_list.index(str(role.id))
                        roles_id_list.remove(str(role.id))
                        roles_name_list.pop(role_name_to_remove)
                        if not bool(roles_id_list) is False:
                            new_roles_id = ""
                            for role_id in roles_id_list:
                                new_roles_id += role_id + ", "
                            new_roles_id = new_roles_id[:len(new_roles_id) - 2]

                            new_roles_name = ""
                            for role_name in roles_name_list:
                                new_roles_name += role_name + ", "
                            new_roles_name = new_roles_name[:len(new_roles_name) - 2]

                            cursor.execute("UPDATE role_persistence_monitored_roles SET role_id = ?, role_name = ? WHERE guild_id = ?", (new_roles_id, new_roles_name, interaction.guild_id))
                            db.commit()
                        else:
                            cursor.execute("DELETE FROM role_persistence_monitored_roles WHERE guild_id = ?", (interaction.guild_id,))
                            db.commit()
                        await interaction.response.send_message(f"{role.mention} role has been removed from the list.", ephemeral=True)
                        await self.db_update_roles(interaction, role)
                else:
                    await interaction.response.send_message(f"{role.mention} role is NOT added to the list.", ephemeral=True)

            @persistence.command(description="Lists all persisted roles")
            async def list(self, interaction: Interaction):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return
                
                result = cursor.execute(f"SELECT role_id FROM role_persistence_monitored_roles WHERE guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    roles_id_list = list(result[0].split(", "))
                    roles = ""
                    for role_id in roles_id_list:
                        try:
                            roles += interaction.guild.get_role(int(role_id)).mention + ", "
                        except:
                            continue
                    roles = roles[:len(roles) - 2]

                    if roles == "":
                        cursor.execute("DELETE FROM role_persistence_monitored_roles WHERE guild_id = ?", (interaction.guild_id,))
                        db.commit()
                        await interaction.response.send_message("No role has been added to the list.", ephemeral=True)
                    else:
                        embed = discord.Embed(description=f"Roles added to list -\n{roles}", color=0x7575fc)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("No role has been added to the list.", ephemeral=True)


            @persistence.command(description="Sets the channel to log all roles saved and restored")
            async def logs(self, interaction: Interaction, channel: discord.TextChannel):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return
                    
                result = cursor.execute(f"SELECT channel_id FROM role_persistence_logs_channel WHERE guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    cursor.execute("UPDATE role_persistence_logs_channel SET channel_id = ?, channel_name = ? WHERE guild_id = ?", (channel.id, channel.name, interaction.guild_id))
                    db.commit()
                    await interaction.response.send_message(f"{channel.mention} has been set as the logs channel.", ephemeral=True)
                else:
                    cursor.execute("INSERT INTO role_persistence_logs_channel (guild_id, channel_id, channel_name) VALUES (?,?,?)", (interaction.guild_id, channel.id, channel.name))
                    db.commit()
                    await interaction.response.send_message(f"{channel.mention} has been set as the logs channel.", ephemeral=True)



            @linking.command(description="Links a role based on it being added or removed")
            async def add(self, interaction: Interaction, watched_role: discord.Role, rolelink_type: Literal["add", "remove"], role: discord.Role, role_action: Literal["add", "remove"]):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return

                rolelink_type = rolelink_type.lower().strip()
                if rolelink_type == "add" or rolelink_type == "remove":
                    pass
                else:
                    await interaction.response.send_message(f"Invalid rolelink type entered. It should be either ``add`` or ``remove``.", ephemeral=True)
                    return

                if role_action == "add" or role_action == "remove":
                    pass
                else:
                    await interaction.response.send_message(f"Invalid role action type entered. It should be either ``add`` or ``remove``.", ephemeral=True)
                    return

                result = cursor.execute(f"SELECT role_to_watch FROM rolelink_roles WHERE role_to_watch = {watched_role.id} AND rolelink_type = '{rolelink_type}' AND guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    await interaction.response.send_message(f"{watched_role.mention} already has a role link role linked with role link type ``{rolelink_type}``.", ephemeral=True)
                else:
                    cursor.execute("INSERT INTO rolelink_roles (guild_id, role_to_watch, role_to_watch_name, rolelink_type, role, role_name, role_action) VALUES (?,?,?,?,?,?,?)", (interaction.guild_id, watched_role.id, watched_role.name, rolelink_type, role.id, role.name, role_action))
                    db.commit()
                    await interaction.response.send_message(f"Role link Added!\n``{role_action}`` action will be performed on {role.mention} when ``{rolelink_type}`` action will be done on {watched_role.mention}.", ephemeral=True)

            @linking.command(description="Removes a linked role from the server")
            async def remove(self, interaction: Interaction, watched_role: discord.Role, rolelink_type: Literal["add", "remove"]):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return

                rolelink_type = rolelink_type.lower().strip()
                if rolelink_type == "add" or rolelink_type == "remove":
                    pass
                else:
                    await interaction.response.send_message(f"Invalid rolelink type entered. It should be either ``add`` or ``remove``.", ephemeral=True)
                    return

                result = cursor.execute(f"SELECT role_to_watch FROM rolelink_roles WHERE role_to_watch = {watched_role.id} AND rolelink_type = '{rolelink_type}' AND guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    cursor.execute("DELETE FROM rolelink_roles WHERE role_to_watch = ? AND rolelink_type = ? AND guild_id = ?", (watched_role.id, rolelink_type, interaction.guild_id,))
                    db.commit()
                    await interaction.response.send_message(f"{watched_role.mention}'s rolelink with rolelink type ``{rolelink_type}`` has been removed.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"{watched_role.mention} doesn't have a rolelink with rolelink type ``{rolelink_type}`` linked.", ephemeral=True)

            @linking.command(description="Shows all the available role links in the server")
            async def list(self, interaction: Interaction):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return
                
                result = cursor.execute(f"SELECT role_to_watch, role, rolelink_type, role_action FROM rolelink_roles WHERE guild_id = {interaction.guild_id}").fetchall()
                if len(result) != 0:
                    roles = ""
                    i = 1
                    for x in result:
                        try:
                            roles += f"**{i}.** {interaction.guild.get_role(x[0]).mention} ({x[2]}) -> {interaction.guild.get_role(x[1]).mention} ({x[3]})\n"
                            i += 1
                        except:
                            cursor.execute("DELETE FROM rolelink_roles WHERE role_to_watch = ? AND rolelink_type = ? AND guild_id = ?", (x[0], x[2], interaction.guild_id,))
                            db.commit()
                            continue

                    embed = discord.Embed(description=f"Rolelinks :-\n{roles}", color=0x7575fc)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(description=f"There are no rolelinks in the server.", color=0x7575fc)
                    await interaction.response.send_message(embed=embed, ephemeral=True)



            @message.command(description="Create a role messages")
            async def create(self, interaction: Interaction, method: Literal["form", "json"], channel: discord.TextChannel, role1: discord.Role, role2: discord.Role = None, role3: discord.Role = None, role4: discord.Role = None, role5: discord.Role = None):

                try:
                    if await check_slash_role(interaction, cursor) is True:
                        pass
                    else:
                        await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                        return

                    method = method.lower().strip()
                    if method == "form" or method == "json":
                        pass
                    else:
                        await interaction.response.send_message("Invalid create method defined.", ephemeral=True)
                        return

                    all_roles = []
                    all_roles.append(role1)
                    if role2 is not None:
                        all_roles.append(role2)
                    if role3 is not None:
                        all_roles.append(role3)
                    if role4 is not None:
                        all_roles.append(role4)
                    if role5 is not None:
                        all_roles.append(role5)

                    new_roles_id = ""
                    for role in all_roles:
                        new_roles_id += str(role.id) + ", "
                    new_roles_id = new_roles_id[:len(new_roles_id) - 2]

                    added_roles = ""
                    for role in all_roles:
                        added_roles += role.mention + ", "
                    added_roles = added_roles[:len(added_roles) - 2]

                    if method == "form":
                        class RoleMSG(ui.Modal, title='Role Message'):
                            title_input = TextInput(label="Title", placeholder="Enter title here", style=TextStyle.short, max_length=256, required=True)
                            description_input = TextInput(label="Description", placeholder="Enter description here", style=TextStyle.long, max_length=4000, required=False)
                            color_input = TextInput(label="Color", placeholder="Enter color hex here including #", style=TextStyle.short, max_length=7, required = False)
                            footer_text_input = TextInput(label="Footer Text", placeholder="Enter footer text here", style=TextStyle.short, required=False)
                            image_url_input = TextInput(label="Image URL", placeholder="Enter image url here", style=TextStyle.short, required=False)

                            async def on_submit(self, interaction: discord.Interaction):
                                title = str(self.title_input)
                                description_input = str(self.description_input)
                                color_input = str(self.color_input)
                                footer_text_input = str(self.footer_text_input)
                                image_url_input = str(self.image_url_input)

                                id = random.randrange(10000000, 9999999999)

                                if description_input is None or description_input == '':
                                    description = ''
                                else:
                                    description = description_input

                                if color_input is None or color_input == '':
                                    color = ''
                                else:
                                    try:
                                        color = str(int(hex(int(color_input.replace("#", ""), 16)), 0))
                                    except:
                                        await interaction.response.send_message("Invalid color hex entered.", ephemeral=True)
                                        return

                                if footer_text_input is None or footer_text_input == '':
                                    footer_text = ''
                                else:
                                    footer_text = footer_text_input

                                if image_url_input is None or image_url_input == '':
                                    image_url = ''
                                else:
                                    image_url = image_url_input

                                cursor.execute("INSERT INTO role_embed_msg (id, guild_id, title, description, color, footer_text, image_url, role_id, channel_id, channel_name) VALUES (?,?,?,?,?,?,?,?,?,?)", (id, interaction.guild_id, title, description, color, footer_text, image_url, new_roles_id, channel.id, channel.name))
                                db.commit()
                                embed = discord.Embed(description=f"Embed saved with the ID: ``{id}``\nRoles added -> {added_roles}\nTo edit embed info use ``/role message edit`` slash command.", color=0x7575fc)
                                await interaction.response.send_message(embed=embed, ephemeral=True)

                            async def on_error(self, interaction: Interaction):
                                await interaction.response.send_message("An error occured. Please check your input.", ephemeral=True)
                                return
                            
                            async def on_timeout(self, interaction: Interaction):
                                await interaction.response.send_message("You took too long to respond.", ephemeral=True)
                                return

                        await interaction.response.send_modal(RoleMSG())

                    if method == "json":
                        class EmbedWithJSON(ui.Modal, title='Embed Builder: Create with JSON'):
                            raw_json_input = TextInput(label="Raw JSON", placeholder="Enter raw json here", style=TextStyle.long, max_length=4000, required=True)

                            async def on_submit(self, interaction: discord.Interaction):
                                raw_json = str(self.raw_json_input)
                                try:
                                    data = json.loads(raw_json)
                                except:
                                    await interaction.response.send_message("An error occured. Please check your raw json data.", ephemeral=True)
                                    return
                                try:
                                    title = data['title']
                                except:
                                    title = ''
                                try:
                                    description = data['description']
                                except:
                                    description = ''
                                try:
                                    color = data['color']
                                except:
                                    color = ''
                                try:
                                    footer_text = data['footer']['text']
                                except:
                                    footer_text = ''
                                try:
                                    image_url = data['image']['url']
                                except:
                                    image_url = ''
                                try:
                                    author_name = data['author']['name']
                                except:
                                    author_name = ''
                                try:
                                    author_icon_url = data['author']['icon_url']
                                except:
                                    author_icon_url = ''
                                try:
                                    author_url = data['author']['url']
                                except:
                                    author_url = ''
                                try:
                                    footer_icon_url = data['footer']['icon_url']
                                except:
                                    footer_icon_url = ''
                                try:
                                    thumbnail_url = data['thumbnail']['url']
                                except:
                                    thumbnail_url = ''
                                try:
                                    field_names = ""
                                    for x in data['fields']:
                                        field_names += x["name"] + ", "
                                    field_names = field_names[:len(field_names) - 2]
                                except:
                                    field_names = ''
                                try:
                                    field_values = ""
                                    for x in data['fields']:
                                        field_values += x["value"] + ", "
                                    field_values = field_values[:len(field_values) - 2]
                                except:
                                    field_values = ''
                                id = random.randrange(10000000, 9999999999)

                                cursor.execute("INSERT INTO role_embed_msg (id, guild_id, title, description, color, footer_text, image_url, author_name, author_url, author_icon_url, footer_icon_url, thumbnail_url, field_names, field_values, role_id, channel_id, channel_name, raw_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (id, interaction.guild_id, title, description, color, footer_text, image_url, author_name, author_url, author_icon_url, footer_icon_url, thumbnail_url, field_names, field_values, new_roles_id, channel.id, channel.name, raw_json))
                                db.commit()
                                embed = discord.Embed(description=f"Embed saved with the ID: ``{id}``\nRoles added -> {added_roles}\nTo edit embed info use ``/role message edit`` slash command.", color=0x7575fc)
                                await interaction.response.send_message(embed=embed, ephemeral=True)

                            async def on_error(self, interaction: Interaction):
                                await interaction.response.send_message("An error occured. Please check your input.", ephemeral=True)
                                return
                            
                            async def on_timeout(self, interaction: Interaction):
                                await interaction.response.send_message("You took too long to respond.", ephemeral=True)
                                return

                        await interaction.response.send_modal(EmbedWithJSON())
                except Exception as e:
                    print(e)


            @message.command(description="Edits a role message")
            async def edit(self, interaction: Interaction, method: Literal["form", "json"], id: int, channel: discord.TextChannel = None, roles_action: Literal["add", "remove"] = None, role1: discord.Role = None, role2: discord.Role = None, role3: discord.Role = None, role4: discord.Role = None, role5: discord.Role = None):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return

                method = method.lower().strip()
                if method == "form" or method == "json":
                    pass
                else:
                    await interaction.response.send_message("Invalid edit method defined.", ephemeral=True)
                    return

                if roles_action is not None:
                    roles_action = roles_action.lower().strip()
                    if roles_action == "add" or roles_action == "remove":
                        pass
                    else:
                        await interaction.response.send_message("Invalid roles action defined.", ephemeral=True)
                        return

                    if role1 is None:
                        await interaction.response.send_message("You need to a choose atleast 1 role.", ephemeral=True)
                        return

                all_roles = []
                all_roles.append(role1)
                if role2 is not None:
                    all_roles.append(role2)
                if role3 is not None:
                    all_roles.append(role3)
                if role4 is not None:
                    all_roles.append(role4)
                if role5 is not None:
                    all_roles.append(role5)

                result = cursor.execute(f"SELECT title FROM role_embed_msg WHERE id = {id} AND guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    result = cursor.execute(f"SELECT title, description, color, footer_text, image_url, author_name, author_icon_url, author_url, footer_icon_url, thumbnail_url, field_names, field_values, role_id, channel_id, channel_name, raw_json FROM role_embed_msg WHERE id = {id} AND guild_id = {interaction.guild_id}").fetchone()
                    roles_id_list = list(result[12].split(", "))

                    if channel is None:
                        channel_id = result[13]
                        channel_name = result[14]
                    else:
                        channel_id = channel.id
                        channel_name = channel.name

                    if roles_action is None:
                        new_roles_id = result[12]

                    else:
                        if roles_action == "add":
                            for role in all_roles:
                                if str(role.id) in roles_id_list:
                                    continue
                                else:
                                    roles_id_list.append(str(role.id))
                                    if roles_id_list[0] == "":
                                        roles_id_list.pop(0)

                                    new_roles_id = ""
                                    for role_id in roles_id_list:
                                        new_roles_id += role_id + ", "
                                    new_roles_id = new_roles_id[:len(new_roles_id) - 2]

                            added_roles = ""
                            for role in roles_id_list:
                                added_roles += interaction.guild.get_role(int(role)).mention + ", "
                            added_roles = added_roles[:len(added_roles) - 2]

                        if roles_action == "remove":
                            removed_roles_list = []
                            for role in all_roles:
                                if str(role.id) in roles_id_list:
                                    roles_id_list.remove(str(role.id))
                                    removed_roles_list.append(str(role.id))

                            if not bool(roles_id_list) is False:
                                new_roles_id = ""
                                for role_id in roles_id_list:
                                    new_roles_id += role_id + ", "
                                new_roles_id = new_roles_id[:len(new_roles_id) - 2]
                            else:
                                new_roles_id = ""

                            removed_roles = ""
                            for role_id in removed_roles_list:
                                try:
                                    removed_roles += interaction.guild.get_role(int(role_id)).mention + ", "
                                except:
                                    continue
                            removed_roles = removed_roles[:len(removed_roles) - 2]

                    if method == "form":
                        try:
                            class EditEmbedForm(ui.Modal, title='Embed Builder: Edit embed details'):
                                title_input = TextInput(label="Title", placeholder="Enter title here", style=TextStyle.short, default=result[0], max_length=256, required=True)
                                description_input = TextInput(label="Description", placeholder="Enter description here", style=TextStyle.long, default=result[1], max_length=4000, required=False)
                                if result[2] is None or result[2] == '':
                                    color_input = TextInput(label="Color", placeholder="Enter color hex here including #", style=TextStyle.short, default="", max_length=7, required = False)
                                else:
                                    color_input = TextInput(label="Color", placeholder="Enter color hex here including #", style=TextStyle.short, default=f"#{hex(int(result[2]))}", max_length=7, required = False)
                                footer_text_input = TextInput(label="Footer Text", placeholder="Enter footer text here", style=TextStyle.short, default=result[3], required=False)
                                image_url_input = TextInput(label="Image URL", placeholder="Enter image url here", style=TextStyle.short, default=result[4], required=False)

                                async def on_submit(self, interaction: Interaction):
                                    title = str(self.title_input)
                                    description_input = str(self.description_input)
                                    color_input = str(self.color_input)
                                    footer_text_input = str(self.footer_text_input)
                                    image_url_input = str(self.image_url_input)

                                    if description_input is None or description_input == '':
                                        description = ''
                                    else:
                                        description = description_input

                                    if color_input is None or color_input == '':
                                        color = ''
                                    else:
                                        try:
                                            color = str(int(hex(int(color_input.replace("#", ""), 16)), 0))
                                        except:
                                            await interaction.response.send_message("Invalid color hex entered.", ephemeral=True)
                                            return

                                    if footer_text_input is None or footer_text_input == '':
                                        footer_text = ''
                                    else:
                                        footer_text = footer_text_input

                                    if image_url_input is None or image_url_input == '':
                                        image_url = ''
                                    else:
                                        image_url = image_url_input

                                    cursor.execute("UPDATE role_embed_msg SET title = ?, description = ?, color = ?, footer_text = ?, image_url = ?, role_id = ?, channel_id = ?, channel_name = ? WHERE id = ? AND guild_id = ?", (title, description, color, footer_text, image_url, new_roles_id, channel_id, channel_name, id, interaction.guild_id))
                                    db.commit()
                                    if roles_action is None:
                                        embed = discord.Embed(description=f"Embed updated with the ID: ``{id}``", color=0x7575fc)
                                    else:
                                        if roles_action == "add":
                                            embed = discord.Embed(description=f"Embed updated with the ID: ``{id}``\nRoles added -> {added_roles}", color=0x7575fc)
                                        if roles_action == "remove":
                                            embed = discord.Embed(description=f"Embed updated with the ID: ``{id}``\nRoles removed -> {removed_roles}", color=0x7575fc)
                                    await interaction.response.send_message(embed=embed, ephemeral=True)

                                async def on_error(self, interaction: Interaction):
                                    await interaction.response.send_message("An error occured. Please check your input.", ephemeral=True)
                                    return
                                
                                async def on_timeout(self, interaction: Interaction):
                                    await interaction.response.send_message("You took too long to respond.", ephemeral=True)
                                    return

                            await interaction.response.send_modal(EditEmbedForm())
                            return
                        except Exception as e:
                            print(e)

                    if method == "json":
                        class EditEmbedJSON(ui.Modal, title='Embed Builder: Edit with JSON'):
                            raw_json_input = TextInput(label="Raw JSON", placeholder="Enter raw json here", style=TextStyle.long, default=result[15], max_length=4000, required=True)

                            async def on_submit(self, interaction: discord.Interaction):
                                raw_json = str(self.raw_json_input)
                                try:
                                    data = json.loads(raw_json)
                                except:
                                    await interaction.response.send_message("An error occured. Please check your raw json data.", ephemeral=True)
                                    return
                                try:
                                    title = data['title']
                                except:
                                    await interaction.response.send_message("Title is required.", ephemeral=True)
                                    return
                                try:
                                    description = data['description']
                                except:
                                    description = ''
                                try:
                                    color = data['color']
                                except:
                                    color = ''
                                try:
                                    footer_text = data['footer']['text']
                                except:
                                    footer_text = ''
                                try:
                                    image_url = data['image']['url']
                                except:
                                    image_url = ''
                                try:
                                    author_name = data['author']['name']
                                except:
                                    author_name = ''
                                try:
                                    author_icon_url = data['author']['icon_url']
                                except:
                                    author_icon_url = ''
                                try:
                                    author_url = data['author']['url']
                                except:
                                    author_url = ''
                                try:
                                    footer_icon_url = data['footer']['icon_url']
                                except:
                                    footer_icon_url = ''
                                try:
                                    thumbnail_url = data['thumbnail']['url']
                                except:
                                    thumbnail_url = ''
                                try:
                                    field_names = ""
                                    for x in data['fields']:
                                        field_names += x["name"] + ", "
                                    field_names = field_names[:len(field_names) - 2]
                                except:
                                    field_names = ''
                                try:
                                    field_values = ""
                                    for x in data['fields']:
                                        field_values += x["value"] + ", "
                                    field_values = field_values[:len(field_values) - 2]
                                except:
                                    field_values = ''

                                cursor.execute("UPDATE role_embed_msg SET title = ?, description = ?, color = ?, footer_text = ?, image_url = ?, author_name = ?, author_url = ?, author_icon_url = ?, footer_icon_url = ?, thumbnail_url = ?, field_names = ?, field_values = ?, role_id = ?, channel_id = ?, channel_name = ?, raw_json = ? WHERE id = ? AND guild_id = ?", (title, description, color, footer_text, image_url, author_name, author_url, author_icon_url, footer_icon_url, thumbnail_url, field_names, field_values, new_roles_id, channel_id, channel_name, raw_json, id, interaction.guild_id))
                                db.commit()
                                if roles_action is None:
                                    embed = discord.Embed(description=f"Embed updated with the ID -> ``{id}``", color=0x7575fc)
                                else:
                                    if roles_action == "add":
                                        embed = discord.Embed(description=f"Embed updated with the ID -> ``{id}``\nRoles added -> {added_roles}", color=0x7575fc)
                                    if roles_action == "remove":
                                        embed = discord.Embed(description=f"Embed updated with the ID -> ``{id}``\nRoles removed -> {removed_roles}", color=0x7575fc)
                                await interaction.response.send_message(embed=embed, ephemeral=True)

                            async def on_error(self, interaction: Interaction):
                                    await interaction.response.send_message("An error occured. Please check your input.", ephemeral=True)
                                    return
                                
                            async def on_timeout(self, interaction: Interaction):
                                await interaction.response.send_message("You took too long to respond.", ephemeral=True)
                                return

                    await interaction.response.send_modal(EditEmbedJSON())
                    return
                else:
                    await interaction.response.send_message(f"No such embed with ID ``{id}`` exists.", ephemeral=True)


            @message.command(description="Shows the list of roles added to a role message")
            async def roles_list(self, interaction: Interaction, id: int):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return
                
                result = cursor.execute(f"SELECT role_id FROM role_embed_msg WHERE id = {id} AND guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    roles_id_list = list(result[0].split(", "))
                    roles = ""
                    for role_id in roles_id_list:
                        try:
                            roles += interaction.guild.get_role(int(role_id)).mention + ", "
                        except:
                            continue
                    roles = roles[:len(roles) - 2]

                    if roles == "":
                        await interaction.response.send_message(f"No role has been added to the embed with ID ``{id}``.", ephemeral=True)
                    else:
                        embed = discord.Embed(description=f"Roles added to embed:\n{roles}", color=0x7575fc)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(f"No such embed with ID ``{id}`` exists.", ephemeral=True)


            @message.command(description="Deletes a role message")
            async def delete(self, interaction: Interaction, id: int):
                
                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return

                result = cursor.execute(f"SELECT id FROM role_embed_msg WHERE id = {id} AND guild_id = {interaction.guild_id}").fetchone()
                if result is not None:
                    cursor.execute("DELETE FROM role_embed_msg WHERE id = ? AND guild_id = ?", (id, interaction.guild_id,))
                    db.commit()
                    await interaction.response.send_message(f"Embed deleted with ID ``{id}``.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"No such embed with ID ``{id}`` exists.", ephemeral=True)


                
            @message.command(description="Shows the list of role message embed id's")
            async def embed_list(self, interaction: Interaction):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return

                result = cursor.execute(f"SELECT id, title FROM role_embed_msg WHERE guild_id = {interaction.guild_id}").fetchall()
                if len(result) != 0:
                    ids = ""
                    for x in result:
                        ids += f"``{x[0]}`` - {x[1]}\n"

                    embed = discord.Embed(description=f"All embed IDs available:\n{ids}", color=0x7575fc)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("No embed ID available.", ephemeral=True)

        self.bot.tree.add_command(role())


async def setup(bot):
    await bot.add_cog(role(bot))
