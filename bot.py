from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ChatMemberHandler
from telegram import ChatPermissions
import json, os, re

TOKEN = "7843972684:AAFf8KbAY1wVFfvXIvKT0KMrZ_sqvbg5jsA"
OWNER_ID = 7293463985
GROUPS_FILE = "enabled_groups.json"
forced_channel = None
enabled_groups = set()

def load_enabled_groups():
    global enabled_groups
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            enabled_groups = set(json.load(f))

def save_enabled_groups():
    with open(GROUPS_FILE, "w") as f:
        json.dump(list(enabled_groups), f)

load_enabled_groups()

def is_admin(update):
    user_id = update.effective_user.id
    member = update.effective_chat.get_member(user_id)
    return member.status in ["administrator", "creator"]

def only_if_enabled(func):
    def wrapper(update, context):
        if update.effective_chat.id in enabled_groups:
            return func(update, context)
    return wrapper

@only_if_enabled
def welcome(update, context):
    for member in update.message.new_chat_members:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"👋 Welcome {member.full_name} to the group!"
        )

@only_if_enabled
def auto_detect_ads(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    ad_keywords = [
        "تلخيص", "حل واجبات", "اعذار", "مشاريع", "بحوث", "خدمة", "تواصل", "خاص",
        "درجات", "ضمان", "سيرة", "مقالات", "ترجمة", "سعر", "نقوم", "نقدم", "لدينا",
        "أوفر", "نحل", "نعمل", "سكليف", "بوستر", "عرض خاص"
    ]
    help_phrases = [
        "محتاج", "ساعدوني", "أحد يساعدني", "أريد تلخيص", "هل فيه أحد", "مين يقدر", "ساعدني", "ممكن تساعدوني", "أحد عنده"
    ]
    is_ad = any(word in text for word in ad_keywords)
    is_help = any(phrase in text for phrase in help_phrases)

    if is_ad and not is_help:
        try:
            context.bot.delete_message(update.effective_chat.id, update.message.message_id)
            context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=update.message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔐 | {update.message.from_user.first_name} has been restricted.\n🔍 Reason: Ad or spam detected."
            )
        except:
            pass

@only_if_enabled
def check_subscription(update, context):
    global forced_channel
    if forced_channel:
        username = forced_channel.replace("https://t.me/", "")
        for member in update.message.new_chat_members:
            try:
                status = context.bot.get_chat_member(username, member.id).status
                if status not in ['member', 'administrator', 'creator']:
                    context.bot.restrict_chat_member(
                        chat_id=update.effective_chat.id,
                        user_id=member.id,
                        permissions=ChatPermissions(can_send_messages=False)
                    )
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"⚠️ {member.full_name} has been restricted for not joining the channel:\n{forced_channel}"
                    )
            except: pass

def set_forced_subscription(update, context):
    global forced_channel
    if is_admin(update) and context.args:
        forced_channel = context.args[0]
        update.message.reply_text(f"✅ Forced subscription enabled:\n{forced_channel}")

def disable_forced_subscription(update, context):
    global forced_channel
    if is_admin(update):
        forced_channel = None
        update.message.reply_text("❌ Forced subscription disabled.")

def notify_owner_on_add(update, context):
    if update.my_chat_member.new_chat_member.status == "member":
        chat = update.effective_chat
        context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"📢 Bot added to new group:\n📛 Name: {chat.title}\n🆔 ID: {chat.id}\nSend /enable {chat.id} to activate."
        )

def enable_group(update, context):
    if update.effective_user.id == OWNER_ID and context.args:
        group_id = int(context.args[0])
        enabled_groups.add(group_id)
        save_enabled_groups()
        update.message.reply_text(f"✅ Bot activated for group ID: {group_id}")
    else:
        update.message.reply_text("❌ This command is only for the owner.")

# Admin commands
@only_if_enabled
def lock_chat(update, context):
    if is_admin(update):
        context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=False))
        update.message.reply_text("🔒 Chat has been locked.")

@only_if_enabled
def unlock_chat(update, context):
    if is_admin(update):
        context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions(can_send_messages=True))
        update.message.reply_text("🔓 Chat has been unlocked.")

@only_if_enabled
def mute(update, context):
    if is_admin(update) and update.message.reply_to_message:
        context.bot.restrict_chat_member(
            update.effective_chat.id,
            update.message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=False)
        )
        update.message.reply_text("🔇 User muted.")

@only_if_enabled
def unmute(update, context):
    if is_admin(update) and update.message.reply_to_message:
        context.bot.restrict_chat_member(
            update.effective_chat.id,
            update.message.reply_to_message.from_user.id,
            ChatPermissions(can_send_messages=True)
        )
        update.message.reply_text("🔊 User unmuted.")

@only_if_enabled
def ban(update, context):
    if is_admin(update) and update.message.reply_to_message:
        context.bot.kick_chat_member(
            update.effective_chat.id,
            update.message.reply_to_message.from_user.id
        )
        update.message.reply_text("🚫 User banned.")

@only_if_enabled
def unban(update, context):
    if is_admin(update) and update.message.reply_to_message:
        context.bot.unban_chat_member(
            update.effective_chat.id,
            update.message.reply_to_message.from_user.id
        )
        update.message.reply_text("✅ User unbanned.")

@only_if_enabled
def user_info(update, context):
    if is_admin(update) and update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        update.message.reply_text(f"ℹ️ Name: {u.full_name}\n@{u.username}\nID: {u.id}")

@only_if_enabled
def group_link(update, context):
    if is_admin(update):
        try:
            link = context.bot.export_chat_invite_link(update.effective_chat.id)
            update.message.reply_text(f"🔗 Group link:\n{link}")
        except:
            update.message.reply_text("❗ Failed to get group link.")

# Bot setup
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

# Owner commands
dp.add_handler(CommandHandler("enable", enable_group))
dp.add_handler(ChatMemberHandler(notify_owner_on_add, chat_member_types=["my_chat_member"]))

# Forced subscription
dp.add_handler(CommandHandler("enable_forced_sub", set_forced_subscription))
dp.add_handler(CommandHandler("disable_forced_sub", disable_forced_subscription))

# Admin features
dp.add_handler(CommandHandler("lock", lock_chat))
dp.add_handler(CommandHandler("unlock", unlock_chat))
dp.add_handler(CommandHandler("mute", mute))
dp.add_handler(CommandHandler("unmute", unmute))
dp.add_handler(CommandHandler("ban", ban))
dp.add_handler(CommandHandler("unban", unban))
dp.add_handler(CommandHandler("info", user_info))
dp.add_handler(CommandHandler("link", group_link))

# Automatic detection
dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))
dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, check_subscription))
dp.add_handler(MessageHandler(Filters.text & Filters.group, auto_detect_ads))

updater.start_polling()
updater.idle()