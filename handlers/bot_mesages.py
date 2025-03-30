from aiogram import types, Router
import keyboards
from data.subloader import get_json

router =Router()

@router.message()
async def echo(message: types.Message):
    msg = message.text.lower()
    smiles = await get_json("smiles.json")

    if msg == "ссылки":
        await message.answer("Вот ваши ссылки", reply_markup=keyboards.inline.links)
    elif msg == "спец. кнопки":
        await message.answer("Спец кнопки:", reply_markup=keyboards.reply.spec)
    elif msg == "калькулятор":
        await  message.answer("Калькулятор", reply_markup=keyboards.builders.calc())
    elif msg == "назад":
        await message.answer("Главное меню", reply_markup=keyboards.reply.main)
    elif msg == "смайлики":
        await message.answer(f"{smiles[0][0]} <b>{smiles[0][1]}</b>", reply_markup=keyboards.fabrics.paginator())
    else:
        await message.answer("I dont understand you")