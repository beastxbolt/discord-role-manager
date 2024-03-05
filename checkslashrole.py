async def check_slash_role(interaction, cursor):
    result = cursor.execute(f"SELECT role_id FROM permissions WHERE guild_id = {interaction.guild_id}").fetchone()
    if result is not None:
        roles_id_list = list(result[0].split(", "))
        for role in interaction.user.roles:
            if str(role.id) in roles_id_list:
                return True
            else:
                continue
        return False
    else:
        return True