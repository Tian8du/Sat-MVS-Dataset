# Minor modifications added by Myron Brown, 2018
# - Code adapted from https://github.com/Turbo87/utm
# - Added numpy array versions of conversions
# - Consolidated code into one file and renamed functions
# - Added usage examples below


# MIT License
# Copyright (c) 2012-2017 Tobias Bieniek <Tobias.Bieniek@gmx.de>
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# Example with numpy arrays:
# lats = [64.83778, 64.83778,64.83778]
# lons = [-147.71639,-147.71639, -147.71639]
# from utm import *
# print(wgs84_to_utm_array(lats,lons))
# eastings, northings, zone_number, zone_letter = wgs84_to_utm_array(lats,lons)
# lats, lons = utm_to_wgs84_array(eastings, northings, zone_number, zone_letter)

# Example with scalar values:
# lat = 64.83778
# lon = -147.71639
# from utm import *
# print(wgs84_to_utm(lat,lon))
# easting, northing, zone_number, zone_letter = wgs84_to_utm(lat,lon)
# lat, lon = utm_to_wgs84(easting, northing, zone_number, zone_letter)



import math
import numpy
from copy import deepcopy

# Define out of range exception
class OutOfRangeError(ValueError):
    pass

# Define functions allowable for import
__all__ = ['utm_to_wgs84_array', 'wgs84_to_utm_array', 'utm_to_wgs84', 'wgs84_to_utm']


# Define constants for conversions
K0 = 0.9996

E = 0.00669438
E2 = E * E
E3 = E2 * E
E_P2 = E / (1.0 - E)

SQRT_E = math.sqrt(1 - E)
_E = (1 - SQRT_E) / (1 + SQRT_E)
_E2 = _E * _E
_E3 = _E2 * _E
_E4 = _E3 * _E
_E5 = _E4 * _E

M1 = (1 - E / 4 - 3 * E2 / 64 - 5 * E3 / 256)
M2 = (3 * E / 8 + 3 * E2 / 32 + 45 * E3 / 1024)
M3 = (15 * E2 / 256 + 45 * E3 / 1024)
M4 = (35 * E3 / 3072)

P2 = (3. / 2 * _E - 27. / 32 * _E3 + 269. / 512 * _E5)
P3 = (21. / 16 * _E2 - 55. / 32 * _E4)
P4 = (151. / 96 * _E3 - 417. / 128 * _E5)
P5 = (1097. / 512 * _E4)

R = 6378137

ZONE_LETTERS = "CDEFGHJKLMNPQRSTUVWXX"

# Convert scalar UTM to WGS84
def utm_to_wgs84(easting, northing, zone_number, zone_letter=None, northern=None, strict=True):
    """This function convert an UTM coordinate into Latitude and Longitude

        Parameters
        ----------
        easting: int
            Easting value of UTM coordinate

        northing: int
            Northing value of UTM coordinate

        zone number: int
            Zone Number is represented with global map numbers of an UTM Zone
            Numbers Map. More information see utmzones [1]_

        zone_letter: str
            Zone Letter can be represented as string values. Where UTM Zone
            Designators can be accessed in [1]_

        northern: bool
            You can set True or False to set this parameter. Default is None


       .. _[1]: http://www.jaworski.ca/utmzones.htm

    """
    if not zone_letter and northern is None:
        raise ValueError('either zone_letter or northern needs to be set')

    elif zone_letter and northern is not None:
        raise ValueError('set either zone_letter or northern, but not both')

    if strict:
        if not 100000 <= easting < 1000000:
            print(easting)
            raise OutOfRangeError('easting out of range (must be between 100.000 m and 999.999 m)')
        if not 0 <= northing <= 10000000:
            print(northing)
            raise OutOfRangeError('northing out of range (must be between 0 m and 10.000.000 m)')
    if not 1 <= zone_number <= 60:
        raise OutOfRangeError('zone number out of range (must be between 1 and 60)')

    if zone_letter:
        zone_letter = zone_letter.upper()

        if not 'C' <= zone_letter <= 'X' or zone_letter in ['I', 'O']:
            raise OutOfRangeError('zone letter out of range (must be between C and X)')

        northern = (zone_letter >= 'N')

    x = easting - 500000
    y = northing

    if not northern:
        y -= 10000000

    m = y / K0
    mu = m / (R * M1)

    p_rad = (mu +
             P2 * math.sin(2 * mu) +
             P3 * math.sin(4 * mu) +
             P4 * math.sin(6 * mu) +
             P5 * math.sin(8 * mu))

    p_sin = math.sin(p_rad)
    p_sin2 = p_sin * p_sin

    p_cos = math.cos(p_rad)

    p_tan = p_sin / p_cos
    p_tan2 = p_tan * p_tan
    p_tan4 = p_tan2 * p_tan2

    ep_sin = 1 - E * p_sin2
    ep_sin_sqrt = math.sqrt(1 - E * p_sin2)

    n = R / ep_sin_sqrt
    r = (1 - E) / ep_sin

    c = _E * p_cos**2
    c2 = c * c

    d = x / (n * K0)
    d2 = d * d
    d3 = d2 * d
    d4 = d3 * d
    d5 = d4 * d
    d6 = d5 * d

    latitude = (p_rad - (p_tan / r) *
                (d2 / 2 -
                 d4 / 24 * (5 + 3 * p_tan2 + 10 * c - 4 * c2 - 9 * E_P2)) +
                 d6 / 720 * (61 + 90 * p_tan2 + 298 * c + 45 * p_tan4 - 252 * E_P2 - 3 * c2))

    longitude = (d -
                 d3 / 6 * (1 + 2 * p_tan2 + c) +
                 d5 / 120 * (5 - 2 * c + 28 * p_tan2 - 3 * c2 + 8 * E_P2 + 24 * p_tan4)) / p_cos

    return (math.degrees(latitude),
            math.degrees(longitude) + zone_number_to_central_longitude(zone_number))

# Convert scalar WGS84 to UTM
def wgs84_to_utm(latitude, longitude, force_zone_number=None):
    """This function convert Latitude and Longitude to UTM coordinate

        Parameters
        ----------
        latitude: float
            Latitude between 80 deg S and 84 deg N, e.g. (-80.0 to 84.0)

        longitude: float
            Longitude between 180 deg W and 180 deg E, e.g. (-180.0 to 180.0).

        force_zone number: int
            Zone Number is represented with global map numbers of an UTM Zone
            Numbers Map. You may force conversion including one UTM Zone Number.
            More information see utmzones [1]_

       .. _[1]: http://www.jaworski.ca/utmzones.htm
    """
    if not -80.0 <= latitude <= 84.0:
        raise OutOfRangeError('latitude out of range (must be between 80 deg S and 84 deg N)')
    if not -180.0 <= longitude <= 180.0:
        raise OutOfRangeError('longitude out of range (must be between 180 deg W and 180 deg E)')

    lat_rad = math.radians(latitude)
    lat_sin = math.sin(lat_rad)
    lat_cos = math.cos(lat_rad)

    lat_tan = lat_sin / lat_cos
    lat_tan2 = lat_tan * lat_tan
    lat_tan4 = lat_tan2 * lat_tan2

    if force_zone_number is None:
        zone_number = latlon_to_zone_number(latitude, longitude)
    else:
        zone_number = force_zone_number

    zone_letter = latitude_to_zone_letter(latitude)

    lon_rad = math.radians(longitude)
    central_lon = zone_number_to_central_longitude(zone_number)
    central_lon_rad = math.radians(central_lon)

    n = R / math.sqrt(1 - E * lat_sin**2)
    c = E_P2 * lat_cos**2

    a = lat_cos * (lon_rad - central_lon_rad)
    a2 = a * a
    a3 = a2 * a
    a4 = a3 * a
    a5 = a4 * a
    a6 = a5 * a

    m = R * (M1 * lat_rad -
             M2 * math.sin(2 * lat_rad) +
             M3 * math.sin(4 * lat_rad) -
             M4 * math.sin(6 * lat_rad))

    easting = K0 * n * (a +
                        a3 / 6 * (1 - lat_tan2 + c) +
                        a5 / 120 * (5 - 18 * lat_tan2 + lat_tan4 + 72 * c - 58 * E_P2)) + 500000

    northing = K0 * (m + n * lat_tan * (a2 / 2 +
                                        a4 / 24 * (5 - lat_tan2 + 9 * c + 4 * c**2) +
                                        a6 / 720 * (61 - 58 * lat_tan2 + lat_tan4 + 600 * c - 330 * E_P2)))

    if latitude < 0:
        northing += 10000000

    return easting, northing, zone_number, zone_letter

# Convert numpy array UTM to WGS84
def utm_to_wgs84_array(easting, northing, zone_number, zone_letter=None, northern=None, strict=True):
    """This function convert an UTM coordinate into Latitude and Longitude

        Parameters
        ----------
        easting: int numpy array
            Easting value of UTM coordinate

        northing: int numpy array
            Northing value of UTM coordinate

        zone number: int
            Zone Number is represented with global map numbers of an UTM Zone
            Numbers Map. More information see utmzones [1]_

        zone_letter: str
            Zone Letter can be represented as string values. Where UTM Zone
            Designators can be accessed in [1]_

        northern: bool
            You can set True or False to set this parameter. Default is None


       .. _[1]: http://www.jaworski.ca/utmzones.htm

    """
    if not zone_letter and northern is None:
        raise ValueError('either zone_letter or northern needs to be set')

    elif zone_letter and northern is not None:
        raise ValueError('set either zone_letter or northern, but not both')

    # if strict:
        # if not 100000 <= easting < 1000000:
            # raise OutOfRangeError('easting out of range (must be between 100.000 m and 999.999 m)')
        # if not 0 <= northing <= 10000000:
            # raise OutOfRangeError('northing out of range (must be between 0 m and 10.000.000 m)')

    if not 1 <= zone_number <= 60:
        raise OutOfRangeError('zone number out of range (must be between 1 and 60)')

    if zone_letter:
        zone_letter = zone_letter.upper()

        # if not 'C' <= zone_letter <= 'X' or zone_letter in ['I', 'O']:
            # raise OutOfRangeError('zone letter out of range (must be between C and X)')

        northern = (zone_letter >= 'N')

    x = deepcopy(easting) - 500000
    y = deepcopy(northing)

    if not northern:
        y -= 10000000

    m = y / K0
    mu = m / (R * M1)

    p_rad = (mu +
             P2 * numpy.sin(2 * mu) +
             P3 * numpy.sin(4 * mu) +
             P4 * numpy.sin(6 * mu) +
             P5 * numpy.sin(8 * mu))

    p_sin = numpy.sin(p_rad)
    p_sin2 = p_sin * p_sin

    p_cos = numpy.cos(p_rad)

    p_tan = p_sin / p_cos
    p_tan2 = p_tan * p_tan
    p_tan4 = p_tan2 * p_tan2

    ep_sin = 1 - E * p_sin2
    ep_sin_sqrt = numpy.sqrt(1 - E * p_sin2)

    n = R / ep_sin_sqrt
    r = (1 - E) / ep_sin

    c = _E * p_cos**2
    c2 = c * c

    d = x / (n * K0)
    d2 = d * d
    d3 = d2 * d
    d4 = d3 * d
    d5 = d4 * d
    d6 = d5 * d

    latitude = (p_rad - (p_tan / r) *
                (d2 / 2 -
                 d4 / 24 * (5 + 3 * p_tan2 + 10 * c - 4 * c2 - 9 * E_P2)) +
                 d6 / 720 * (61 + 90 * p_tan2 + 298 * c + 45 * p_tan4 - 252 * E_P2 - 3 * c2))

    longitude = (d -
                 d3 / 6 * (1 + 2 * p_tan2 + c) +
                 d5 / 120 * (5 - 2 * c + 28 * p_tan2 - 3 * c2 + 8 * E_P2 + 24 * p_tan4)) / p_cos

    return (numpy.degrees(latitude),
            numpy.degrees(longitude) + zone_number_to_central_longitude(zone_number))

# Convert numpy array WGS84 to UTM
def wgs84_to_utm_array(latitude, longitude, force_zone_number=None):
    """This function converts Latitude and Longitude to UTM coordinate

        Parameters
        ----------
        latitude: float numpy array
            Latitude between 80 deg S and 84 deg N, e.g. (-80.0 to 84.0)

        longitude: float numpy array
            Longitude between 180 deg W and 180 deg E, e.g. (-180.0 to 180.0).

        force_zone number: int
            Zone Number is represented with global map numbers of an UTM Zone
            Numbers Map. You may force conversion including one UTM Zone Number.
            More information see utmzones [1]_

       .. _[1]: http://www.jaworski.ca/utmzones.htm
    """
    # if not -80.0 <= latitude <= 84.0:
        # raise OutOfRangeError('latitude out of range (must be between 80 deg S and 84 deg N)')
    # if not -180.0 <= longitude <= 180.0:
        # raise OutOfRangeError('longitude out of range (must be between 180 deg W and 180 deg E)')

    # Get first latitude and longitude values for checking zone
    first_latitude = latitude[0]
    first_longitude = longitude[0]

    lat_rad = numpy.radians(latitude)
    lat_sin = numpy.sin(lat_rad)
    lat_cos = numpy.cos(lat_rad)

    lat_tan = lat_sin / lat_cos
    lat_tan2 = lat_tan * lat_tan
    lat_tan4 = lat_tan2 * lat_tan2

    if force_zone_number is None:
        zone_number = latlon_to_zone_number(first_latitude, first_longitude)
    else:
        zone_number = force_zone_number

    zone_letter = latitude_to_zone_letter(first_latitude)

    lon_rad = numpy.radians(longitude)
    central_lon = zone_number_to_central_longitude(zone_number)
    central_lon_rad = numpy.radians(central_lon)

    n = R / numpy.sqrt(1 - E * lat_sin**2)
    c = E_P2 * lat_cos**2

    a = lat_cos * (lon_rad - central_lon_rad)
    a2 = a * a
    a3 = a2 * a
    a4 = a3 * a
    a5 = a4 * a
    a6 = a5 * a

    m = R * (M1 * lat_rad -
             M2 * numpy.sin(2 * lat_rad) +
             M3 * numpy.sin(4 * lat_rad) -
             M4 * numpy.sin(6 * lat_rad))

    easting = K0 * n * (a +
                        a3 / 6 * (1 - lat_tan2 + c) +
                        a5 / 120 * (5 - 18 * lat_tan2 + lat_tan4 + 72 * c - 58 * E_P2)) + 500000

    northing = K0 * (m + n * lat_tan * (a2 / 2 +
                                        a4 / 24 * (5 - lat_tan2 + 9 * c + 4 * c**2) +
                                        a6 / 720 * (61 - 58 * lat_tan2 + lat_tan4 + 600 * c - 330 * E_P2)))

    if first_latitude < 0:
        northing += 10000000

    return easting, northing, zone_number, zone_letter


def latitude_to_zone_letter(latitude):
    if -80 <= latitude <= 84:
        return ZONE_LETTERS[int(latitude + 80) >> 3]
    else:
        return None

def latlon_to_zone_number(latitude, longitude):
    if 56 <= latitude < 64 and 3 <= longitude < 12:
        return 32

    if 72 <= latitude <= 84 and longitude >= 0:
        if longitude <= 9:
            return 31
        elif longitude <= 21:
            return 33
        elif longitude <= 33:
            return 35
        elif longitude <= 42:
            return 37

    return int((longitude + 180) / 6) + 1

def zone_number_to_central_longitude(zone_number):
    return (zone_number - 1) * 6 - 180 + 3

if __name__ == "__main__":
    # # # 假设已知 UTM 坐标和区号、区字母
    # easting = 431982.995119
    # northing = 3358519.999913
    # zone_number = 17  # 假设 UTM 区号为 33
    # zone_letter = 'R'  # 假设 UTM 区字母为 N
    #
    # # 使用 utm_to_wgs84 函数转换为经纬度
    # lat, lon = utm_to_wgs84(easting, northing, zone_number, zone_letter)
    #
    # print(f"Latitude: {lat}, Longitude: {lon}")
    # 提供的经纬度
    latitude = 30 + 16 / 60 + 42.66 / 3600  # 30°16'42.66"N
    longitude = -(81 + 36 / 60 + 44.28 / 3600)  # 81°36'44.28"W

    # 转换为 UTM 坐标
    easting, northing, zone_number, zone_letter = wgs84_to_utm(latitude, longitude)

    print(f"Easting: {easting}, Northing: {northing}, Zone Number: {zone_number}, Zone Letter: {zone_letter}")


