from aiogram import F, types, Router
from aiogram.exceptions import TelegramBadRequest
from contextlib import suppress
import keyboards
from data.subloader import get_json

router = Router()

@router.callback_query(keyboards.fabrics.Pagination.filter(F.action.in_(["prev", "next"])))
async def pagination_handler(call: types.CallbackQuery, callback_data: keyboards.fabrics.Pagination):
    smiles = await get_json("smiles.json")
    page_num = int(callback_data.page)
    page = page_num - 1 if page_num > 0 else 0

    if callback_data.action == "next":
        page = page_num + 1 if page_num < (len(smiles) - 1) else page_num

    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            f"{smiles[page][0]} <b>{smiles[page][1]}</b>",
            reply_markup=keyboards.fabrics.paginator(page)
        )
    await call.answer()