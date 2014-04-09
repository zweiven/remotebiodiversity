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

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class RBDPage(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('')

  def getLayer(self, elev):
    blank = ee.Image(0)
    #mapid = ee.Image('CGIAR/SRTM90_V4').getMapId({'min': 0, 'max': 1000})
    srtm = ee.Image('CGIAR/SRTM90_V4')
    output = blank.where(srtm.gt(elev), 1)
    output = output.mask(output)
    mapid = output.getMapId()    
    template_values = {
        'mapid': mapid['mapid'],
        'token': mapid['token']
    }
    return(template_values)    

class MainPage(RBDPage):
  def get(self):                             # pylint: disable=g-bad-name
    """Request an image from Earth Engine and render it to a web page."""
    ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)

    # These could be put directly into template.render, but it
    # helps make the script more readable to pull them out here, especially
    # if this is expanded to include more variables.

    template_values = self.getLayer(0)
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

class SliderHandler(RBDPage):
  def get(self):
    ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
    minElev = self.request.get('minElev')
    #to do: error handling
    minElev = float(minElev)
    template_values = self.getLayer(minElev)
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(template_values))

app = webapp2.WSGIApplication([('/', MainPage), ('/slider',SliderHandler)], debug=True)
