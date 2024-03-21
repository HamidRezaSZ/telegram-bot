import logging
import os
import re
import uuid

from dotenv import load_dotenv
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy.orm import Session
from telegram import Update
from telegram.ext import (Application, CallbackContext, CommandHandler,
                          MessageHandler, filters)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

engine = create_engine("sqlite:///user_data.db", echo=True)
meta = MetaData()

user_table = Table(
    "users",
    meta,
    Column("uuid", String, primary_key=True),
    Column("chat_id", Integer, nullable=False),
    Column("first_name", String),
    Column("last_name", String),
    Column("phone_number", String),
    Column("video_file_id", String),
)

meta.create_all(engine)


bot_token = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_uuid = str(uuid.uuid4())

    with Session(engine) as session:
        user_exist = session.execute(
            user_table.select().where(user_table.c.chat_id == chat_id)).fetchone()
        if not user_exist:
            new_user = {
                "uuid": user_uuid,
                "chat_id": chat_id,
            }
            session.execute(user_table.insert().values(new_user))
            session.commit()

    message = """
    Welcome to the bot! Please send the following information:
    - first_name: <your first name>
    - last_name: <your last name>
    - phone_number: <your phone number>

    - Your video: <send a video>
"""
    await update.message.reply_text(message)


async def handle_unmatched_messages(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("I didn't understand, please try again!")


async def handle_user_first_name(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_uuid = None

    with Session(engine) as session:
        result = session.execute(
            user_table.select().where(user_table.c.chat_id == chat_id)
        ).fetchone()
        if result:
            user_uuid = result[0]

    if user_uuid:
        match = re.match(r'^first_name:\s*(.+)$',
                         update.message.text, re.IGNORECASE)
        if match:
            context.user_data['first_name'] = match.group(1).strip()
            with Session(engine) as session:
                updated_user_info = {
                    "first_name": context.user_data["first_name"],
                }
                session.execute(
                    user_table.update()
                    .values(updated_user_info)
                    .where(user_table.c.uuid == user_uuid)
                )
                session.commit()

            await update.message.reply_text("Your first name has been successfully registered")
        else:
            await update.message.reply_text(
                "The first name format is not valid, please send it again")
    else:
        await update.message.reply_text(
            "Oops! Something went wrong, please use the /start command"
        )


async def handle_user_last_name(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_uuid = None

    with Session(engine) as session:
        result = session.execute(
            user_table.select().where(user_table.c.chat_id == chat_id)
        ).fetchone()
        if result:
            user_uuid = result[0]

    if user_uuid:
        match = re.match(r'^last_name:\s*(.+)$',
                         update.message.text, re.IGNORECASE)
        if match:
            context.user_data['last_name'] = match.group(1).strip()
            with Session(engine) as session:
                updated_user_info = {
                    "last_name": context.user_data["last_name"],
                }
                session.execute(
                    user_table.update()
                    .values(updated_user_info)
                    .where(user_table.c.uuid == user_uuid)
                )
                session.commit()

            await update.message.reply_text("Your last name has been successfully registered")
        else:
            await update.message.reply_text(
                "The last name format is not valid, please send it again")
    else:
        await update.message.reply_text(
            "Oops! Something went wrong, please use the /start command"
        )


async def handle_user_file(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_uuid = None

    with Session(engine) as session:
        result = session.execute(
            user_table.select().where(user_table.c.chat_id == chat_id)
        ).fetchone()
        if result:
            user_uuid = result[0]

    if user_uuid:
        if update.message.video.file_size > 50000000:
            await update.message.reply_text(
                "The video file size is too large, please send a file less than 50MB"
            )
            return

        video_file_id = update.message.video.file_id
        context.user_data["video_file"] = video_file_id

        with Session(engine) as session:
            updated_user_info = {
                "video_file_id": context.user_data["video_file"],
            }
            session.execute(
                user_table.update()
                .values(updated_user_info)
                .where(user_table.c.uuid == user_uuid)
            )
            session.commit()

        await update.message.reply_text(
            "Your video has been successfully registered")
    else:
        await update.message.reply_text(
            "Oops! Something went wrong, please use the /start command"
        )


async def handle_user_phone_number(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_uuid = None

    with Session(engine) as session:
        result = session.execute(
            user_table.select().where(user_table.c.chat_id == chat_id)
        ).fetchone()
        if result:
            user_uuid = result[0]

    if user_uuid:
        match = re.match(r'^phone_number:\s*(.+)$',
                         update.message.text, re.IGNORECASE)
        if match:
            context.user_data['phone_number'] = match.group(1).strip()
            with Session(engine) as session:
                updated_user_info = {
                    "phone_number": context.user_data["phone_number"],
                }
                session.execute(
                    user_table.update()
                    .values(updated_user_info)
                    .where(user_table.c.uuid == user_uuid)
                )
                session.commit()

            await update.message.reply_text("Your phone number has been successfully registered")
        else:
            await update.message.reply_text(
                "The phone number format is not valid, please send it again")
    else:
        await update.message.reply_text(
            "Oops! Something went wrong, please use the /start command"
        )


def main() -> None:
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start, block=True))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'^last_name:\s*(.+)$', re.IGNORECASE)) & ~
                                           filters.COMMAND, handle_user_last_name, block=True))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'^first_name:\s*(.+)$', re.IGNORECASE)) & ~
                                           filters.COMMAND, handle_user_first_name, block=True))
    application.add_handler(MessageHandler(filters.Regex(re.compile(r'^phone_number:\s*(.+)$', re.IGNORECASE)) & ~
                                           filters.COMMAND, handle_user_phone_number, block=True))
    application.add_handler(MessageHandler(filters.VIDEO & ~
                                           filters.COMMAND, handle_user_file, block=True))

    application.add_handler(MessageHandler(
        filters.ALL, handle_unmatched_messages, block=True))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
