from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///data/dbvoronkaasyabot.sqlite3')
# engine = create_async_engine(url='sqlite+aiosqlite:///dbvoronkaasyabot.sqlite3')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    tg_name = mapped_column(String(35))
    active = mapped_column(Integer, default=1)



class Gaid(Base):
    __tablename__ = 'gaid'

    id: Mapped[int] = mapped_column(primary_key=True)
    namefail = mapped_column(String(70))
    photo = mapped_column(String(300))
    descriptiongaid = mapped_column(String(300))
    fail = mapped_column(String(300))
    pricecardgaid = mapped_column(Integer())
    pricestargaid = mapped_column(Integer())


class Kurs(Base):
    __tablename__ = 'kurs'

    id: Mapped[int] = mapped_column(primary_key=True) 
    nameurl = mapped_column(String(70))
    descriptionkurs = mapped_column(String(300))
    url = mapped_column(String(300))
    pricecardkurs = mapped_column(Integer())
    pricestarkurs = mapped_column(Integer())


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)