"""A simple example of connecting to Earth Engine using App Engine."""



# Works in the local development environment and when deployed.
# If successful, shows a single web page with the SRTM DEM
# displayed in a Google Map.  See accompanying README file for
# instructions on how to set up authentication.

import os

# TO DO: uncomment all initialization code later when actually authenticating

import config
import ee
import jinja2
import webapp2
import json

from google.appengine.ext import ndb

from summary_stats import SummaryStats

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class RBDPage(webapp2.RequestHandler):
  def initData(self):
    self.regions = {'afr': 'GME/images/13831694222710742720-06060588760989137524',
                    'aus': 'GME/images/13831694222710742720-18217876338472823932',
                    'cam': 'GME/images/13831694222710742720-04328481494314888890',
                    'eur': 'GME/images/13831694222710742720-03516536627963450262',
                    'mid': 'GME/images/13831694222710742720-15376670774087721723',
                    'nam': 'GME/images/13831694222710742720-02094782379573228579',
                    'pac': 'GME/images/13831694222710742720-14125439452667326560',
                    'sea': 'GME/images/13831694222710742720-04010150827404158855',
                    'sam': 'GME/images/13831694222710742720-00076760469739156288',
                    'stp': 'GME/images/13831694222710742720-05302187767333437806',
                    'glo': ''}

    self.layers = {'rem': 'GME/images/13831694222710742720-05809997748937958690',
                   'bdp': 'GME/images/13831694222710742720-17643117795501624396',
                   'bda': 'GME/images/13831694222710742720-01677512005004143246',
                   'bdb': 'GME/images/13831694222710742720-13464369061086462890',
                   'bdm': 'GME/images/13831694222710742720-10734434487272614892',
                   'endp': 'GME/images/13831694222710742720-14182859561222861561',
                   'endv': 'GME/images/13831694222710742720-02664411750483227641'}
    
  def get(self):
    self.response.out.write('')

  def getPixelValues(self, filterVals, region):
    #minRem, minBDP, minBDA, minBDB, minBDM, minEndP, minEndV, region):
    #for now, just use global data always
    #convert raw minima to 0-255 range
    
    stats = SummaryStats.query(SummaryStats.region==region).fetch()
    pixelVals = {}
    for stat in stats:
      pixelVals[stat.layer] = min(max((filterVals[stat.layer] - stat.min)/(stat.max-stat.min)*255, 0), 255)

    return(pixelVals)

    #generally, use (value - min)/(max-min)*255
    #where max, min are metric + region specific
    #minRem = min(max((minVals['rem'] - 0)/(108536-0)*255, 0), 255)
    #minBDP = min(max((minVals['bdp'] - 0)/(5019-0)*255, 0), 255)
    #minBDA = min(max((minVals['bda'] - 0)/(174-0)*255, 0), 255)
    #minBDB = min(max((minVals['bdb'] - 0)/(956-0)*255, 0), 255)
    #minBDM = min(max((minVals['bdm'] - 0)/(254-0)*255, 0), 255)
    #minEndP = min(max((minVals['endp'] - 1)/(1350-1)*255, 0), 255)
    #minEndV = min(max((minVals['endv'] - 4)/(1210.4-4)*255, 0), 255)
    #return (minRem, minBDP, minBDA, minBDB, minBDM, minEndP, minEndV)

  def getLayer(self, pixelVals, region):
    #load underlying data
    #srtm = ee.Image('CGIAR/SRTM90_V4')

    bdAmph = ee.Image('GME/images/13831694222710742720-01677512005004143246')
    bdBird = ee.Image('GME/images/13831694222710742720-13464369061086462890')
    bdMamm = ee.Image('GME/images/13831694222710742720-10734434487272614892')
    bdPlant = ee.Image('GME/images/13831694222710742720-17643117795501624396')
    endP = ee.Image('GME/images/13831694222710742720-14182859561222861561')
    endV = ee.Image('GME/images/13831694222710742720-02664411750483227641')
    #original, 7 level image for remoteness
    #rem = ee.Image('GME/images/13831694222710742720-04617895392534889421')

    #new, minute-based image for remoteness
    rem = ee.Image('GME/images/13831694222710742720-05809997748937958690')
    #use underlying data to generate mask
    blank = ee.Image(0)
    #output = blank.where(srtm.lte(4500).And(bdGlobal.gte(minBDP)), 1)
    #output = blank.where(srtm.gte(elev),1)
    crit = bdAmph.gte(pixelVals['bda'])
    crit = crit.And(bdBird.gte(pixelVals['bdb']))
    crit = crit.And(bdMamm.gte(pixelVals['bdm']))
    crit = crit.And(bdPlant.gte(pixelVals['bdp']))
    crit = crit.And(rem.gte(pixelVals['rem']))
    crit = crit.And(endP.gte(pixelVals['endp']))
    crit = crit.And(endV.gte(pixelVals['endv']))

    #clip to region
    if(not region=="glo"):
      regionMask = ee.Image(self.regions[region])
      crit = crit.And(regionMask.gte(1))

    output = blank.where(crit, 1)
    output = output.mask(output)



    mapid = output.getMapId({'palette': '66FF33'})    
    template_values = {
        'mapid': mapid['mapid'],
        'token': mapid['token']
    }
    return(template_values)    

class MainPage(RBDPage):
  def get(self):                             # pylint: disable=g-bad-name
    """Generate the homepage for the project"""
    ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
    self.initData()
    
    #DEFAULT VIEW: generate mask with filters set to +1SD 
    #except remoteness, which we set at 1
    stats = SummaryStats.query(SummaryStats.region=="glo").fetch()
    filtValues = {}
    for stat in stats:
      if(not stat.layer == "rem"):
        filtValues[stat.layer] = stat.mean + stat.sd
      else:
        filtValues[stat.layer] = 1


    pixelVals = self.getPixelValues(filtValues, "glo")               #Global scope
    template_values = self.getLayer(pixelVals, "glo")
    
    allStats = {}
    for region in self.regions.keys():
      allStats[region] = {}
      for layer in self.layers.keys():
        allStats[region][layer] = {}
    
    ndbStats = SummaryStats.query().fetch()
    for stat in ndbStats:
      allStats[stat.region][stat.layer]["mean"] = stat.mean
      allStats[stat.region][stat.layer]["sd"] = stat.sd
    template_values['stats'] = json.dumps(allStats)
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

class SliderHandler(RBDPage):
  def get(self):
    """Generate a mask with areas satisfying all of the provided criteria
       and provide the necessary map id and token as json."""
    ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
    self.initData()
    #to do: error handling
    filterVals = {}
    filterVals['rem']  = float(self.request.get('minRem'))
    filterVals['bdp']  = float(self.request.get('minBDP'))
    filterVals['bda']  = float(self.request.get('minBDA'))
    filterVals['bdb']  = float(self.request.get('minBDB'))
    filterVals['bdm']  = float(self.request.get('minBDM'))
    filterVals['endp'] = float(self.request.get('minEndP'))
    filterVals['endv'] = float(self.request.get('minEndV'))

    region = self.request.get('region');

    #convert raw filter values to pixel values
    pixelVals = self.getPixelValues(filterVals, region)
                                                                      
    #get info for display using filters
    template_values = self.getLayer(pixelVals, region)
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(template_values))

class StatsHandler(RBDPage):
  def get(self):
    """ Update all the means and standard deviations per layer and region"""
    ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
    self.initData()

    targetRegion = self.request.get('region')
    if(not targetRegion == ""):
      self.updateRegion(targetRegion)
    else:
      for regionKey in self.regions.keys():
        self.updateRegion(regionKey)

  def updateRegion(self, regionKey):
    for layerKey in self.layers.keys():
      self.updateRegionLayer(regionKey, layerKey)

                           
  def updateRegionLayer(self, regionKey, layerKey):
    #regionAssetId = self.regions[regionKey]
    #layerImage = ee.Image(self.layers[layerKey])
    #mask if there is an actual region asset
    #if(not regionAssetId==""):
    #  regionImage = ee.Image(regionAssetId)
    #  maskedLayer = layerImage.mask(regionImage)
    #otherwise, it's global, and we head straight for mean/sd calcs
    #else:
    #  maskedLayer = layerImage

    #meanReducer = ee.call("Reducer.mean")
    #sdReducer = ee.call("Reducer.stdDev")
    #layerMean = maskedLayer.reduceRegion(meanReducer).getInfo()['b1']
    #layerSD = maskedLayer.reduceRegion(sdReducer).getInfo()['b1']
    
    globalStats = SummaryStats.query(SummaryStats.region=="glo", SummaryStats.layer==layerKey).fetch()[0]
    
    sumStat = SummaryStats(layer=layerKey,
                           region=regionKey,
                           mean=globalStats.mean,
                           sd=globalStats.sd, 
                           min=globalStats.min,
                           max=globalStats.max)
    sumStat.put()

app = webapp2.WSGIApplication([('/', MainPage), ('/slider',SliderHandler), ('/updateLayerStats', StatsHandler)], debug=True)
