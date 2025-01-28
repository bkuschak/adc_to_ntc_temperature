# Description
These python scripts were adapted from the webpage
https://www.sebulli.com/ntc/index.php  

They generate C-code to convert an ADC measurement of an NTC voltage divider to
temperature using a lookup table. This can be included in an MCU project for
example.

The website was limited to 8, 10, 12 bit ADC resolution.  This script allows
arbitrary values for the ADC resolution and the table length. 

There are two scripts. One generates the lookup table using the
manufacturer-specified Beta value. The other generates a table using an
arbitrary list of manufacturer-specified resistance vs temperature points. The
second is likely to be more accurate and is recommended if you have access to
such data.

# Usage
```
$ python3 adc_to_ntc_temperature_using_beta.py -h        
usage: adc_to_ntc_temperature_using_beta.py [-h] --adc_bits ADC_BITS --table_bits TABLE_BITS --resolution DEGREES
                                            -B BETA -R OHMS -T DEGREES -r OHMS [-o OUTPUT] [--plot] (-t | -b)

options:
  -h, --help            show this help message and exit
  --adc_bits ADC_BITS   Number of bits of ADC resolution.
  --table_bits TABLE_BITS
                        Number of bits. Table len = 2^TABLE_BITS + 1.
  --resolution DEGREES  Temperature resolution (C). Typically 0.01.
  -B BETA, --beta BETA  Thermistor beta value.
  -R OHMS               Thermistor reference resistance (ohms).
  -T DEGREES            Thermistor reference temperature (C).
  -r OHMS               Other resistor value (ohms).
  -o OUTPUT, --output OUTPUT
                        Output file to write.
  --plot                Create plot.
  -t, --top             Thermistor on top-side of voltage divider.
  -b, --bottom          Thermistor on bottom-side of voltage divider.

Generate a lookup table to convert ratiometric ADC values directly to
temperature. For use with NTC thermistor voltage divider, where ADC VREF is
applied across the voltage divider. The NTC thermistor may be located on either
the top side or bottom side of the divider. The table is constructed using a
manufacturer-provided Beta value, which is accurate over some range of
temperatures, but becomes less accurate as the range increases. The resulting
code is fast, using one integer multiply and some additions and bit shifts.
Adapted from https://www.sebulli.com/ntc/index.php
```

Here's an example:
```
python3 adc_to_ntc_temperature_using_beta.py --adc_bits 16 --table_bits 9 -B 3345 -R 10000 -T 25 -r 10000 -b --resolution 0.01
```

The following output is generated:

```
#include <stdint.h>

/* ADC to temperature lookup table.
 * github.com/bkuschak/adc_to_ntc_temperature
 * Adapted from https://www.sebulli.com/ntc/index.php
 *
 * 10000 ohms @ 25 deg C. Beta: 3345.
 * NTC thermistor location: bottom side of the voltage divider.
 * 10000 ohm resistor on opposite side of the voltage divider.
 * Input: 9 MSBs of the ADC value.
 * Output: Temperature in units of 0.01 deg C.
 * LSBs of ADC value should be used to interpolate between the nearest points.
 */
const int32_t ntc_table[513] = {
    2568820, 39815, 31597, 27653, 25155, 23365, 21989, 20880, 19957, 19170, 
    18487, 17884, 17347, 16863, 16423, 16021, 15651, 15308, 14989, 14691, 
    14411, 14148, 13900, 13666, 13443, 13231, 13029, 12836, 12652, 12475, 
    12306, 12143, 11986, 11835, 11689, 11548, 11412, 11280, 11152, 11029, 
    10908, 10792, 10678, 10568, 10460, 10355, 10253, 10154, 10057, 9962, 9869, 
    9779, 9690, 9603, 9518, 9435, 9354, 9274, 9196, 9119, 9044, 8970, 8897, 
    8826, 8756, 8687, 8619, 8553, 8487, 8423, 8359, 8297, 8235, 8175, 8115, 
    8056, 7998, 7941, 7884, 7829, 7774, 7720, 7666, 7614, 7561, 7510, 7459, 
    7409, 7359, 7310, 7262, 7214, 7166, 7120, 7073, 7028, 6982, 6937, 6893, 
    6849, 6806, 6763, 6720, 6678, 6636, 6595, 6554, 6513, 6473, 6433, 6393, 
    6354, 6315, 6277, 6239, 6201, 6163, 6126, 6089, 6053, 6016, 5980, 5945, 
    5909, 5874, 5839, 5805, 5770, 5736, 5702, 5668, 5635, 5602, 5569, 5536, 
    5504, 5471, 5439, 5407, 5376, 5344, 5313, 5282, 5251, 5221, 5190, 5160, 
    5130, 5100, 5070, 5040, 5011, 4982, 4953, 4924, 4895, 4866, 4838, 4809, 
    4781, 4753, 4725, 4698, 4670, 4643, 4615, 4588, 4561, 4534, 4507, 4481, 
    4454, 4428, 4401, 4375, 4349, 4323, 4297, 4271, 4246, 4220, 4195, 4170, 
    4144, 4119, 4094, 4069, 4044, 4020, 3995, 3971, 3946, 3922, 3898, 3873, 
    3849, 3825, 3801, 3777, 3754, 3730, 3706, 3683, 3659, 3636, 3613, 3590, 
    3566, 3543, 3520, 3497, 3474, 3452, 3429, 3406, 3384, 3361, 3339, 3316, 
    3294, 3271, 3249, 3227, 3205, 3183, 3161, 3139, 3117, 3095, 3073, 3051, 
    3029, 3008, 2986, 2965, 2943, 2921, 2900, 2879, 2857, 2836, 2815, 2793, 
    2772, 2751, 2730, 2709, 2688, 2667, 2646, 2625, 2604, 2583, 2562, 2541, 
    2520, 2500, 2479, 2458, 2437, 2417, 2396, 2375, 2355, 2334, 2314, 2293, 
    2273, 2252, 2232, 2211, 2191, 2171, 2150, 2130, 2109, 2089, 2069, 2049, 
    2028, 2008, 1988, 1967, 1947, 1927, 1907, 1887, 1866, 1846, 1826, 1806, 
    1786, 1766, 1745, 1725, 1705, 1685, 1665, 1645, 1625, 1605, 1584, 1564, 
    1544, 1524, 1504, 1484, 1464, 1443, 1423, 1403, 1383, 1363, 1343, 1322, 
    1302, 1282, 1262, 1242, 1221, 1201, 1181, 1161, 1140, 1120, 1100, 1079, 
    1059, 1039, 1018, 998, 977, 957, 936, 916, 895, 875, 854, 834, 813, 792, 
    772, 751, 730, 709, 688, 668, 647, 626, 605, 584, 563, 542, 521, 499, 478, 
    457, 436, 414, 393, 372, 350, 329, 307, 285, 264, 242, 220, 198, 177, 155, 
    133, 111, 88, 66, 44, 22, 0, -22, -45, -67, -90, -113, -136, -159, -182, 
    -205, -228, -251, -275, -298, -322, -345, -369, -393, -417, -441, -465, 
    -489, -513, -538, -562, -587, -612, -637, -662, -687, -712, -737, -763, 
    -789, -815, -840, -867, -893, -919, -946, -973, -999, -1027, -1054, -1081, 
    -1109, -1137, -1164, -1193, -1221, -1250, -1278, -1307, -1336, -1366, 
    -1395, -1425, -1455, -1486, -1516, -1547, -1578, -1610, -1642, -1674, 
    -1706, -1738, -1771, -1805, -1838, -1872, -1906, -1941, -1976, -2012, 
    -2047, -2084, -2120, -2157, -2195, -2233, -2272, -2311, -2350, -2390, 
    -2431, -2472, -2514, -2557, -2600, -2644, -2689, -2734, -2781, -2828, 
    -2876, -2925, -2974, -3025, -3077, -3130, -3185, -3240, -3297, -3355, 
    -3415, -3476, -3539, -3604, -3670, -3739, -3810, -3884, -3960, -4039, 
    -4121, -4206, -4295, -4389, -4487, -4590, -4699, -4815, -4938, -5071, 
    -5214, -5369, -5540, -5731, -5946, -6195, -6491, -6860, -7357, -8152, 
    -12321
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

This is a plot of the resulting table using Beta script:

![figure](/img/figure_1_beta.png)

This is a plot of the resulting table using tablular data script:

![figure](/img/figure_1_tabular_data.png)

Here is an example of temperature data collected using the generated code.

![screenshot](/img/screenshot.png)
