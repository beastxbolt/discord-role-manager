import discord
from discord.ext import commands
from discord import app_commands, Interaction


class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')


    @app_commands.command(name="help", description="Shows the list of available commands and its usage.")
    async def help(self, interaction: Interaction):

        embed = discord.Embed(color=0x7575fc)
        embed.description = "**__ROLE MANAGER COMMANDS__**\n\n`/help` \nShows the list of commands and descriptions\n\n**__Permissions__**\n`/permissions role add [role]`\nAdds a role to the list of roles allowed to use slash commands\n`/permissions role remove [role]`\nRemoves a role from the list of roles allowed to use slash commands\n`/permissions role list`\nLists all of roles allowed to use the  commands\n\n**__Role Linking__**\n`/role linking add [watched_role] [rolelink_type] [role_action] [role]`\nLinks a role based on it being added or removed\n`/role linking remove [watched_role] [rolelink_type]`\nRemoves linking role\n`/role linking list` \nShows all the available role links in the server\n\n**__Role Persistence__**\n`/role persistence add [role]`\nAdds persisted roles\n`/role persistence remove [role]`\nRemove persisted roles\n`/role persistence list`\nLists all persisted roles\n`/role persistence logs`\nSets the channel to log all roles saved and restored\n\n**__Hierarchy Role__**\n`/hierarchy role add [role] [position]`\nAdds a role to the hierarchy\n`/hierarchy role remove [role]`\nRemoved a role from the hierarchy\n`/hierarchy role move [current_position] [new_position]`\nChange the role position in the hierarchy\n`/hierarchy role list`\nLists all the roles positions in the hierarchy\n\n**__Role Message__**\n`/role message create [method] [channel] [roles]`\nCreates a role message\n`/role message edit [method] [id] [channel] [roles_action] [roles]`\nEdits a role message\n`/role message roles_list [id]`\nShow the list of roles added to a role message\n`/role message embed_list`\nShow the list of role message embed id's\n`/role message delete [id]`\nDeletes a role message"
        await interaction.response.send_message(embed=embed)
        return


async def setup(bot):
    await bot.add_cog(help(bot))
