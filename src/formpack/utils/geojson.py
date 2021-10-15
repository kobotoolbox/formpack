# coding: utf-8
from geojson_rewind import rewind

from .exceptions import FormPackGeoJsonError


def field_and_response_to_geometry(field, response):
    """
    Return a GeoJSON `geometry` object given a field object (`FormField`) and
    an unformatted response (str). Maps XForm data types to GeoJSON geomtry
    types as follows:

        * `geopoint` to `Point`;
        * `geotrace` to `LineString`;
        * `geoshape` to `Polygon`.

    Gotcha: XForm lists the latitude first, but GeoJSON places the longitude in
    the first position! Both agree that the third position, if included,
    specifies the altitude in meters.

    The XForm types are described by  https://opendatakit.github.io/xforms-spec/:

    `geopoint` | Space-separated list of valid latitude (decimal degrees),
                 longitude (decimal degrees), altitude (decimal meters) and
                 accuracy (decimal meters)
    `geotrace` | Semi-colon-separated list of at least 2 geopoints, where the
                 last geopoint's latitude and longitude is not equal to the
                 first
    `geoshape` | Semi-colon-separated list of at least 3 geopoints, where the
                 last geopoint's latitude and longitude is equal to the first
    """

    def split_geopoint_str(geopoint_str):
        """
        From https://tools.ietf.org/html/rfc7946#section-4: "An
        OPTIONAL third-position element SHALL be the height in meters
        above or below the WGS 84 reference ellipsoid."

        From https://tools.ietf.org/html/rfc7946#section-9: "GeoJSON
        has no concept of uncertainty; imprecise or uncertain 'geo'
        URIs thus cannot be mapped to GeoJSON geometries."
        """

        point_components = geopoint_str.split(' ')
        if not 2 <= len(point_components) <= 4:
            raise FormPackGeoJsonError('Cannot parse coordinates')
        try:
            coordinates = list(map(float, point_components))
        except ValueError:
            raise FormPackGeoJsonError('Non-numeric data for a coordinate')

        # Swap the coordinates because that's what GeoJSON wants 🙄
        latitude, longitude, altitude, accuracy = coordinates
        return longitude, latitude, altitude

    geometry = {}

    if field.data_type == 'geopoint':
        geometry['type'] = 'Point'
        geometry['coordinates'] = split_geopoint_str(response)
    elif field.data_type == 'geotrace':
        geometry['type'] = 'LineString'
        geometry['coordinates'] = [
            split_geopoint_str(point)
            for point in response.split(';')
        ]
        if len(geometry['coordinates']) < 2:
            raise FormPackGeoJsonError('Too few points for a line')
    elif field.data_type == 'geoshape':
        geometry['type'] = 'Polygon'
        geometry['coordinates'] = [
            [split_geopoint_str(point) for point in response.split(';')],
            # We don't specify any holes in the `Polygon`, but if we did,
            # they'd go in another list here
        ]
        if len(geometry['coordinates'][0]) < 4:
            raise FormPackGeoJsonError('Too few points for a shape')
        # The first point must be equal to the last
        if geometry['coordinates'][0][0] != geometry['coordinates'][0][-1]:
            raise FormPackGeoJsonError('Shape is not closed')
        # GeoJSON requires the points to follow the right-hand rule; XForm does
        # not
        geometry = rewind(geometry)
    else:
        raise RuntimeError(
            '{field_name} is a {data_type}, which is not geographic'.format(
                field_name=field.name, data_type=field.data_type)
        )

    return geometry
