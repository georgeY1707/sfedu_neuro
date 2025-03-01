import json
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
import requests
import matplotlib.pyplot as plt


class TgBot:
    def __init__(self):
        super().__init__()

        self.history = []

        # Настройка логирования
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )

        # Состояния для ConversationHandler
        self.CHOOSING, self.TYPING_ANSWER = range(2)

        # Данные о факультете (заглушки)
        self.faculty_info = {
            "история": self.get_text('resource/history.txt'),
            "кафедры": self.get_text('resource/cafedri.txt'),
            "преподаватели": self.get_text('resource/teachers.txt'),
            "направления": self.get_text('resource/directions.txt'),
            "поступление": self.get_text('resource/entrance.txt'),
            "бюджет": self.get_text('resource/budget.txt'),
            "адрес": self.get_text('resource/address.txt'),
            "мероприятия": self.get_text('resource/events.txt')
        }

        # Клавиатура для выбора категорий
        reply_keyboard = [
            ["История", "Кафедры", "Преподаватели"],
            ["Направления", "Поступление", "Бюджет"],
            ["Адрес", "Мероприятия", "График поступлений"]
        ]
        self.markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    def get_text(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()

    # Старт бота
    async def start(self, update: Update, context):
        await update.message.reply_text(
            "Привет! Я твой помощник по вопросам учебы и поступления. "
            "Выбери категорию, чтобы получить информацию:",
            reply_markup=self.markup
        )
        return self.CHOOSING

    # Обработка выбора категории
    async def choose_category(self, update: Update, context):
        text = update.message.text.lower()

        if text == 'график поступлений':
            await self.graff(update)
        elif text == 'преподаватели':
            list_ = self.faculty_info[text].split('\n')
            for i in range(0, len(list_), 20):
                s = ''
                try:
                    for j in range(20):
                        s = s + "\n" + list_[i + j]
                except:
                    s = list_[i:]
                    s = '\n'.join(s)
                await update.message.reply_text(s, parse_mode="HTML")
            await update.message.reply_text('Список преподователей также можно посмотреть <a href="http://www.mmcs.sfedu.ru/faculty/staff">здесь</a>', parse_mode="HTML")
        elif text in self.faculty_info:
            await update.message.reply_text(self.faculty_info[text], parse_mode="HTML")
        else:
            await update.message.reply_text(self.ai_ansver(text))
        return self.CHOOSING

    # Отмена
    async def cancel(self, update: Update, context):
        await update.message.reply_text("До свидания! Если нужно, просто нажми /start.")
        return ConversationHandler.END

    def run(self):
        # Создаем приложение бота
        application = ApplicationBuilder().token("7570190716:AAHeUzn2tG8QFaOe8mlE6ipKkDGOXa1KeG4").build()

        # Обработчик диалога
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                self.CHOOSING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.choose_category)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        # Добавляем обработчик в приложение
        application.add_handler(conv_handler)

        # Запуск бота
        application.run_polling()

    async def graff(self, update: Update):
        # Пример данных: годы и количество поступивших студентов
        years = [2018, 2019, 2020, 2021, 2022, 2023]
        admissions = [1500, 1600, 1700, 1800, 1900, 2000]  # Примерные данные

        # Создание графика
        plt.figure(figsize=(10, 6))
        plt.plot(years, admissions, marker='o', linestyle='-', color='b')

        # Настройка графика
        plt.title('Количество поступивших на платное обучение в ЮФУ')
        plt.xlabel('Год')
        plt.ylabel('Количество поступивших студентов')
        plt.xticks(years)  # Установка меток по оси X
        plt.grid(True)

        # Сохранение графика
        plt.savefig('resource/admissions_graph.png')
        plt.close()

        # Отправка графика в Telegram
        await update.message.reply_photo(photo=open('resource/admissions_graph.png', 'rb'))

    def ai_ansver(self, text):
        self.history.append("user:" + text)

        prompt = {
            "modelUri": "gpt://b1g1hrqgd7lvvch2499s/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "system",
                    "text": """Должен общаться в дружелюбной и уважительной манере.
                                Ты общаешься с абитуриентом, который хочет поступиться в ЮФУ
                                или студентом, который уже обучается в ЮФУ. К запросу прилагается диалог нужно ответить
                                в контексте диалога"""
                },
                {
                    "role": "user",
                    "text": "\n".join(self.history) + '\n---------------\n' + str(text)
                }
            ]
        }  # шаблон запроса для нейросети

        url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Api-Key AQVN33DOKM5m3eR9prsoE7tmZaNNfG0Agb88OrU0  "
        }

        response = requests.post(url, headers=headers, json=prompt)  # отправка запроса и получение ответа
        data = json.loads(
            response.text)  # дальнейщшие сточки кода преобразуют json объект с данными транзакции в словарь
        result = data['result']['alternatives'][0]['message']['text']
        self.history.append('system:' + result)
        return result


tg_bot = TgBot()
tg_bot.run()