import aiosqlite
import discord

from pathlib import Path
from typing import Any
import logging

import config


log = logging.getLogger("mainLog")


async def setup_dbs(path: Path = config.DB_PATH) -> bool:
    try:
        async with aiosqlite.connect(path) as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "CREATE TABLE IF NOT EXISTS settings(setting_name TEXT, setting TEXT, guild INTEGER)"
                )
                await cursor.execute("CREATE TABLE IF NOT EXISTS permissions(kind TEXT, id INTEGER, guild INTEGER)")
            await db.commit()
            log.info("DB's set up successfully")
        return True
    except Exception as e:
        log.error("Error whilst setting up databases", exc_info=e)


async def insert_settings(setting_name: str, setting: Any, guild: int, path: Path | str = config.DB_PATH) -> Any:
    try:
        setting_name = setting_name.lower()
        async with aiosqlite.connect(path) as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "SELECT setting FROM settings WHERE setting_name = ? AND guild = ?", (setting_name, guild)
                )
                old_setting = await cursor.fetchone()
                if not old_setting:
                    await cursor.execute(
                        "INSERT INTO settings(setting_name, setting, guild) VALUES (?,?,?)",
                        (setting_name, setting, guild),
                    )
                    await db.commit()
                    return None
                else:
                    await cursor.execute(
                        "UPDATE settings SET setting = ? WHERE setting_name = ? AND guild = ?",
                        (setting, setting_name, guild),
                    )
                    await db.commit()
                    return old_setting
    except Exception as e:
        log.error("Error whilst inserting setting", exc_info=e)


async def get_setting(setting_name: str, guild_id: int, path: Path = config.DB_PATH) -> int:
    async with aiosqlite.connect(path) as db:
        async with db.cursor() as cursor:
            await cursor.execute(
                "SELECT setting FROM settings WHERE guild = ? AND setting_name = ?", (guild_id, setting_name)
            )
            setting = await cursor.fetchone()
    return setting
