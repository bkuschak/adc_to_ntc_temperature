# Description
This python script was adapted from the webpage https://www.sebulli.com/ntc/index.php  

It generates C-code to convert an ADC measurement of an NTC voltage divider to temperature using a lookup table. This can be included in an MCU project for example.

The website was limited to 12 bit maximum ADC resolution.  This script allows arbitrary values for the ADC resolution and the table length. 

It does not yet calculate the temperature error attributed to the lookup table interpolation.

# Usage
```
$ python3 adc_to_ntc_temperature.py -h
usage: adc_to_ntc_temperature.py [-h] --adc_bits ADC_BITS --table_bits TABLE_BITS --resolution DEGREES -B BETA -R OHMS -T DEGREES -r OHMS [-o OUTPUT]
                                 (-t | -b)

options:
  -h, --help            show this help message and exit
  --adc_bits ADC_BITS   Number of bits of ADC resolution.
  --table_bits TABLE_BITS
                        Number of bits. Table len = 2^N + 1.
  --resolution DEGREES  Temperature resolution (C). Typically 0.01.
  -B BETA, --beta BETA  Thermistor beta value.
  -R OHMS               Thermistor reference resistance (ohms).
  -T DEGREES            Thermistor reference temperature (C).
  -r OHMS               Other resistor value (ohms).
  -o OUTPUT, --output OUTPUT
                        Output file to write.
  -t, --top             Thermistor on top-side of voltage divider.
  -b, --bottom          Thermistor on bottom-side of voltage divider.
```

Here's an example:
```
python3 adc_to_ntc_temperature.py --adc_bits 16 --table_bits 9 --resolution 0.01 -B 3435 -R 10000 -T 25 -r 10000 -b
```

The following output is generated:

```
#include <stdint.h>

/* ADC to temperature lookup table.
 * 10000 ohms @ 25 deg C. Beta: 3435.
 * NTC thermistor location: bottom side of the voltage divider.
 * Input: 9 MSBs of the ADC value.
 * Output: Temperature in units of 0.01 deg C.
 * LSBs of ADC value should be used to interpolate between the nearest points.
 */
const int32_t ntc_table[513] = {
    770211, 37684, 30128, 26464, 24131, 22453, 21159, 20114, 19242, 18499, 
    17852, 17281, 16772, 16312, 15895, 15512, 15160, 14833, 14529, 14245, 
    13979, 13728, 13491, 13267, 13055, 12852, 12659, 12475, 12299, 12130, 
    11967, 11811, 11661, 11516, 11377, 11242, 11111, 10985, 10862, 10743, 
    10628, 10516, 10407, 10301, 10198, 10097, 9999, 9904, 9810, 9719, 9630, 
    9543, 9458, 9374, 9293, 9213, 9134, 9058, 8982, 8908, 8836, 8765, 8695, 
    8626, 8559, 8492, 8427, 8363, 8300, 8238, 8177, 8116, 8057, 7999, 7941, 
    7884, 7828, 7773, 7719, 7665, 7612, 7560, 7508, 7457, 7407, 7357, 7308, 
    7260, 7212, 7164, 7118, 7071, 7026, 6980, 6936, 6891, 6848, 6804, 6761, 
    6719, 6677, 6635, 6594, 6553, 6513, 6473, 6433, 6394, 6355, 6317, 6278, 
    6241, 6203, 6166, 6129, 6092, 6056, 6020, 5984, 5949, 5914, 5879, 5844, 
    5810, 5776, 5742, 5709, 5675, 5642, 5609, 5577, 5544, 5512, 5480, 5449, 
    5417, 5386, 5355, 5324, 5293, 5263, 5233, 5203, 5173, 5143, 5113, 5084, 
    5055, 5026, 4997, 4968, 4940, 4911, 4883, 4855, 4827, 4799, 4772, 4744, 
    4717, 4690, 4663, 4636, 4609, 4582, 4556, 4530, 4503, 4477, 4451, 4425, 
    4400, 4374, 4348, 4323, 4298, 4272, 4247, 4222, 4197, 4173, 4148, 4123, 
    4099, 4075, 4050, 4026, 4002, 3978, 3954, 3930, 3906, 3883, 3859, 3836, 
    3812, 3789, 3766, 3743, 3720, 3696, 3674, 3651, 3628, 3605, 3583, 3560, 
    3537, 3515, 3493, 3470, 3448, 3426, 3404, 3382, 3360, 3338, 3316, 3294, 
    3272, 3251, 3229, 3207, 3186, 3164, 3143, 3122, 3100, 3079, 3058, 3036, 
    3015, 2994, 2973, 2952, 2931, 2910, 2889, 2869, 2848, 2827, 2806, 2786, 
    2765, 2744, 2724, 2703, 2683, 2662, 2642, 2621, 2601, 2581, 2560, 2540, 
    2520, 2500, 2479, 2459, 2439, 2419, 2399, 2379, 2359, 2339, 2319, 2299, 
    2279, 2259, 2239, 2219, 2199, 2179, 2159, 2139, 2120, 2100, 2080, 2060, 
    2040, 2021, 2001, 1981, 1961, 1942, 1922, 1902, 1883, 1863, 1843, 1824, 
    1804, 1784, 1765, 1745, 1725, 1706, 1686, 1667, 1647, 1627, 1608, 1588, 
    1568, 1549, 1529, 1509, 1490, 1470, 1450, 1431, 1411, 1391, 1372, 1352, 
    1332, 1313, 1293, 1273, 1253, 1234, 1214, 1194, 1174, 1154, 1135, 1115, 
    1095, 1075, 1055, 1035, 1015, 995, 975, 955, 935, 915, 895, 875, 855, 834, 
    814, 794, 774, 753, 733, 713, 692, 672, 651, 631, 610, 590, 569, 548, 528, 
    507, 486, 465, 444, 424, 403, 382, 360, 339, 318, 297, 276, 254, 233, 211, 
    190, 168, 147, 125, 103, 81, 59, 37, 15, -6, -28, -50, -73, -95, -118, 
    -140, -163, -186, -208, -231, -254, -278, -301, -324, -347, -371, -395, 
    -418, -442, -466, -490, -514, -538, -563, -587, -612, -637, -662, -687, 
    -712, -737, -763, -788, -814, -840, -866, -892, -918, -945, -971, -998, 
    -1025, -1053, -1080, -1108, -1135, -1163, -1192, -1220, -1249, -1277, 
    -1306, -1336, -1365, -1395, -1425, -1455, -1486, -1517, -1548, -1579, 
    -1611, -1643, -1675, -1708, -1741, -1774, -1808, -1842, -1876, -1911, 
    -1946, -1982, -2018, -2054, -2091, -2128, -2166, -2204, -2243, -2283, 
    -2323, -2363, -2405, -2447, -2489, -2532, -2576, -2621, -2666, -2713, 
    -2760, -2808, -2857, -2907, -2958, -3010, -3063, -3118, -3174, -3231, 
    -3290, -3350, -3412, -3476, -3541, -3609, -3679, -3751, -3826, -3904, 
    -3985, -4069, -4157, -4249, -4346, -4447, -4555, -4669, -4791, -4922, 
    -5063, -5217, -5385, -5574, -5786, -6032, -6325, -6690, -7182, -7970, 
    -12123
};

/*
 * Convert an ADC value into a temperature value.
 * The ADC value must be a ratiometric measurement of the NTC voltage divider.
 *
 * p1 and p2 are the interpolating points just before and after the
 * ADC value. The function interpolates between these two points
 * The resulting code is very small and fast.
 * Only one integer multiplication is used.
 *
 * adc_value: the ADC measurement, 16 bits full scale, right justified.
 * Returns the temperature in units of 0.01 °C
 *
 */
int32_t adc_to_temperature(uint16_t adc_value) 
{
  adc_value &= 0xFFFF;

  /* Estimate the interpolating point before and after the ADC value. */
  int32_t p1 = ntc_table[ (adc_value >> 7)  ];
  int32_t p2 = ntc_table[ (adc_value >> 7)+1];

  /* Interpolate between both points. */
  return p1 - (((p1-p2) * (adc_value & 0x7F))>>7);
}
```
