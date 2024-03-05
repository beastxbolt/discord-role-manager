import discord
from discord.ext import commands
from discord import app_commands, Interaction
from sqlite3 import connect
from discord import Colour
from checkslashrole import check_slash_role
import yaml

db = connect('./database.db', check_same_thread = False)
cursor = db.cursor()

class hierarchy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @app_commands.guild_only()
        class hierarchy(app_commands.Group):
            role = app_commands.Group(name="role", description="Sub group of roles group.")

            @role.command(description="Adds a role to the hierarchy")
            async def add(self, interaction: Interaction, role: discord.Role, position: int):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return
                
                with open('./config.yml', 'r') as file:
                    data = yaml.load(file, Loader=yaml.CLoader)

                    if data["roles"] is None:
                        data["roles"] = {str(interaction.guild_id): []}

                    elif str(interaction.guild_id) in data["roles"]:
                        pass

                    else:
                        var = {str(interaction.guild_id): []}
                        data["roles"].update(var)
                    
                    if role.id in data["roles"][str(interaction.guild_id)]:
                        await interaction.response.send_message(f"{role.mention} role is already added to the hierarchy roles list.", ephemeral=True)

                    else:
                        if position < 1 or position > (len(data["roles"][str(interaction.guild_id)]) + 1):
                            await interaction.response.send_message("Role position is not valid.", ephemeral=True)
                            return

                        data["roles"][str(interaction.guild_id)].insert(position - 1, role.id)
                        with open('./config.yml', 'w') as file:
                            yaml.dump(data, file)
                        await interaction.response.send_message(f"{role.mention} role has been added to the hierarchy roles list at position ``{position}``.", ephemeral=True)


            @role.command(description="Removes a role from the hierarchy")
            async def remove(self, interaction: Interaction, role: discord.Role):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return
                
                with open('./config.yml', 'r') as file:
                    data = yaml.load(file, Loader=yaml.CLoader)

                    if data["roles"] is None:
                        await interaction.response.send_message(f"{role.mention} role is NOT added to the hierarchy roles list.", ephemeral=True)
                        return

                    elif str(interaction.guild_id) in data["roles"]:
                        pass

                    else:
                        await interaction.response.send_message(f"{role.mention} role is NOT added to the hierarchy roles list.", ephemeral=True)
                        return
                    
                    if role.id in data["roles"][str(interaction.guild_id)]:
                        data["roles"][str(interaction.guild_id)].remove(role.id)
                        with open('./config.yml', 'w') as file:
                            yaml.dump(data, file)
                        await interaction.response.send_message(f"{role.mention} role has been removed from the hierarchy roles list.", ephemeral=True)

                    else:
                        await interaction.response.send_message(f"{role.mention} role is NOT added to the hierarchy roles list.", ephemeral=True)


            @role.command(description="Lists all the roles positions in the hierarchy")
            async def list(self, interaction: Interaction):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return
                
                with open('./config.yml', 'r') as file:
                    data = yaml.load(file, Loader=yaml.CLoader)

                    if data["roles"] is None:
                        await interaction.response.send_message("No roles have been added to bot's hierarchy roles.", ephemeral=True)
                        return

                    elif str(interaction.guild_id) in data["roles"]:
                        pass

                    else:
                        await interaction.response.send_message("No roles have been added to bot's hierarchy roles.", ephemeral=True)
                        return
                    
                    if len(data["roles"][str(interaction.guild_id)]) == 0:
                        await interaction.response.send_message("No roles have been added to bot's hierarchy roles.", ephemeral=True)
                        return
                    
                    i = 1
                    store_role = []
                    roles = ""
                    for role in data["roles"][str(interaction.guild_id)]:
                        try:
                            roles += f"**{i}.** {interaction.guild.get_role(role).mention}\n"
                            i += 1
                            store_role.append(role)
                        except:
                            data["roles"][str(interaction.guild_id)].remove(role)
                            continue

                    with open('./config.yml', 'w') as file:
                        yaml.dump(data, file)

                    if len(store_role) != 0:
                        embed = discord.Embed(description=f"Roles added to bot's hierarchy roles list -\n{roles}", color=0x7575fc)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        await interaction.response.send_message("No roles have been added to bot's hierarchy roles.", ephemeral=True)
                        return


            @role.command(description="Changes the role position in the hierarchy")
            async def move(self, interaction: Interaction, current_position: int, new_position: int):

                if await check_slash_role(interaction, cursor) is True:
                    pass
                else:
                    await interaction.response.send_message("You don't have the required role to use slash commands.", ephemeral=True)
                    return

                with open('./config.yml', 'r') as file:
                    data = yaml.load(file, Loader=yaml.CLoader)

                    if data["roles"] is None:
                        await interaction.response.send_message("No roles have been added to bot's hierarchy roles.", ephemeral=True)
                        return

                    elif str(interaction.guild_id) in data["roles"]:
                        pass

                    else:
                        await interaction.response.send_message("No roles have been added to bot's hierarchy roles.", ephemeral=True)
                        return
                    
                    if len(data["roles"][str(interaction.guild_id)]) == 0:
                        await interaction.response.send_message("No roles have been added to bot's hierarchy roles.", ephemeral=True)
                        return

                    if current_position < 1 or current_position > (len(data["roles"][str(interaction.guild_id)])):
                        await interaction.response.send_message("Role position is not valid.", ephemeral=True)
                        return

                    if new_position < 1 or new_position > (len(data["roles"][str(interaction.guild_id)])):
                        await interaction.response.send_message("Role position is not valid.", ephemeral=True)
                        return

                    popped_role = data["roles"][str(interaction.guild_id)].pop(current_position - 1)
                    data["roles"][str(interaction.guild_id)].insert(new_position - 1, popped_role)

                    try:
                        role = interaction.guild.get_role(popped_role)
                        await interaction.response.send_message(f"{role.mention}'s position has been changed to ``{new_position}``!", ephemeral=True)
                        with open('./config.yml', 'w') as file:
                            yaml.dump(data, file)
                    except:
                        await interaction.response.send_message(f"Role position has been changed to ``{new_position}``!", ephemeral=True)
                        with open('./config.yml', 'w') as file:
                            yaml.dump(data, file)

        self.bot.tree.add_command(hierarchy())    

async def setup(bot):
    await bot.add_cog(hierarchy(bot))
