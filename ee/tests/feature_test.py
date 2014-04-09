"""Test for the ee.feature module."""



import unittest

import ee
from ee import apitestcase


class FeatureTest(apitestcase.ApiTestCase):

  def testConstructors(self):
    """Verifies that constructors understand valid parameters."""
    point = ee.Geometry.Point(1, 2)
    from_geometry = ee.Feature(point)
    self.assertEquals(ee.ApiFunction('Feature'), from_geometry.func)
    self.assertEquals({'geometry': point, 'metadata': None}, from_geometry.args)

    from_null_geometry = ee.Feature(None, {'x': 2})
    self.assertEquals(ee.ApiFunction('Feature'), from_null_geometry.func)
    self.assertEquals({'geometry': None, 'metadata': {'x': 2}},
                      from_null_geometry.args)

    computed_geometry = ee.Geometry(ee.ComputedObject(ee.Function(), {'a': 1}))
    computed_properties = ee.ComputedObject(ee.Function(), {'b': 2})
    from_computed_one = ee.Feature(computed_geometry)
    from_computed_both = ee.Feature(computed_geometry, computed_properties)
    self.assertEquals(ee.ApiFunction('Feature'), from_computed_one.func)
    self.assertEquals({'geometry': computed_geometry,
                       'metadata': None},
                      from_computed_one.args)
    self.assertEquals(ee.ApiFunction('Feature'), from_computed_both.func)
    self.assertEquals({'geometry': computed_geometry,
                       'metadata': computed_properties},
                      from_computed_both.args)

    from_variable = ee.Feature(ee.CustomFunction.variable(None, 'foo'))
    self.assertTrue(isinstance(from_variable, ee.Feature))
    self.assertEquals({'type': 'ArgumentRef', 'value': 'foo'},
                      from_variable.encode(None))

    from_geo_json_feature = ee.Feature({
        'type': 'Feature',
        'geometry': point.toGeoJSON(),
        'properties': {'foo': 42}
    })
    self.assertEquals(ee.ApiFunction('Feature'), from_geo_json_feature.func)
    self.assertEquals(point, from_geo_json_feature.args['geometry'])
    self.assertEquals({'foo': 42}, from_geo_json_feature.args['metadata'])

  def testGetMap(self):
    """Verifies that getMap() uses Collection.draw to rasterize Features."""
    feature = ee.Feature(None)
    mapid = feature.getMapId({'color': 'ABCDEF'})
    manual = ee.ApiFunction.apply_('Collection.draw', {
        'collection': ee.FeatureCollection([feature]),
        'color': 'ABCDEF'})

    self.assertEquals('fakeMapId', mapid['mapid'])
    self.assertEquals(manual.serialize(), mapid['image'].serialize())


if __name__ == '__main__':
  unittest.main()
