from database.models import async_session
from database.models import User, Gaid, Kurs
from sqlalchemy import select, text, update


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
    

# async def select_gaidid():
#     async with async_session() as session:
#         return await session.scalar(select(User.gaidid))
    

# async def updateinfogaidid(tg_id, user_gaids):
#     async with async_session() as session:
#         stmt = text("UPDATE users SET gaidid=:gaidid WHERE tg_id=:tg_id")
#         stmt = stmt.bindparams(tg_id=tg_id, gaidid=user_gaids)
#         await session.execute(stmt)
#         await session.commit()


async def addgaid(namefail, photo, descriptiongaid, fail, pricecardgaid, pricestargaid):
    async with async_session() as session:
        session.add(Gaid(namefail=namefail, photo=photo, descriptiongaid=descriptiongaid, fail=fail, pricecardgaid=pricecardgaid, pricestargaid=pricestargaid))
        await session.commit()

    
async def addkurs(nameurl, descriptionkurs, url, pricecardkurs, pricestarkurs):
    async with async_session() as session:
        session.add(Kurs(nameurl=nameurl, url=url, descriptionkurs=descriptionkurs, pricecardkurs=pricecardkurs, pricestarkurs=pricestarkurs))
        await session.commit()


async def select_gaid():
    async with async_session() as session:
        return await session.scalars(select(Gaid))
    

async def select_kurs():
    async with async_session() as session:
        return await session.scalars(select(Kurs))
    

async def get_gaid(getgaid):
    async with async_session() as session:
        result = await session.scalars(select(Gaid).where(Gaid.namefail == getgaid))
        return result
    

async def proverka_gaids():
    async with async_session() as session:
        return await session.scalar(select(Gaid.id))
    

async def get_kurs(selectkurs):
    async with async_session() as session:
        result = await session.scalars(select(Kurs).where(Kurs.nameurl == selectkurs))
        return result
    

async def proverka_kurss():
    async with async_session() as session:
        return await session.scalar(select(Kurs.id))
    

async def droptablegaid(delitintgaid):
    async with async_session() as session:
        namegaid = await session.scalars(select(Gaid).where(Gaid.id == delitintgaid))
        for gaid in namegaid:
            await session.delete(gaid)
        await session.commit()


async def droptablekurs(delitintkurs):
    async with async_session() as session:
        namekurs = await session.scalars(select(Kurs).where(Kurs.id == delitintkurs))
        for kurs in namekurs:
            await session.delete(kurs)
        await session.commit()
