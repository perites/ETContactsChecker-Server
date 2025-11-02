import json
import logging

from peewee import (
    SqliteDatabase,
    Model,
    TextField,
    IntegerField,
    DateTimeField
)

DB_PATH = "app_data.sqlite3"
database = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = database


class ContractData(BaseModel):
    name = TextField()
    author_google_id = TextField()
    slack_users_ids_raw = TextField()
    sfmc_subdomain = TextField()
    client_id = TextField()
    client_secret = TextField()
    de_key = TextField()
    contacts_limit = IntegerField()
    contacts_amount = IntegerField()
    last_checked = DateTimeField(null=True)

    @property
    def slack_users_ids(self):
        return json.loads(self.slack_users_ids_raw)

    @slack_users_ids.setter
    def slack_users_ids(self, value):
        self.slack_users_ids_raw = json.dumps(value)


# -----------------------------
# Helper functions
# -----------------------------
def create_tables():
    with database:
        database.create_tables([ContractData])


def drop_tables():
    with database:
        database.drop_tables([ContractData])


if __name__ == "__main__":
    create_tables()
    logging.info("Tables created")
