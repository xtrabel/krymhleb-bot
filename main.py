from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router
from aiogram.filters import Command
import config
import os
import re

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Счётчики
complaint_counter = 1
collaboration_counter = 1

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Подача жалобы")],
        [KeyboardButton(text="🤝 Подача заявки о сотрудничестве")],
        [KeyboardButton(text="📄 Запросить актуальный прайс")],
        [KeyboardButton(text="☎️ Контакты ТП и РУ")],
        [KeyboardButton(text="🆕 Новости")],
        [KeyboardButton(text="🛒 Сделать заказ")]
    ],
    resize_keyboard=True
)

# Кнопка для заказа через сайт
order_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Перейти на сайт для оформления заказа", url="http://zakaz.krymhleb.ru/login")]
    ]
)

# Кнопки отмены
cancel_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)

confirm_cancel_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Да"), KeyboardButton(text="↩️ Нет")]],
    resize_keyboard=True
)

payment_form_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Безналичный расчет")],
        [KeyboardButton(text="💵 Наличный расчет")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)

user_data = {}
admin_broadcast_text = {}
# Команда /start
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = str(message.from_user.id)

    # Сохраняем ID в файл users.txt
    if not os.path.exists("users.txt"):
        with open("users.txt", "w") as f:
            f.write(user_id + "\n")
    else:
        with open("users.txt", "r") as f:
            users = f.read().splitlines()
        if user_id not in users:
            with open("users.txt", "a") as f:
                f.write(user_id + "\n")

    user_data.pop(message.from_user.id, None)
    await message.answer(
        "Добро пожаловать в АО 'КрымХлеб'!\n\nВыберите нужный раздел:",
        reply_markup=main_menu
    )

# Универсальная отмена
@router.message(lambda message: message.text == "❌ Отмена")
async def cancel_action(message: types.Message):
    user_data.pop(message.from_user.id, None)
    await message.answer("✅ Операция отменена. Возвращаю в главное меню.", reply_markup=main_menu)

# Открытие сайта заказа
@router.message(lambda message: message.text == "🛒 Сделать заказ")
async def open_order_site(message: types.Message):
    await message.answer(
        "Нажмите кнопку ниже, чтобы перейти на сайт и оформить заказ:",
        reply_markup=order_button
    )

# ---------------- Подача жалобы ----------------

@router.message(lambda message: message.text == "📢 Подача жалобы")
async def complaint_start(message: types.Message):
    user_data[message.from_user.id] = {"step": "complaint_ip"}
    await message.answer("Введите название ИП или контракта:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "complaint_ip")
async def complaint_ip(message: types.Message):
    user_data[message.from_user.id]["ip_name"] = message.text
    user_data[message.from_user.id]["step"] = "complaint_datetime"
    await message.answer("Введите дату и время происшествия:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "complaint_datetime")
async def complaint_datetime(message: types.Message):
    user_data[message.from_user.id]["datetime"] = message.text
    user_data[message.from_user.id]["step"] = "complaint_text"
    await message.answer("Опишите суть жалобы:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "complaint_text")
async def complaint_text(message: types.Message):
    user_data[message.from_user.id]["description"] = message.text
    user_data[message.from_user.id]["step"] = "complaint_photo_question"
    await message.answer("Хотите приложить фото к жалобе?", reply_markup=confirm_cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "complaint_photo_question")
async def complaint_photo_question(message: types.Message):
    if message.text == "✅ Да":
        user_data[message.from_user.id]["step"] = "complaint_photo_upload"
        await message.answer("Отправьте фото:", reply_markup=cancel_menu)
    else:
        await send_complaint(message)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "complaint_photo_upload")
async def complaint_photo_upload(message: types.Message):
    if message.photo:
        user_data[message.from_user.id]["photo"] = message.photo[-1].file_id
    await send_complaint(message)

async def send_complaint(message: types.Message):
    global complaint_counter
    data = user_data.pop(message.from_user.id, {})
    text = (
        f"‼️ Жалоба №{complaint_counter}\n\n"
        f"ИП/Контракт: {data.get('ip_name')}\n"
        f"Дата и время: {data.get('datetime')}\n"
        f"Описание: {data.get('description')}"
    )
    if "photo" in data:
        await bot.send_photo(config.REPORT_CHAT_ID, data["photo"], caption=text)
    else:
        await bot.send_message(config.REPORT_CHAT_ID, text)

    complaint_counter += 1
    await message.answer("✅ Ваша жалоба принята и передана руководству.", reply_markup=main_menu)
# ---------------- Подача заявки о сотрудничестве ----------------

@router.message(lambda message: message.text == "🤝 Подача заявки о сотрудничестве")
async def collaboration_start(message: types.Message):
    user_data[message.from_user.id] = {"step": "choose_payment"}
    await message.answer("Выберите форму оплаты:", reply_markup=payment_form_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "choose_payment")
async def choose_payment(message: types.Message):
    if message.text == "💳 Безналичный расчет":
        user_data[message.from_user.id]["payment_type"] = "Безналичный"
        user_data[message.from_user.id]["step"] = "partner_card"
        await message.answer("Отправьте фото или скан карточки партнера:", reply_markup=cancel_menu)
    elif message.text == "💵 Наличный расчет":
        user_data[message.from_user.id]["payment_type"] = "Наличный"
        user_data[message.from_user.id]["step"] = "contract_name"
        await message.answer("Введите название ИП или Контрагента:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "partner_card")
async def partner_card(message: types.Message):
    if message.photo:
        user_data[message.from_user.id]["partner_card_photo"] = message.photo[-1].file_id
        user_data[message.from_user.id]["step"] = "tax_certificate"
        await message.answer("Отправьте фото или скан выписки из налоговой:", reply_markup=cancel_menu)
    else:
        await message.answer("Пожалуйста, отправьте именно фото.", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "tax_certificate")
async def tax_certificate(message: types.Message):
    if message.photo:
        user_data[message.from_user.id]["tax_certificate_photo"] = message.photo[-1].file_id
        user_data[message.from_user.id]["step"] = "tax_system"
        await message.answer("На какой системе налогообложения находится ваш магазин?", reply_markup=cancel_menu)
    else:
        await message.answer("Пожалуйста, отправьте именно фото.", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "tax_system")
async def tax_system(message: types.Message):
    user_data[message.from_user.id]["tax_system"] = message.text
    user_data[message.from_user.id]["step"] = "contract_name"
    await message.answer("Введите название ИП или Контрагента:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "contract_name")
async def contract_name(message: types.Message):
    user_data[message.from_user.id]["contract_name"] = message.text
    user_data[message.from_user.id]["step"] = "address"
    await message.answer("Введите точный адрес магазина:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "address")
async def address(message: types.Message):
    user_data[message.from_user.id]["address"] = message.text
    user_data[message.from_user.id]["step"] = "work_time"
    await message.answer("Введите время работы магазина:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "work_time")
async def work_time(message: types.Message):
    user_data[message.from_user.id]["work_time"] = message.text
    user_data[message.from_user.id]["step"] = "contact_person"
    await message.answer("Введите Ф.И.О контактного лица:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "contact_person")
async def contact_person(message: types.Message):
    user_data[message.from_user.id]["contact_person"] = message.text
    user_data[message.from_user.id]["step"] = "phone_number"
    await message.answer("Введите номер телефона (разрешены +, -, скобки):", reply_markup=cancel_menu)
@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "phone_number")
async def phone_number(message: types.Message):
    global collaboration_counter
    if not re.fullmatch(r"[\d\-\+\(\)\s]+", message.text):
        await message.answer("❗ Введите корректный номер телефона (разрешены только цифры, +, -, пробелы и скобки)", reply_markup=cancel_menu)
        return

    data = user_data.pop(message.from_user.id, {})
    text = (
        f"📢 Заявка №{collaboration_counter}\n\n"
        f"ИП/Контрагент: {data.get('contract_name')}\n"
        f"Адрес: {data.get('address')}\n"
        f"Время работы: {data.get('work_time')}\n"
        f"Ф.И.О: {data.get('contact_person')}\n"
        f"Телефон: {message.text}\n"
        f"Форма оплаты: {data.get('payment_type')}\n"
        f"Система налогообложения: {data.get('tax_system', 'Не указана')}"
    )

    if "partner_card_photo" in data:
        await bot.send_photo(config.REPORT_CHAT_ID, data["partner_card_photo"], caption="Карточка партнера")
    if "tax_certificate_photo" in data:
        await bot.send_photo(config.REPORT_CHAT_ID, data["tax_certificate_photo"], caption="Выписка из налоговой")

    await bot.send_message(config.REPORT_CHAT_ID, text)
    collaboration_counter += 1
    await message.answer("✅ Спасибо! Ваша заявка принята и передана менеджеру.", reply_markup=main_menu)

# ---------------- Прайс ----------------

@router.message(lambda message: message.text == "📄 Запросить актуальный прайс")
async def request_price(message: types.Message):
    user_data[message.from_user.id] = {"step": "request_price_ip"}
    await message.answer("Введите название ИП или Контрагента:", reply_markup=cancel_menu)

@router.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "request_price_ip")
async def send_price(message: types.Message):
    if message.text == "❌ Отмена":
        user_data.pop(message.from_user.id, None)
        await message.answer("Запрос отменён. Возвращаю в главное меню.", reply_markup=main_menu)
        return

    ip_name = message.text
    try:
        price = FSInputFile(config.PRICE_FILE)
        await message.answer_document(price, caption="📄 Ваш актуальный прайс.", reply_markup=main_menu)
        await bot.send_message(config.REPORT_CHAT_ID, f"📄 Прайс был запрошен.\nИП/Контрагент: {ip_name}")
    except Exception as e:
        await message.answer(f"❗ Ошибка при отправке прайса: {e}")
    finally:
        user_data.pop(message.from_user.id, None)

# ---------------- Контакты и новости ----------------

@router.message(lambda message: message.text == "☎️ Контакты ТП и РУ")
async def show_contacts(message: types.Message):
    await message.answer(
        f"👨‍💼 ТП: {config.MANAGER_NAME}\nТелефон: {config.MANAGER_PHONE}\n\n"
        f"👔 Региональный управляющий: {config.REGIONAL_MANAGER_NAME}\nТелефон: {config.REGIONAL_MANAGER_PHONE}",
        reply_markup=main_menu
    )

@router.message(lambda message: message.text == "🆕 Новости")
async def show_news(message: types.Message):
    await message.answer(f"📰 Новости:\n\n{config.NEWS_TEXT}", reply_markup=main_menu)

# ---------------- Рассылка для админа ----------------

ADMIN_ID = config.ADMIN_ID

@router.message(Command("admin"))
async def admin_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    await message.answer("Введите текст рассылки:")
    admin_broadcast_text[message.from_user.id] = "waiting_for_text"

@router.message(lambda message: admin_broadcast_text.get(message.from_user.id) == "waiting_for_text")
async def admin_broadcast(message: types.Message):
    text = message.text
    admin_broadcast_text.pop(message.from_user.id)

    if not os.path.exists("users.txt"):
        await message.answer("Файл пользователей не найден.")
        return

    with open("users.txt", "r") as f:
        users = f.read().splitlines()

    sent_count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            sent_count += 1
        except Exception:
            continue

    await message.answer(f"✅ Рассылка завершена. Отправлено: {sent_count} пользователям.")

# ---------------- Запуск ----------------

dp.include_router(router)

if __name__ == "__main__":
    dp.run_polling(bot)
