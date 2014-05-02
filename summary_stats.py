""" Simple class for storing summary stats per layer per region
"""

from google.appengine.ext import ndb


class SummaryStats(ndb.Model):
  layer = ndb.StringProperty(required=True)
  region = ndb.StringProperty(required=True)
  mean = ndb.FloatProperty(required=True)
  sd = ndb.FloatProperty(required=True)
  min = ndb.FloatProperty(required=True)
  max = ndb.FloatProperty(required=True)
