# Description
These python scripts were inspired by the webpage
https://www.sebulli.com/ntc/index.php.   
I am not affiliated with the webpage.

The scipts generate C-code to convert an ADC measurement of an NTC voltage divider to
temperature using a lookup table. This can be included in an MCU project for
example.

The website was limited to 8, 10, 12 bit ADC resolution.  These scripts allow
arbitrary values for the ADC resolution and the table length.

There are two scripts. One generates a lookup table using either the
manufacturer-specified Beta value or a set of Steinhart-Hart coefficients. If
you have access to Steinhart-Hart coefficients, they are likely to provide a
more accurate result over a wider range of temperatures. Otherwise, Beta is
used for less demanding applications over a smaller temperature range.

The other script generates a table using an arbitrary list of
manufacturer-provided resistance vs. temperature values. This is likely to be
more accurate than using Beta.

The second script also has two modes of operation. By default it will perform a
piecewise-cubic interpolation of the data provided. This means that the
resulting curve will exactly pass through each data point provided. Between the
points, the cubic polynomial will produce relatively little error. However, once
the temperature gets outside the range of manufacturer-provided values, the
accuracy quickly degrades due to the cubic extrapolation.

The alternate mode, using the option --steinhart, will curve fit the provided data
to a 3 or 4 parameter Steinhart-Hart model and then use that to generate the
table. The resulting curve will likely NOT pass through each provided data
point exactly, but it MAY be more accurate overall. An option is provided to
exclude some data points to reduce the effect of self-heating skewing the
curve.

In all cases the values at the two ends of the table are not going to be
accurate, but this can usually be ignored as they are outside the expected
range of ADC values, corresponding to unrealistic temperatures.

# Usage
```
$ python3 adc_to_ntc_temperature.py -h
usage: adc_to_ntc_temperature.py [-h] --adc_bits ADC_BITS --table_bits
                                 TABLE_BITS --resolution DEGREES [-R OHMS]
                                 [-T DEGREES] -r OHMS [-o OUTPUT] [--plot]
                                 (-B BETA | -S a0 a1 a2 a3) (-t | -b)

options:
  -h, --help            show this help message and exit
  --adc_bits ADC_BITS   Number of bits of ADC resolution.
  --table_bits TABLE_BITS
                        Number of bits. Table len = 2^TABLE_BITS + 1.
  --resolution DEGREES  Temperature resolution (C). Typically 0.01.
  -R OHMS               Thermistor reference resistance (ohms).
  -T DEGREES            Thermistor reference temperature (C).
  -r OHMS               Other resistor value (ohms).
  -o OUTPUT, --output OUTPUT
                        Output file to write.
  --plot                Create plot.
  -B BETA, --beta BETA  Thermistor beta value.
  -S a0 a1 a2 a3, --steinhart a0 a1 a2 a3
                        4 Steinhart-Hart coefficients a0, a1, a2, a3. If using
                        only 3 coefficients (A, B, C) set a0=A, a1=B, a2=0,
                        a3=C.
  -t, --top             Thermistor on top-side of voltage divider.
  -b, --bottom          Thermistor on bottom-side of voltage divider.

Generate a lookup table to convert ratiometric ADC values directly to
temperature. For use with NTC thermistor voltage divider, where ADC VREF is
applied across the voltage divider. The NTC thermistor may be located on
either the top side or bottom side of the divider. The table is constructed in
one of two ways: 1) Using a beta value, reference temperature, and reference
resistance. 2) Using 3 or 4 Steinhart-Hart coefficients. Using the Beta value,
the resulting table is accurate over some range of temperatures, but becomes
less accurate as the range increases. Using Steinhart-Hart coefficients, the
table may be more accurate over a larger temperature range. The resulting code
is fast, using one integer multiply and some additions and bit shifts. Adapted
from https://www.sebulli.com/ntc/index.php
```
## Example 1

Here's an example using the Beta value. Reference temperature and reference
resistances must also be specified:
```
python3 adc_to_ntc_temperature.py --adc_bits 16 --table_bits 9 -B 3435 -R 10000 -T 25 -r 10000 -b --resolution 0.01
```

The following output is generated:

```
#include <stdint.h>

/* ADC to temperature lookup table.
 * github.com/bkuschak/adc_to_ntc_temperature
 * Adapted from https://www.sebulli.com/ntc/index.php
 *
 * Command:
 * adc_to_ntc_temperature.py --adc_bits 16 --table_bits 9 -B 3435 -R 10000 -T 25 -r 10000 -b --resolution 0.01
 *
 * 10000 ohms @ 25 deg C. Beta: 3435.
 * NTC thermistor location: bottom side of the voltage divider.
 * 10000 ohm resistor on opposite side of the voltage divider.
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
 * p1 and p2 are the interpolating points just before and after the ADC value.
 * The function interpolates between these two points. The resulting code is
 * very small and fast. Only one integer multiplication is used.
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

## Example 2

This example uses the tabular data script and a list of resistance vs.
temperature points provided by the manufacturer.

```
$ python3 adc_to_ntc_temperature_using_tabular_data.py -h
usage: adc_to_ntc_temperature_using_tabular_data.py [-h] --adc_bits ADC_BITS
                                                    --table_bits TABLE_BITS
                                                    --resolution DEGREES -f
                                                    FILE -r OHMS [-o OUTPUT]
                                                    [--plot] [--steinhart SH]
                                                    [--steinhart_exclude NUM]
                                                    (-t | -b)

options:
  -h, --help            show this help message and exit
  --adc_bits ADC_BITS   Number of bits of ADC resolution.
  --table_bits TABLE_BITS
                        Number of bits. Table len = 2^TABLE_BITS + 1.
  --resolution DEGREES  Temperature resolution (C). Typically 0.01.
  -f FILE               Input file providing temperature and resistancein
                        tabular format.
  -r OHMS               Other resistor value (ohms).
  -o OUTPUT, --output OUTPUT
                        Output file to write.
  --plot                Create plot.
  --steinhart SH        Calculate the Steinhart-Hart coefficients using 3 or 4
                        parameters.
  --steinhart_exclude NUM
                        When fitting data to the Steinhart-Hart model, exclude
                        the NUM highest temperature data points to try to
                        reduce error due to self-heating.
  -t, --top             Thermistor on top-side of voltage divider.
  -b, --bottom          Thermistor on bottom-side of voltage divider.

Generate a lookup table to convert ratiometric ADC values directly to
temperature. For use with NTC thermistor voltage divider, where ADC VREF is
applied across the voltage divider. The NTC thermistor may be located on
either the top side or bottom side of the divider. The lookup table is
constructed from list of manufacturer-specified temperature and resistance
values. These are provided in a space-delimited text file, with each line
consisting of one temperature and one resistance. Temperature is in deg C and
resistance in ohms. See the data in the example tabular_data_example.txt. By
default, the data is fit to a piecewise-cubic curve, which passes through each
data point exactly. Since the extreme ends of the table correspond to ADC
values that represent extreme (unrealistic) temperatures, the ends of the
table are likely to contain wildly inaccurate values extrapolated from well
beyond the range of manufacturer data provided. This can usually be safely
ignored, as the ADC is not expected to generate these values. Alternatively,
using the option --steinhart, a 3 or 4 parameter Steinhart-Hart model is used
instead for the curve fit. Since NTC resistance is low at high temperatures,
the effect of self-heating causes error. The --steinhart_exclude option can be
used to exclude the N highest temperature points when doing the curve fit to
avoid them skewing the curve. The resulting C code is fast, using one integer
multiply and some additions and bit shifts. Adapted from
https://www.sebulli.com/ntc/index.php
```

By default a piecewise-cubic interpolation is used, which passes directly
through each data point provided. However, at the two ends of the table it is
extrapolated well beyond the provided manufacturer data resulting in
unrealistic temperature values. These can usually be safely ignored as they
correspond to ADC voltages that are never expected in practice. For an
alternative see the Steinhart-Hart method in example 3.

```
python3 adc_to_ntc_temperature_using_tabular_data.py --adc_bits=16 --table_bits=9 --resolution=0.01 -r 10e3 -b -f tabular_data_example.txt
```

The following output is generated:

```
Piecewise cubic interpolation:
  Temperature at 10000.0 ohms: 25.000000 deg C
```

```
#include <stdint.h>

/* ADC to temperature lookup table.
 * github.com/bkuschak/adc_to_ntc_temperature
 * Adapted from https://www.sebulli.com/ntc/index.php
 *
 * Command:
 * adc_to_ntc_temperature_using_tabular_data.py --adc_bits=16 --table_bits=9 --resolution=0.01 -r 10e3 -b -f tabular_data_example.txt
 *
 * Table derived from manfacturer-provided temperature/resistance data which is
 * interpolated to fit a piecewise-cubic curve.
 *
 * NTC thermistor location: bottom side of the voltage divider.
 * 10000 ohm resistor on opposite side of the voltage divider.
 * Input: 9 MSBs of the ADC value.
 * Output: Temperature in units of 0.01 deg C.
 * LSBs of ADC value should be used to interpolate between the nearest points.
 */
const int32_t ntc_table[513] = {
    19861, 19421, 18981, 18556, 18146, 17749, 17367, 16999, 16643, 16301, 
    15972, 15656, 15352, 15060, 14780, 14511, 14254, 14007, 13771, 13545, 
    13329, 13122, 12925, 12736, 12555, 12382, 12217, 12058, 11906, 11760, 
    11620, 11485, 11355, 11229, 11107, 10989, 10874, 10763, 10655, 10550, 
    10447, 10347, 10250, 10155, 10062, 9972, 9883, 9797, 9712, 9629, 9548, 
    9469, 9391, 9315, 9240, 9166, 9094, 9023, 8953, 8884, 8816, 8749, 8683, 
    8619, 8555, 8492, 8430, 8369, 8308, 8249, 8190, 8132, 8075, 8019, 7963, 
    7908, 7853, 7799, 7746, 7693, 7641, 7590, 7539, 7489, 7440, 7391, 7343, 
    7295, 7248, 7201, 7155, 7109, 7064, 7020, 6976, 6932, 6889, 6846, 6804, 
    6762, 6720, 6679, 6639, 6598, 6558, 6519, 6480, 6441, 6402, 6364, 6326, 
    6288, 6251, 6214, 6178, 6141, 6105, 6069, 6034, 5998, 5963, 5929, 5894, 
    5860, 5826, 5792, 5758, 5725, 5692, 5659, 5626, 5594, 5562, 5530, 5498, 
    5466, 5435, 5404, 5373, 5342, 5311, 5281, 5251, 5221, 5191, 5161, 5132, 
    5102, 5073, 5044, 5015, 4986, 4958, 4929, 4901, 4873, 4845, 4817, 4789, 
    4762, 4734, 4707, 4680, 4653, 4626, 4599, 4572, 4546, 4519, 4493, 4467, 
    4440, 4414, 4388, 4363, 4337, 4311, 4286, 4261, 4235, 4210, 4185, 4160, 
    4135, 4110, 4086, 4061, 4037, 4012, 3988, 3964, 3939, 3915, 3891, 3867, 
    3843, 3820, 3796, 3772, 3749, 3725, 3702, 3679, 3655, 3632, 3609, 3586, 
    3563, 3540, 3517, 3494, 3472, 3449, 3426, 3404, 3381, 3359, 3336, 3314, 
    3292, 3270, 3248, 3225, 3203, 3181, 3159, 3138, 3116, 3094, 3072, 3050, 
    3029, 3007, 2986, 2964, 2943, 2921, 2900, 2878, 2857, 2836, 2814, 2793, 
    2772, 2751, 2730, 2709, 2687, 2666, 2645, 2625, 2604, 2583, 2562, 2541, 
    2520, 2500, 2479, 2458, 2437, 2417, 2396, 2376, 2355, 2334, 2314, 2293, 
    2273, 2252, 2232, 2212, 2191, 2171, 2150, 2130, 2110, 2089, 2069, 2049, 
    2029, 2008, 1988, 1968, 1947, 1927, 1907, 1886, 1866, 1846, 1825, 1805, 
    1785, 1765, 1744, 1724, 1704, 1683, 1663, 1643, 1622, 1602, 1582, 1561, 
    1541, 1521, 1500, 1480, 1460, 1439, 1419, 1399, 1378, 1358, 1338, 1317, 
    1297, 1277, 1256, 1236, 1215, 1195, 1175, 1154, 1134, 1113, 1093, 1072, 
    1052, 1031, 1011, 990, 969, 949, 928, 907, 886, 866, 845, 824, 803, 782, 
    761, 740, 719, 698, 677, 656, 635, 613, 592, 571, 550, 528, 507, 485, 464, 
    442, 421, 399, 377, 355, 334, 312, 290, 268, 246, 224, 201, 179, 157, 134, 
    112, 90, 67, 44, 22, 0, -23, -46, -69, -92, -115, -139, -162, -185, -209, 
    -233, -256, -280, -304, -328, -352, -376, -401, -425, -450, -474, -499, 
    -524, -549, -574, -599, -625, -650, -676, -702, -727, -753, -780, -806, 
    -832, -859, -886, -913, -940, -967, -994, -1022, -1050, -1077, -1106, 
    -1134, -1162, -1191, -1220, -1249, -1278, -1308, -1338, -1368, -1398, 
    -1428, -1459, -1490, -1521, -1552, -1584, -1616, -1648, -1681, -1714, 
    -1747, -1781, -1815, -1849, -1883, -1918, -1953, -1989, -2025, -2061, 
    -2098, -2136, -2173, -2212, -2250, -2289, -2329, -2369, -2410, -2451, 
    -2493, -2536, -2579, -2623, -2667, -2713, -2759, -2805, -2853, -2901, 
    -2951, -3001, -3052, -3105, -3158, -3213, -3269, -3326, -3384, -3443, 
    -3504, -3566, -3629, -3695, -3762, -3832, -3906, -3983, -4065, -4155, 
    -4255, -4369, -4504, -4668, -4875, -5148, -5518, -6041, -6803, -7950, 
    -9732, -12599, -17393, -25780, -41291, -72103, -139505, -308738, -834883, 
    -3223813, -29509714, -55795615
};

/*
 * Convert an ADC value into a temperature value.
 * The ADC value must be a ratiometric measurement of the NTC voltage divider.
 *
 * p1 and p2 are the interpolating points just before and after the ADC value.
 * The function interpolates between these two points. The resulting code is
 * very small and fast. Only one integer multiplication is used.
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

## Example 3

This example uses the manufacturer-provided data to fit a Steinhart-Hart model,
which is then interpolated to create the table. This uses the data points to
fit a single curve, unlike the piecewise-cubic method. Therefore, the resulting
curve is unlikely to pass through each data point exactly. However, it might
result in a more accurate result overall. Since NTC self-heating is most
relevant at high temperatures (low resistance) an option
```--steinhart_exclude``` is provided to exclude some of the the highest
temperature data points when fitting the curve. These points might otherwise
skew the curve, leading to to lower accuracy.

```
python3 adc_to_ntc_temperature_using_tabular_data.py --adc_bits=16 --table_bits=9 --resolution=0.01 -r 10e3 -b -f tabular_data_example.txt --steinhart=3 --steinhart_exclude=8
```

For this method, the computed coefficients are printed, along with the
calculated temperature at 10 Kohm resistance. (For this example, we expect 25.0
C at 10 Kohms).

```
Steinhart-Hart coefficients:
  A = 8.118491e-04
  B = 2.649361e-04
  C = 1.301107e-07
  Standard deviation of the curve fit: 6.061497640297236e-12
  Temperature at 10000.0 ohms: 25.031857 deg C
```

The resulting code:

```
#include <stdint.h>

/* ADC to temperature lookup table.
 * github.com/bkuschak/adc_to_ntc_temperature
 * Adapted from https://www.sebulli.com/ntc/index.php
 *
 * Command:
 * adc_to_ntc_temperature_using_tabular_data.py --adc_bits=16 --table_bits=9 --resolution=0.01 -r 10e3 -b -f tabular_data_example.txt --steinhart=3 --steinhart_exclude=8
 *
 * Table derived from manfacturer-provided temperature/resistance data which is
 * interpolated to fit a 3 parameter Steinhart-Hart curve.
 *   A: 8.118491e-04
 *   B: 2.649361e-04
 *   C: 1.301107e-07
 *
 * NTC thermistor location: bottom side of the voltage divider.
 * 10000 ohm resistor on opposite side of the voltage divider.
 * Input: 9 MSBs of the ADC value.
 * Output: Temperature in units of 0.01 deg C.
 * LSBs of ADC value should be used to interpolate between the nearest points.
 */
const int32_t ntc_table[513] = {
    41580, 35060, 28540, 25297, 23204, 21684, 20503, 19544, 18741, 18052, 
    17451, 16919, 16443, 16012, 15620, 15259, 14927, 14618, 14331, 14061, 
    13808, 13570, 13344, 13130, 12927, 12734, 12549, 12372, 12203, 12041, 
    11885, 11735, 11590, 11451, 11316, 11186, 11060, 10937, 10819, 10704, 
    10592, 10484, 10378, 10275, 10175, 10077, 9982, 9889, 9798, 9709, 9622, 
    9537, 9454, 9372, 9293, 9215, 9138, 9063, 8989, 8917, 8846, 8776, 8708, 
    8640, 8574, 8509, 8445, 8382, 8320, 8258, 8198, 8139, 8081, 8023, 7966, 
    7910, 7855, 7801, 7747, 7694, 7642, 7590, 7539, 7489, 7439, 7390, 7341, 
    7293, 7246, 7199, 7153, 7107, 7062, 7017, 6972, 6928, 6885, 6842, 6799, 
    6757, 6715, 6674, 6633, 6593, 6552, 6513, 6473, 6434, 6395, 6357, 6319, 
    6281, 6244, 6207, 6170, 6133, 6097, 6061, 6026, 5990, 5955, 5920, 5886, 
    5851, 5817, 5784, 5750, 5717, 5684, 5651, 5618, 5586, 5554, 5522, 5490, 
    5458, 5427, 5396, 5365, 5334, 5303, 5273, 5243, 5213, 5183, 5153, 5124, 
    5094, 5065, 5036, 5007, 4979, 4950, 4922, 4894, 4866, 4838, 4810, 4782, 
    4755, 4727, 4700, 4673, 4646, 4619, 4592, 4566, 4539, 4513, 4487, 4460, 
    4434, 4409, 4383, 4357, 4332, 4306, 4281, 4255, 4230, 4205, 4180, 4155, 
    4131, 4106, 4081, 4057, 4032, 4008, 3984, 3960, 3936, 3912, 3888, 3864, 
    3840, 3817, 3793, 3770, 3746, 3723, 3700, 3676, 3653, 3630, 3607, 3584, 
    3561, 3539, 3516, 3493, 3471, 3448, 3426, 3403, 3381, 3358, 3336, 3314, 
    3292, 3270, 3248, 3226, 3204, 3182, 3160, 3138, 3116, 3095, 3073, 3051, 
    3030, 3008, 2987, 2965, 2944, 2923, 2901, 2880, 2859, 2838, 2816, 2795, 
    2774, 2753, 2732, 2711, 2690, 2669, 2648, 2627, 2607, 2586, 2565, 2544, 
    2523, 2503, 2482, 2461, 2441, 2420, 2399, 2379, 2358, 2338, 2317, 2297, 
    2276, 2256, 2235, 2215, 2195, 2174, 2154, 2133, 2113, 2093, 2072, 2052, 
    2032, 2011, 1991, 1971, 1951, 1930, 1910, 1890, 1870, 1849, 1829, 1809, 
    1789, 1768, 1748, 1728, 1708, 1687, 1667, 1647, 1627, 1606, 1586, 1566, 
    1546, 1525, 1505, 1485, 1465, 1444, 1424, 1404, 1383, 1363, 1343, 1322, 
    1302, 1282, 1261, 1241, 1220, 1200, 1180, 1159, 1139, 1118, 1098, 1077, 
    1056, 1036, 1015, 994, 974, 953, 932, 912, 891, 870, 849, 828, 807, 786, 
    765, 744, 723, 702, 681, 660, 639, 618, 596, 575, 554, 532, 511, 489, 468, 
    446, 425, 403, 381, 359, 337, 316, 294, 272, 249, 227, 205, 183, 161, 138, 
    116, 93, 71, 48, 25, 2, -20, -42, -66, -89, -112, -135, -158, -182, -205, 
    -229, -253, -277, -301, -325, -349, -373, -397, -422, -446, -471, -496, 
    -520, -545, -571, -596, -621, -647, -672, -698, -724, -750, -776, -802, 
    -829, -855, -882, -909, -936, -963, -991, -1018, -1046, -1074, -1102, 
    -1130, -1159, -1188, -1216, -1246, -1275, -1304, -1334, -1364, -1394, 
    -1425, -1456, -1487, -1518, -1549, -1581, -1613, -1645, -1678, -1711, 
    -1744, -1778, -1812, -1846, -1881, -1915, -1951, -1987, -2023, -2059, 
    -2096, -2134, -2171, -2210, -2248, -2288, -2328, -2368, -2409, -2450, 
    -2492, -2535, -2578, -2622, -2667, -2712, -2759, -2806, -2853, -2902, 
    -2952, -3002, -3054, -3106, -3160, -3215, -3271, -3328, -3387, -3447, 
    -3508, -3571, -3636, -3703, -3772, -3843, -3916, -3992, -4070, -4151, 
    -4235, -4323, -4414, -4510, -4610, -4715, -4826, -4943, -5067, -5201, 
    -5344, -5498, -5667, -5853, -6060, -6295, -6567, -6892, -7299, -7851, 
    -8740, -9629
};

/*
 * Convert an ADC value into a temperature value.
 * The ADC value must be a ratiometric measurement of the NTC voltage divider.
 *
 * p1 and p2 are the interpolating points just before and after the ADC value.
 * The function interpolates between these two points. The resulting code is
 * very small and fast. Only one integer multiplication is used.
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

## Plots

This is a plot of the resulting table using the beta script:

![figure](/img/figure_1_beta.png)

This is a plot of the resulting table using the tablular data script:

![figure](/img/figure_1_tabular_data.png)

Here is an example of temperature data collected using the generated code.

![screenshot](/img/screenshot.png)
