import discord
from discord.ext import commands
from sqlite3 import connect
from discord import Colour
import datetime
import yaml
import time

db = connect('./database.db', check_same_thread = False)
cursor = db.cursor()

class events(commands.Cog):
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

    async def restored_roles(self, guild, member, user_roles):
        result = cursor.execute(f"SELECT channel_id FROM role_persistence_logs_channel WHERE guild_id = {guild.id}").fetchone()
        if result is not None:
            roles = ""
            if len(user_roles) > 0:
                for role_id in user_roles:
                    try:
                        roles += guild.get_role(int(role_id)).mention + ", "
                    except:
                        continue
                roles = roles[:len(roles) - 2]

                embed = discord.Embed(description=f"{member.mention}'s Roles Have Been Restored.\nRoles restored -\n{roles}", color=0x7575fc)
                try:
                    channel = guild.get_channel(result[0])
                    await channel.send(embed=embed)
                    return True
                except discord.NotFound:
                    return False
            else:
                return False
        else:
            return False

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print("Updating member roles on database...")

        for guild in self.bot.guilds:
            for member in guild.members:

                result = cursor.execute(f"SELECT role_id FROM role_persistence_monitored_roles WHERE guild_id = {guild.id}").fetchone()
                if result is not None:
                    role_persistence_monitored_roles_id_list = list(result[0].split(", "))

                    user_roles_id_in_monitored_list = []
                    for user_role in member.roles:
                        if str(user_role.id) in role_persistence_monitored_roles_id_list:
                            user_roles_id_in_monitored_list.append(str(user_role.id))
                        else:
                            continue

                    user_roles_name = ""
                    for role in member.roles:
                        if str(role.id) in role_persistence_monitored_roles_id_list:
                            user_roles_name += str(role.name) + ", "
                        else:
                            continue
                    user_roles_name = user_roles_name[:len(user_roles_name) - 2]

                    user_roles_id = ""
                    for role in member.roles:
                        if str(role.id) in role_persistence_monitored_roles_id_list:
                            user_roles_id += str(role.id) + ", "
                        else:
                            continue
                    user_roles_id = user_roles_id[:len(user_roles_id) - 2]

                    if len(user_roles_id_in_monitored_list) == 0:
                        continue

                    result = cursor.execute(f"SELECT role_id, is_save_role FROM role_persistence WHERE guild_id = {guild.id} AND user_id = {member.id}").fetchone()
                    if result is not None:
                        if result[1] == "False":
                            cursor.execute("UPDATE role_persistence SET is_save_role = ? WHERE guild_id = ? AND user_id = ?", ("True", guild.id, member.id))
                            db.commit()

                        db_roles_id_list = list(result[0].split(", "))

                        check_user_roles = []
                        for x in user_roles_id_in_monitored_list:
                            if x not in db_roles_id_list:
                                check_user_roles.append(x)

                        check_db_roles = []
                        for y in db_roles_id_list:
                            if y not in user_roles_id_in_monitored_list:
                                check_db_roles.append(y)

                        if len(check_user_roles) == 0 and len(check_db_roles) == 0:
                            continue

                        cursor.execute("UPDATE role_persistence SET rolename = ?, role_id = ? WHERE guild_id = ? AND user_id = ?", (user_roles_name, user_roles_id, guild.id, member.id))
                        db.commit()
                    else:
                        cursor.execute("INSERT INTO role_persistence (guild_id, username, user_id, rolename, role_id, is_save_role) VALUES (?,?,?,?,?,?)", (guild.id, str(member), member.id, user_roles_name, user_roles_id, "True"))
                        db.commit()
                    if await self.saved_roles(guild, member, user_roles_id_in_monitored_list) is False:
                        continue
                else:
                    continue
        print("Bot Is Ready!")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(description=f"**{error}**", color=0x7575fc, timestamp=ctx.message.created_at)
            await ctx.send(embed=embed)
            return

        if isinstance(error,commands.BadArgument):
            embed = discord.Embed(title="Check Your Argument and Try Again!",color=0x7575fc, timestamp=ctx.message.created_at)
            await ctx.send(embed=embed)
            return

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        if len(before.roles) < len(after.roles) or len(before.roles) > len(after.roles):
            if len(before.roles) > len(after.roles): #Role removed
                result = cursor.execute(f"SELECT role_to_watch, role, rolelink_type, role_action FROM rolelink_roles WHERE guild_id = {before.guild.id}").fetchall()
                if len(result) != 0:
                    removed_role = [role for role in before.roles if role not in after.roles][0]

                    for x in result:
                        if x[0] == removed_role.id and x[2] == "remove":
                            try:
                                if x[3] == "add":
                                    await after.add_roles(after.guild.get_role(x[1]))
                                if x[3] == "remove":
                                    await after.remove_roles(after.guild.get_role(x[1]))
                            except:
                                pass
                        else:
                            continue
                else:
                    pass
            else:
                pass

            if len(before.roles) < len(after.roles): #Role added

                result = cursor.execute(f"SELECT role_to_watch, role, rolelink_type, role_action FROM rolelink_roles WHERE guild_id = {before.guild.id}").fetchall()
                if len(result) != 0:
                    added_role = [role for role in after.roles if role not in before.roles][0]

                    for x in result:
                        if x[0] == added_role.id and x[2] == "add":
                            try:
                                if x[3] == "add":
                                    await after.add_roles(after.guild.get_role(x[1]))
                                if x[3] == "remove":
                                    await after.remove_roles(after.guild.get_role(x[1]))
                            except:
                                pass
                        else:
                            continue
                else:
                    pass

                added_role = [role for role in after.roles if role not in before.roles][0]
                result = cursor.execute(f"SELECT * FROM role_embed_msg WHERE guild_id = {before.guild.id}").fetchall()
                if len(result) != 0:
                    for emb in result:
                        roles_id_list = list(emb[14].split(", "))
                        if str(added_role.id) in roles_id_list:
                            if emb[15] is not None:
                                title = emb[2]
                                image_url = emb[3]
                                description = f"{after.mention}\n" + emb[4]
                                author_name = emb[5]
                                author_icon_url = emb[6]
                                author_url = emb[7]
                                try:
                                    color = int(emb[8])
                                except:
                                    color = Colour.default()
                                footer_text = emb[9]
                                footer_icon_url = emb[10]
                                thumbnail_url = emb[11]

                                field_names = list(emb[12].split(", "))
                                field_values = list(emb[13].split(", "))

                                embed = discord.Embed()
                                embed.title = title
                                embed.set_image(url=image_url)
                                embed.description = description
                                embed.set_author(name=author_name, url=author_url, icon_url=author_icon_url)
                                embed.color = color
                                embed.set_footer(text=f"{footer_text}\nEmbed ID - {emb[0]}", icon_url=footer_icon_url)
                                embed.set_thumbnail(url=thumbnail_url)

                                if len(field_names) > 0 and '' not in field_names:
                                    if len(field_values) > 0 and '' not in field_values:
                                        for x, y in zip(field_names, field_values):
                                            embed.add_field(name=x, value=y, inline=False)

                                channel = before.guild.get_channel(emb[15])
                                if channel is not None:
                                    msg = await channel.send(f"{after.mention}", embed=embed)
                                    await msg.edit(content="", embed=embed)
                                else:
                                    pass
                            else:
                                pass
                        else:
                            pass
                else:
                    pass
                #
                with open('./config.yml', 'r') as file:
                    data = yaml.load(file, Loader=yaml.CLoader)

                added_role = [role for role in after.roles if role not in before.roles][0]

                if data["roles"] is not None:
                    if str(before.guild.id) in data["roles"]:
                        if added_role.id in data["roles"][str(before.guild.id)]:
                            user_role_ids = []
                            for role in before.roles:
                                user_role_ids.append(role.id)

                            other_roles_of_user_in_list = []
                            for role in data["roles"][str(before.guild.id)]:
                                if role in user_role_ids:
                                    other_roles_of_user_in_list.append(role)
                            
                            if len(other_roles_of_user_in_list) != 0:
                                added_role_index = data["roles"][str(before.guild.id)].index(added_role.id)
                                topmost_role = other_roles_of_user_in_list[0]
                                topmost_role_index = data["roles"][str(before.guild.id)].index(topmost_role)

                                if topmost_role_index < added_role_index:
                                    await before.remove_roles(added_role)
                                
                                if topmost_role_index > added_role_index:
                                    try:
                                        await before.remove_roles(before.guild.get_role(topmost_role))
                                    except:
                                        pass

                                if len(other_roles_of_user_in_list) > 1:
                                    for role in other_roles_of_user_in_list[1:]:
                                        try:
                                            await before.remove_roles(before.guild.get_role(role))
                                        except:
                                            continue
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
            else:
                pass

            result = cursor.execute(f"SELECT role_id FROM role_persistence_monitored_roles WHERE guild_id = {before.guild.id}").fetchone()
            if result is not None:
                roles_id_list = list(result[0].split(", "))

                user_roles_name = ""
                for role in after.roles:
                    if str(role.id) in roles_id_list:
                        user_roles_name += str(role.name) + ", "
                    else:
                        continue
                user_roles_name = user_roles_name[:len(user_roles_name) - 2]

                user_roles_id = ""
                for role in after.roles:
                    if str(role.id) in roles_id_list:
                        user_roles_id += str(role.id) + ", "
                    else:
                        continue
                user_roles_id = user_roles_id[:len(user_roles_id) - 2]

                user_roles_id_in_monitored_list = list(user_roles_id.split(", "))

                result = cursor.execute(f"SELECT role_id FROM role_persistence WHERE guild_id = {before.guild.id} AND user_id = {before.id}").fetchone()
                if result is not None:
                    check_save_status = cursor.execute(f"SELECT is_save_role FROM role_persistence WHERE guild_id = {before.guild.id} AND user_id = {before.id}").fetchone()
                    if check_save_status is not None and check_save_status[0] == "True":
                        user_roles_in_db = list(result[0].split(", "))
                        if user_roles_id_in_monitored_list != user_roles_in_db:
                            if len(user_roles_id) == 0:
                                cursor.execute("DELETE FROM role_persistence WHERE guild_id = ? AND user_id = ?", (before.guild.id, before.id,))
                                db.commit()
                            else:
                                cursor.execute("UPDATE role_persistence SET rolename = ?, role_id = ? WHERE guild_id = ? AND user_id = ?", (user_roles_name, user_roles_id, before.guild.id, before.id))
                                db.commit()
                            await self.saved_roles(before.guild, before, user_roles_id_in_monitored_list)
                        else:
                            return
                    else:
                        return
                else:
                    cursor.execute("INSERT INTO role_persistence (guild_id, username, user_id, rolename, role_id, is_save_role) VALUES (?,?,?,?,?,?)", (before.guild.id, str(before), before.id, user_roles_name, user_roles_id, "True"))
                    db.commit()
                    await self.saved_roles(before.guild, before, user_roles_id_in_monitored_list)
            else:
                return

        else:
            return

    @commands.Cog.listener()
    async def on_member_join(self, member):

        result = cursor.execute(f"SELECT role_id FROM role_persistence WHERE guild_id = {member.guild.id} AND user_id = {member.id}").fetchone()
    
        if result is not None:
            user_roles_id_list = list(result[0].split(", "))

            cursor.execute("UPDATE role_persistence SET is_save_role = ? WHERE guild_id = ? AND user_id = ?", ("False", member.guild.id, member.id))
            db.commit()
            for role_id in user_roles_id_list:
                try:
                    await member.add_roles(member.guild.get_role(int(role_id)))
                except discord.NotFound:
                    continue
            await self.restored_roles(member.guild, member, user_roles_id_list)
            time.sleep(1)
            cursor.execute("UPDATE role_persistence SET is_save_role = ? WHERE guild_id = ? AND user_id = ?", ("True", member.guild.id, member.id))
            db.commit()
        else:
            return

async def setup(bot):
    await bot.add_cog(events(bot))
