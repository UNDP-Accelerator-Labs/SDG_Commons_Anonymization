from os import environ, listdir
from os.path import join, isfile

import logging
import psycopg2
from psycopg2.extras import LoggingConnection
from psycopg2.extensions import connection as connectionType
from psycopg2.sql import SQL, Identifier

import re
import json

class psqlTable:
  def __init__ (self, db_name):
    dbinfo = {
      'database': db_name,
      'password': environ['DB_PORT'],
      'host': environ['DB_HOST'],
      'user': environ['DB_USERNAME'],
      'password': environ['DB_PASSWORD'],
    }
    if environ['LOG_SQL'] == True:
      logging.basicConfig(level=logging.DEBUG)
      logger = logging.getLogger(__name__)
      conn: connectionType = psycopg2.connect(connection_factory=LoggingConnection, **dbinfo)
      self.conn.initialize(logger)
    else:
      self.conn: connectionType = psycopg2.connect(**dbinfo)
    self.conn.autocommit = True

  def selectAll (self, tableName):
    """
    See example here: https://wiki.postgresql.org/wiki/Using_psycopg2_with_PostgreSQL
    """
    curr = self.conn.cursor()
    curr.execute(SQL('SELECT * FROM {}').format(Identifier(tableName)))
    # SQL("INSERT INTO {} VALUES (%s)").format(Identifier('numbers')), (10,)
    try:
      columns = [d[0] for d in curr.description]
      return (columns, curr.fetchall())
    except:
      return (None, None)

  def execute (self, query:str, params:tuple = ()):
    curr = self.conn.cursor()
    curr.execute(query, params)
    try:
      columns = [d[0] for d in curr.description]
      return (columns, curr.fetchall())
    except:
      return (None, None)

  def close (self):
    self.conn.close()

def getData(source_dir:str) -> list:
  data = []
  for f in listdir(source_dir):
    if isfile(join(source_dir, f)) and f != '.DS_Store':
      data.append(json.loads(open(join(source_dir, f)).read()))
  return data

def getContactDetails(text:str) -> dict[str]:
  if text is not None:
    ## Remove email addresses (comprehensive pattern)
    emails = re.findall(r"[A-Za-z0-9\._%+-]*@[A-Za-z0-9\.-]*\.[A-Za-z]{2,}", text, flags=re.IGNORECASE)
    """
    Remove phone numbers with various formats:
    - International format: +1234567890, +1 234 567 890, +1-234-567-890
    - Local format: (123) 456-7890, 123-456-7890, 123.456.7890
    - Plain digits: 1234567890 (8+ digits)
    """
    phones = re.findall(r"(?<![\/\.-])\b(\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})", text)
    return emails + phones
  else:
    return []
  