from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///catalogdb.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

User1 = User(name="Maha", email="maho,th16@gmail.com")
session.add(User1)
session.commit()

category1 = Category(name="Soccer")

session.add(category1)
session.commit()

Item1 = Item(user_id=1, name="Shinguards",
             description="""piece of equipment worn on the front of a player’s
                          shin to protect them from injury""",
             category=category1)

session.add(Item1)
session.commit()


Item2 = Item(user_id=1, name="Two Shinguards",
             description="""piece of equipment worn on the front of a player’s
                          shin to protect them from injury""",
             category=category1)

session.add(Item2)
session.commit()

item3 = Item(user_id=1, name="soccer cleats", description="shoes for soccer",
             category=category1)

session.add(item3)
session.commit()

item4 = Item(user_id=1, name="Jersy", description="Team uniforms",
             category=category1)

session.add(item4)
session.commit()


category2 = Category(user_id=1, name="Basketball")

session.add(category2)
session.commit()


category3 = Category(user_id=1, name="Baseball")

session.add(category3)
session.commit()

item1 = Item(user_id=1, name="Bat", description="The bat",
             category=category3)

session.add(item1)
session.commit()

category4 = Category(user_id=1, name="Frisbee")

session.add(category4)
session.commit()

category10 = Category(user_id=1, name="Hang gliding")

session.add(category10)
session.commit()

category5 = Category(user_id=1, name="Snowboarding")

session.add(category5)
session.commit()

item1 = Item(user_id=1, name="Snowboard",
             description="""boards where both feet are
                          secured to the same board""",
             category=category5)

session.add(item1)
session.commit()

item2 = Item(user_id=1, name="Goggles", description="The glasses",
             category=category5)

session.add(item2)
session.commit()

category6 = Category(user_id=1, name="Rock Climbing")

session.add(category6)
session.commit()

category7 = Category(user_id=1, name="Foosball")

session.add(category7)
session.commit()

category8 = Category(user_id=1, name="Skating")

session.add(category8)
session.commit()

category9 = Category(user_id=1, name="Hockey")

session.add(category9)
session.commit()

item1 = Item(user_id=1, name="Stick", description="The stick",
             category=category9)

session.add(item1)
session.commit()

print("added menu items!")
