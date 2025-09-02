from database.models import async_session
from database.models import User, Gaid, Kurs
from sqlalchemy import select, text
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("add_data.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def set_user(tg_id, tg_name):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id,tg_name=tg_name))
            await session.commit()


async def get_users():
    async with async_session() as session:
        return await session.scalars(select(User))
    

async def set_active(tg_id, active):
    async with async_session() as session:
        newstate = text("UPDATE users SET active=:active WHERE tg_id=:tg_id")
        newstate = newstate.bindparams(tg_id=tg_id, active=active)
        await session.execute(newstate)
        await session.commit()


async def add_gaid(name_fail_gaid, photo_gaid, description_gaid, fail_gaid, price_card_gaid, price_star_gaid):
    async with async_session() as session:
        session.add(Gaid(name_fail_gaid=name_fail_gaid, photo_gaid=photo_gaid, description_gaid=description_gaid, fail_gaid=fail_gaid, price_card_gaid=price_card_gaid, price_star_gaid=price_star_gaid))
        await session.commit()

    
async def add_kurs(name_fail_kurs, photo_kurs, description_kurs, fail_kurs, price_card_kurs, price_star_kurs):
    async with async_session() as session:
        session.add(Kurs(name_fail_kurs=name_fail_kurs, photo_kurs=photo_kurs, description_kurs=description_kurs, fail_kurs=fail_kurs, price_card_kurs=price_card_kurs, price_star_kurs=price_star_kurs))
        await session.commit()


async def select_gaid():
    async with async_session() as session:
        return await session.scalars(select(Gaid))
    

async def select_kurs():
    async with async_session() as session:
        return await session.scalars(select(Kurs))
    

async def get_gaid(selection_id):
    async with async_session() as session:
        result = await session.scalars(select(Gaid).where(Gaid.name_fail_gaid == selection_id))
        return result.all()
    

async def get_kurs(selection_id):
    async with async_session() as session:
        result = await session.scalars(select(Kurs).where(Kurs.name_fail_kurs == selection_id))
        return result.all()
    

async def proverka_gaids():
    async with async_session() as session:
        return await session.scalar(select(Gaid.id))
    

async def proverka_kurss():
    async with async_session() as session:
        return await session.scalar(select(Kurs.id))
    

async def drop_table_gaid(selection_id):
    async with async_session() as session:
        namegaid = await session.scalars(select(Gaid).where(Gaid.name_fail_gaid == selection_id))
        for gaid in namegaid:
            await session.delete(gaid)
        await session.commit()


async def drop_table_kurs(selection_id):
    async with async_session() as session:
        namekurs = await session.scalars(select(Kurs).where(Kurs.name_fail_kurs == selection_id))
        for kurs in namekurs:
            await session.delete(kurs)
        await session.commit()
