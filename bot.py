import os
import logging
import random
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

TOKEN = "8771740048:AAED_MwXxyKCLVTrSAs5KrIXC0qEK40Nd-M"
EXCEL_FILE = "tanaka.xls"

WELCOME, BLAND, STRENGTH, DRINK, TRIP, RESULT, ADD_MORE, COUNTRY, ADD_MORE_2, PICTURE = range(10)

def load_data():
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE, sheet_name="Sheet1")
        else:
            df = pd.read_excel("tanaka.xlsx", sheet_name="Sheet1")
        df = df.iloc[:, :7]
        df.columns = ["Наименование", "Блэнд", "Бренд", "Название_аромата", "Крепость", "Вкус", "Ароматика"]
        df = df[["Блэнд", "Бренд", "Название_аромата", "Крепость", "Вкус", "Ароматика"]]
        df = df.dropna(subset=["Название_аромата"])
        df["Блэнд"] = df["Блэнд"].fillna("").astype(str).str.lower()
        df["Крепость"] = df["Крепость"].fillna("средняя").astype(str).str.lower()
        df["Вкус"] = df["Вкус"].fillna("нейтральный").astype(str).str.lower()
        df["Ароматика"] = df["Ароматика"].fillna("универсальный").astype(str).str.lower()
        df["Бренд"] = df["Бренд"].fillna("Не указан").astype(str)
        df["Название_аромата"] = df["Название_аромата"].fillna("Не указан").astype(str)
        print(f"✅ Загружено {len(df)} табаков")
        return df
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return None

df = load_data()
logging.basicConfig(level=logging.INFO)

# ================= ФИЛЬТРАЦИЯ =================
def filter_by_bland(df, bland):
    if bland == "классический":
        return df[df["Блэнд"] == "классика"]
    elif bland == "сигарный лист":
        return df[df["Блэнд"] == "сигарный лист"]
    return df

def filter_by_drink(df, drink):
    if drink == "лимонад":
        return df[df["Вкус"].str.contains("кисл|свежий", na=False)]
    elif drink == "глинтвейн":
        return df[df["Вкус"].str.contains("пряный|терпкий|сладкий", na=False)]
    elif drink == "травяной чай":
        return df[df["Вкус"].str.contains("травян|нейтральн", na=False)]
    else:
        return df[df["Вкус"].str.contains("сладкий", na=False)]

def filter_by_trip(df, trip):
    if trip == "загородом":
        keywords = "ягод|орехов|травян|медов|древесн|чайный|цветочн|хвойн"
        return df[df["Ароматика"].str.contains(keywords, na=False)]
    elif trip == "тропики":
        return df[df["Ароматика"].str.contains("фрукт|тропич|цитрус", na=False)]
    else:
        return df[df["Ароматика"].str.contains("десерт|сливочн|напиточн|конфет|алкогольн|парфюм", na=False)]

def filter_by_country(df, country):
    if country == "куба":
        return df[df["Ароматика"].str.contains("алкогольн|напиточн|безаромат", na=False)]
    elif country == "тайланд":
        return df[df["Ароматика"].str.contains("фрукт|тропич|алкогольн", na=False)]
    elif country == "индия":
        return df[df["Ароматика"].str.contains("пряный|специи|парфюм", na=False)]
    elif country == "россия":
        return df[df["Ароматика"].str.contains("ягод|таежн|чайный|медов|орехов", na=False)]
    else:
        return df[df["Ароматика"].str.contains("выпечк|конфет|сливочн|парфюм|винн", na=False)]

def filter_by_picture(df, picture):
    if picture == "1":
        return df[df["Ароматика"].str.contains("ягод|цветочн|травян|древесн|ментол|орехов|хвойн", na=False)]
    elif picture == "2":
        return df[df["Ароматика"].str.contains("цитрус|тропич|напиточн|фрукт|алкогольн", na=False)]
    elif picture == "3":
        return df[df["Ароматика"].str.contains("безаромат|специи|чайный|десерт|парфюм|сливочн|медов", na=False)]
    else:
        return df[df["Ароматика"].str.contains("алкогольн|напиточн|чайный|десерт|парфюм|безаромат", na=False)]

def get_random_hookah(df, full_df):
    if df.empty:
        df = full_df
    row = df.sample(1).iloc[0]
    return {
        "brand": row['Бренд'],
        "name": row['Название_аромата'],
        "strength": row['Крепость'].capitalize(),
        "taste": row['Вкус'].capitalize(),
        "aroma": row['Ароматика'].capitalize()
    }

def format_hookah_result(hookahs, strength=None):
    if not hookahs:
        return "❌ Не удалось подобрать кальян."
    result = "🎉 Отталкиваясь от ваших ответов я смог подобрать лучший вариант!\n\n"
    for i, h in enumerate(hookahs, 1):
        result += f"━━━━━━━━━━━━━━━━━━━━━\n"
        result += f"🍃 Вариант {i}: {h['name']}\n"
        result += f"🏷️ Бренд: {h['brand']}\n"
        if strength and i == 1:
            result += f"🔥 Крепость: {strength}\n"
        else:
            result += f"🔥 Крепость: {h['strength']}\n"
        result += f"🍬 Вкус: {h['taste']}\n"
        result += f"🌸 Ароматика: {h['aroma']}\n"
    return result

# ================= ОБРАБОТЧИКИ КОМАНД =================

async def start(update, context):
    keyboard = [[KeyboardButton("🚀 Старт")]]
    await update.message.reply_text(
        "🌟 *Добро пожаловать в лаунж нового поколения — Танока!* 🌟\n\n"
        "Сегодня я подберу для вас идеальный кальян.\n"
        "Пожалуйста, ответьте на несколько моих вопросов.\n\n"
        "👇 Нажмите на кнопку *«Старт»*, чтобы начать.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return WELCOME

async def start_handler(update, context):
    context.user_data["hookahs"] = []
    context.user_data["full_df"] = df
    context.user_data["current_df"] = df.copy()
    context.user_data["selected_strength"] = None
    
    keyboard = [["Классический", "Сигарный лист"]]
    await update.message.reply_text(
        "📋 *Вопрос 1:* Какой кальян вы предпочтёте?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return BLAND

async def bland_handler(update, context):
    bland = update.message.text.lower()
    current = context.user_data.get("current_df", df)
    filtered = filter_by_bland(current, bland)
    context.user_data["current_df"] = filtered
    keyboard = [["Крепкий", "Выше среднего", "Средний", "Легкий"]]
    await update.message.reply_text(
        "📋 *Вопрос 2:* Какую крепость предпочитаете?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return STRENGTH

async def strength_handler(update, context):
    strength = update.message.text.lower()
    context.user_data["selected_strength"] = strength.capitalize()
    keyboard = [["Лимонад", "Глинтвейн", "Травяной чай", "Молочный коктейль"]]
    await update.message.reply_text(
        "📋 *Вопрос 3:* Какой напиток вы выберете?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return DRINK

async def drink_handler(update, context):
    drink = update.message.text.lower()
    current = context.user_data.get("current_df", df)
    filtered = filter_by_drink(current, drink)
    context.user_data["current_df"] = filtered
    keyboard = [["Отдых загородом", "Тропические страны", "Гранд-тур по мегаполисам"]]
    await update.message.reply_text(
        "📋 *Вопрос 4:* Куда бы вы отправились на отдых?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return TRIP

async def trip_handler(update, context):
    trip = update.message.text.lower()
    current = context.user_data.get("current_df", df)
    full = context.user_data.get("full_df", df)
    filtered = filter_by_trip(current, trip)
    context.user_data["current_df"] = filtered
    
    hookah = get_random_hookah(filtered, full)
    context.user_data["hookahs"] = [hookah]
    
    strength = context.user_data.get("selected_strength", "")
    result = format_hookah_result([hookah], strength)
    
    keyboard = [["✅ Подтвердить вкус", "🔄 Перезагрузка вкуса"]]
    await update.message.reply_text(
        result,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return RESULT

async def result_handler(update, context):
    choice = update.message.text.lower()
    if "перезагрузка" in choice:
        await update.message.reply_text("🔄 Начинаем подбор заново!", reply_markup=ReplyKeyboardMarkup([["🚀 Старт"]], resize_keyboard=True))
        return WELCOME
    else:
        keyboard = [["Да", "Нет"]]
        await update.message.reply_text(
            "📋 *Добавить еще один вкус?*",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
            parse_mode="Markdown"
        )
        return ADD_MORE

async def add_more_handler(update, context):
    choice = update.message.text.lower()
    if choice == "нет":
        hookahs = context.user_data.get("hookahs", [])
        result = format_hookah_result(hookahs)
        keyboard = [[KeyboardButton("🔄 Начать заново")]]
        await update.message.reply_text(
            "🌟 *Благодарим за ответы!*\n\n" + result,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    else:
        keyboard = [["Куба", "Тайланд", "Индия", "Россия", "Франция"]]
        await update.message.reply_text(
            "📋 *Какую страну ты выберешь?*",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
            parse_mode="Markdown"
        )
        return COUNTRY

async def country_handler(update, context):
    country = update.message.text.lower()
    full = context.user_data.get("full_df", df)
    current = context.user_data.get("current_df", df)
    
    filtered = filter_by_country(current, country)
    if filtered.empty:
        filtered = filter_by_country(full, country)
    
    context.user_data["current_df"] = filtered
    
    hookah = get_random_hookah(filtered, full)
    hookahs = context.user_data.get("hookahs", [])
    hookahs.append(hookah)
    context.user_data["hookahs"] = hookahs
    
    strength = context.user_data.get("selected_strength", "")
    result = format_hookah_result(hookahs, strength)
    
    keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        result + "\n\n📋 *Добавить еще один вкус?*",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return ADD_MORE_2

async def add_more_2_handler(update, context):
    choice = update.message.text.lower()
    
    if choice == "нет":
        hookahs = context.user_data.get("hookahs", [])
        result = format_hookah_result(hookahs)
        keyboard = [[KeyboardButton("🔄 Начать заново")]]
        await update.message.reply_text(
            "🌟 *Благодарим за ответы!*\n\n" + result,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    else:
        picture_url = "https://raw.githubusercontent.com/tanoka306/hookah-bot/main/pic_collage.jpg"
        
        await update.message.reply_photo(
            photo=picture_url,
            caption="🖼️ *Какая картинка вам нравится больше всего?*\n\nВыберите цифру: 1, 2, 3 или 4",
            parse_mode="Markdown"
        )
        
        keyboard = [["1", "2", "3", "4"]]
        await update.message.reply_text(
            "Выберите цифру: 1, 2, 3 или 4",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return PICTURE

async def picture_handler(update, context):
    picture = update.message.text.lower()
    full = context.user_data.get("full_df", df)
    current = context.user_data.get("current_df", df)
    
    filtered = filter_by_picture(current, picture)
    if filtered.empty:
        filtered = filter_by_picture(full, picture)
    
    hookah = get_random_hookah(filtered, full)
    hookahs = context.user_data.get("hookahs", [])
    hookahs.append(hookah)
    context.user_data["hookahs"] = hookahs
    
    strength = context.user_data.get("selected_strength", "")
    result = format_hookah_result(hookahs, strength)
    
    keyboard = [[KeyboardButton("🔄 Начать заново")]]
    await update.message.reply_text(
        "🌟 *Благодарим за ответы!*\n\n" + result,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def restart_handler(update, context):
    keyboard = [[KeyboardButton("🚀 Старт")]]
    await update.message.reply_text(
        "🌟 *Добро пожаловать в лаунж нового поколения — Танока!* 🌟\n\n"
        "Сегодня я подберу для вас идеальный кальян.\n"
        "Пожалуйста, ответьте на несколько моих вопросов.\n\n"
        "👇 Нажмите на кнопку *«Старт»*, чтобы начать.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return WELCOME

async def cancel(update, context):
    await update.message.reply_text("👋 До встречи!")
    return ConversationHandler.END

# ================= ЗАПУСК =================
def main():
    if df is None:
        print("❌ Ошибка: не загружен файл tanaka.xls")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WELCOME: [
                MessageHandler(filters.Text("🚀 Старт"), start_handler),
                MessageHandler(filters.Text("🔄 Начать заново"), restart_handler)
            ],
            BLAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, bland_handler)],
            STRENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, strength_handler)],
            DRINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, drink_handler)],
            TRIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, trip_handler)],
            RESULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, result_handler)],
            ADD_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_more_handler)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, country_handler)],
            ADD_MORE_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_more_2_handler)],
            PICTURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, picture_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv)
    
    print("🤖 Бот запущен в режиме polling!")
    application.run_polling()

if __name__ == "__main__":
    main()
