import discord
from discord.ext import commands
from discord import app_commands, Interaction
from sqlite3 import connect
from discord import Colour
from checkslashrole import check_slash_role

db = connect('./database.db', check_same_thread = False)
cursor = db.cursor()

class permissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @app_commands.guild_only()
        class permissions(app_commands.Group):
            role = app_commands.Group(name="role", description="Sub group of rolemessage group.")

            @role.command(description="Add role to the list of roles allowed to use commands")
            async def add(self, interaction: Interaction, role: discord.Role):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use commands.", ephemeral=True)
                    return

                result = cursor.execute(f"SELECT role_id, role_name FROM permissions WHERE guild_id = {interaction.guild_id}").fetchone()
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

                        cursor.execute("UPDATE permissions SET role_id = ?, role_name = ? WHERE guild_id = ?", (new_roles_id, new_roles_name, interaction.guild_id))
                        db.commit()
                        await interaction.response.send_message(f"{role.mention} role has been added to the list.", ephemeral=True)
                else:
                    new_roles_id = str(role.id)
                    new_roles_name = role.name
                    cursor.execute("INSERT INTO permissions (guild_id, role_id, role_name) VALUES (?,?,?)", (interaction.guild_id, new_roles_id, new_roles_name))
                    db.commit()
                    await interaction.response.send_message(f"{role.mention} role has been added to the list.", ephemeral=True)

            @role.command(description="Removes role from the list of roles allowed to use commands")
            async def remove(self, interaction: Interaction, role: discord.Role):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use commands.", ephemeral=True)
                    return

                result = cursor.execute(f"SELECT role_id, role_name FROM permissions WHERE guild_id = {interaction.guild_id}").fetchone()
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

                            cursor.execute("UPDATE permissions SET role_id = ?, role_name = ? WHERE guild_id = ?", (new_roles_id, new_roles_name, interaction.guild_id))
                            db.commit()
                        else:
                            cursor.execute("DELETE FROM permissions WHERE guild_id = ?", (interaction.guild_id,))
                            db.commit()
                        await interaction.response.send_message(f"{role.mention} role has been removed from the list.", ephemeral=True)
                else:
                    await interaction.response.send_message(f"{role.mention} role is NOT added to the list.", ephemeral=True)

            @role.command(description="Shows the list of roles allowed to use commands")
            async def list(self, interaction: Interaction):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use commands.", ephemeral=True)
                    return
                
                result = cursor.execute(f"SELECT role_id FROM permissions WHERE guild_id = {interaction.guild_id}").fetchone()
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
                        cursor.execute("DELETE FROM permissions WHERE guild_id = ?", (interaction.guild_id,))
                        db.commit()
                        await interaction.response.send_message("No role has been added to the list.", ephemeral=True)
                    else:
                        embed = discord.Embed(description=f"Roles added to permissions roles list -\n{roles}", color=0x7575fc)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("No role has been added to the list.", ephemeral=True)

        self.bot.tree.add_command(permissions())

async def setup(bot):
    await bot.add_cog(permissions(bot))