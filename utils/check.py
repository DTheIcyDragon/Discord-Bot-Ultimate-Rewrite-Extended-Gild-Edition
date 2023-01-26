from discord import Role, Member


async def has_role(member: Member, role: Role) -> bool:
    if role in member.roles:
        return True
    return False
