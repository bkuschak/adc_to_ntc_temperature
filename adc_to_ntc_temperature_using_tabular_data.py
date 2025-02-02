# Generate a lookup table to convert ratiometric ADC values directly to
# temperature. For use with NTC thermistor voltage divider, where ADC VREF
# is applied across the voltage divider. The NTC thermistor may be located
# on either the top side or bottom side of the divider.
#
# The lookup table is constructed from list of manufacturer-specified
# temperature and resistance values. These are provided in a space-delimited
# text file, with each line consisting of one temperature and one resistance.
# Temperature is in deg C and resistance in ohms. See the data in the example
# tabular_data_example.txt: 
#
#     -40 205200.0
#     -35 154800.0
#     -30 117900.0
#     ...
#
# The resulting code is fast, using one integer multiply and some additions and
# bit shifts.
#
# Adapted from https://www.sebulli.com/ntc/index.php

import argparse
import numpy as np
from scipy import interpolate
from scipy.optimize import curve_fit

class ntc_lookup_table:

    # Manufacturer temperatures / resistances are equal length lists of 
    # resistance vs temperature, provided by the manufacturer.
    # Other resistance is the other resistor in the voltage divider.
    def __init__(self, adc_bits, table_bits, temperature_resolution, 
                 manufacturer_temperatures, manufacturer_resistances, 
                 other_resistance, thermistor_on_top=False,
                 interpolation='piecewise-cubic', steinhart=None):
        if other_resistance <= 0:
            raise ValueError("other_resistance must be > 0")
        if temperature_resolution <= 0:
            raise ValueError("temperature_resolution must be > 0")
        if adc_bits < table_bits:
            raise ValueError("table_bits must be <= adc_bits")
        if interpolation != 'piecewise-cubic' and interpolation != 'steinhart':
            raise ValueError("Invalid interpolation method")
        if steinhart != None and steinhart != 3 and steinhart != 4:
            raise ValueError("steinhart method must be 3 or 4")

        self.adc_bits = adc_bits
        self.table_bits = table_bits
        self.temperature_resolution = temperature_resolution
        self.manufacturer_temperatures = manufacturer_temperatures
        self.manufacturer_resistances = manufacturer_resistances
        self.other_resistance = other_resistance
        self.thermistor_on_top = thermistor_on_top
        self.table = None
        self.interpolation = interpolation
        self.steinhart_parameters = None
        self.steinhart_covariance = None
        self.func = None
        self.func_params = None
        self.covariance = None
        if steinhart == 3:
            self.steinhart_hart = self.steinhart_hart3
        elif steinhart == 4:
            self.steinhart_hart = self.steinhart_hart4

    @staticmethod
    def read_input_file(input_filename):
        temperatures = []
        resistances = []
        with open(input_filename, "r") as f:
            for i,line in enumerate(f, start=1):
                line = line.strip()
                if len(line) == 0 or line[0] == '#':
                    continue
                fields = line.split()
                try:
                    temperatures.append(float(fields[0]))
                    resistances.append(float(fields[1]))
                except Exception as e:
                    print('Failed to read line {}: {}'.format(i, line))
                    raise e
        return temperatures, resistances

    # Given a divider ratio and the high-side resistance value, return the
    # low-side resistance value.
    def low_side_resistance(self, divider_ratio, high_side_resistance):
        if divider_ratio < 0 or divider_ratio >= 1:
            raise ValueError("divider_ratio out of range (0 to 1)")
        if high_side_resistance < 0:
            raise ValueError("high_side_resistance must be >= 0")
        return high_side_resistance * divider_ratio / (1 - divider_ratio)

    # Given a divider ratio and the low-side resistance value, return the
    # high-side resistance value.
    def high_side_resistance(self, divider_ratio, low_side_resistance):
        if divider_ratio <= 0 or divider_ratio > 1:
            raise ValueError("divider_ratio out of range (0 to 1)")
        if low_side_resistance < 0:
            raise ValueError("low_side_resistance must be >= 0")
        return low_side_resistance * (1 - divider_ratio) / divider_ratio

    def resistance_to_temperature(self, resistance):
        if resistance <= 0:
            raise ValueError("resistance must be > 0")
        temp = self.compute_temperature(resistance)
        return temp

    # Curve-fit the manufacturer-provided data: temperature as a function of
    # resistance. Piecewise cubic interpolation, passes through each data point
    # exactly. Requires SciPy 0.17.0 or newer.
    def cubic_fit_manufacturer_data(self):
        func = interpolate.interp1d(self.manufacturer_resistances,
                                    self.manufacturer_temperatures,
                                    kind='cubic', fill_value='extrapolate') 
        return func

    # Curve-fit the manufacturer-provided data: temperature as a function of
    # resistance. Single curve approximation using either 3 or 4 parameter
    # Steinhart-Hart equation.
    def steinhart_hart_fit_manufacturer_data(self):
        if self.steinhart_hart == self.steinhart_hart3:
            initial_values = [1e-3, 1e-3, 1e-3]
        else:
            initial_values = [1e-3, 1e-3, 1e-3, 1e-3]
        kelvin = np.array(self.manufacturer_temperatures) + 273.15
        parameters, cov = curve_fit(self.steinhart_hart,
                                    self.manufacturer_resistances,
                                    kelvin,
                                    p0=initial_values)
        self.steinhart_parameters = parameters
        self.steinhart_covariance = cov
        return parameters, cov

    # The three-parameter version of the S.H. equation. Returns temperature as
    # a function of resistance.
    @staticmethod
    def steinhart_hart3(r, a, b, c):
        return 1.0 / (a + b*np.log(r) + c*(np.log(r)**3))

    # The four-parameter version of the S.H. equation. Returns temperature as
    # a function of resistance.
    @staticmethod
    def steinhart_hart4(r, a0, a1, a2, a3):
        return 1.0 / (a0 + a1*np.log(r) + a2*(np.log(r)**2) +
                      a3*(np.log(r)**3))

    # Return the S.H. coefficients, or None if not using Steinhart-Hart.
    def get_steinhart_hart_coefficients(self):
        return self.steinhart_parameters, self.steinhart_covariance

    # Perform the curve fitting of the manufacturer data.
    def interpolate_manufacturer_data(self):
        if self.interpolation == 'piecewise-cubic':
            self.func = self.cubic_fit_manufacturer_data()
            self.func_params = None
            self.covariance = None
        elif self.interpolation == 'steinhart':
            params, cov = self.steinhart_hart_fit_manufacturer_data()
            self.func = self.steinhart_hart
            self.func_params = params
            self.covariance = cov

    # Compute the temperature, using the selected interpolation method.
    def compute_temperature(self, resistance):
        if self.func_params is not None:
            return self.func(resistance, *self.func_params) - 273.15
        else:
            return self.func(resistance)

    # Calculate the thermistor resistance, then temperature.
    def calc_temp_c(self, divider_ratio):
        if self.thermistor_on_top:
            thermistor_r = self.high_side_resistance(divider_ratio,
                                                     self.other_resistance)
        else:
            thermistor_r = self.low_side_resistance(divider_ratio,
                                                    self.other_resistance)
        # Given the resistance, calculate the temperature.
        temp_c = self.resistance_to_temperature(thermistor_r)
        temp_c /= self.temperature_resolution
        temp_c = int(temp_c)
        return temp_c

    # Table size will be (2^num_bits) + 1, usually a subset of the ADC range.
    # The MSBs of the ADC value are used as an index into the table.
    # Temperature resolution is typically 0.1 or 0.01, or 0.001, and affects
    # the size of the integers in the table.  

    def generate_table(self):
        # Perform the curve fitting.
        self.interpolate_manufacturer_data()

        self.table_len = 2**self.table_bits + 1
        self.table = [None] * self.table_len

        # Calculate the table, excluding the first and last entries.
        for i in range(1, len(self.table)-1):
            # ADC is ratiometric, so the divider ratio is equal to the
            # normalized ADC value.
            divider_ratio = float(i) / 2**self.table_bits
            self.table[i] = self.calc_temp_c(divider_ratio)

        # The first and last entries will not be valid since they correspond to
        # a divider ratio of 0 and infinity, clearly not valid temperatures.
        # Just extrapolate the first and last entries, using the same slope as
        # the adjacent points. This won't be accurate, but we never expect to
        # see temperatures in these ranges anyway.
        self.table[0] = self.table[1] - (self.table[2] - self.table[1])
        self.table[-1] = self.table[-2] - (self.table[-3] - self.table[-2])
        return self.table

    def int_type(self, val_min, val_max):
        if(val_min >= -2**7 and val_max < 2**7):
            int_type = 'int8_t'
        elif(val_min >= -2**15 and val_max < 2**15):
            int_type = 'int16_t'
        elif(val_min >= -2**31 and val_max < 2**31):
            int_type = 'int32_t'
        elif(val_min >= -2**63 and val_max < 2**63):
            int_type = 'int64_t'
        else:
            raise ValueError("Value(s) out of range.")
        return int_type

    def uint_type(self, val_max):
        if(val_max < 2**8):
            uint_type = 'uint8_t'
        elif(val_max < 2**16):
            uint_type = 'uint16_t'
        elif(val_max < 2**32):
            uint_type = 'uint32_t'
        elif(val_max < 2**64):
            uint_type = 'uint64_t'
        else:
            raise ValueError("Value out of range.")
        return uint_type

    # Generate a table for inclusion in C code.
    def generate_c_code(self):
        if self.table == None:
            raise ValueError("Table must be generated first!");

        coef_str = ''
        fit_str = self.interpolation
        if fit_str == 'steinhart':
            coef,cov = self.get_steinhart_hart_coefficients()
            if len(coef) == 3:
                fit_str = '3 parameter Steinhart-Hart'
                coef_str = '\n *   A: {:e}' \
                           '\n *   B: {:e}' \
                           '\n *   C: {:e}'.  \
                           format(coef[0], coef[1], coef[2])
            else:
                fit_str = '4 parameter Steinhart-Hart'
                coef_str = ''
                for i, c in enumerate(coef):
                    coef_str += '\n *   A{}: {:e}'.format(i, c)
                    #if(i < len(coef)-1):
                        #coef_str += '\n'

        # Determine the integer sizes.
        ttype = self.int_type(min(self.table), max(self.table))
        adc_type = self.uint_type(2**self.adc_bits-1)
        side = 'top' if self.thermistor_on_top else 'bottom'
        str = \
"""
#include <stdint.h>

/* ADC to temperature lookup table.
 * github.com/bkuschak/adc_to_ntc_temperature
 * Adapted from https://www.sebulli.com/ntc/index.php
 *
 * Table derived from manfacturer-provided temperature/resistance data which is
 * interpolated to fit a {} curve.{}
 *
 * NTC thermistor location: {} side of the voltage divider.
 * {} ohm resistor on opposite side of the voltage divider.
 * Input: {} MSBs of the ADC value.
 * Output: Temperature in units of {} deg C.
 * LSBs of ADC value should be used to interpolate between the nearest points.
 */
""".format(fit_str, coef_str, side, int(self.other_resistance),
           self.table_bits, self.temperature_resolution)

        str += 'const {} ntc_table[{}] = {{\n'.format(ttype, len(self.table))
        i = 0
        line = '    '
        while i < len(self.table):
            val = "{}".format(self.table[i])
            if i != len(self.table)-1:
                val += ", "

            if len(line) + len(val) < 80:
                line += val;
            else:
                str += line + '\n'
                line = '    ' + val
            i += 1

        str += line
        str += '\n};'

        # Add the code to perform the interpolation.
        adc_mask = '{:X}'.format(2**self.adc_bits - 1)
        shift = self.adc_bits - self.table_bits
        mask = '{:X}'.format(2**shift - 1)

        if self.thermistor_on_top:
            interp = "return p1 + (((p2-p1) * (adc_value & 0x{}))>>{});". \
                     format(mask, shift)
        else:
            interp = "return p1 - (((p1-p2) * (adc_value & 0x{}))>>{});". \
                     format(mask, shift)

        str += '\n'
        str += \
"""
/*
 * Convert an ADC value into a temperature value.
 * The ADC value must be a ratiometric measurement of the NTC voltage divider.
 *
 * p1 and p2 are the interpolating points just before and after the ADC value.
 * The function interpolates between these two points. The resulting code is
 * very small and fast. Only one integer multiplication is used.
 *
 * adc_value: the ADC measurement, {} bits full scale, right justified.
 * Returns the temperature in units of {} °C
 *
 */
{} adc_to_temperature({} adc_value) 
{{
  adc_value &= 0x{};

  /* Estimate the interpolating point before and after the ADC value. */
  {} p1 = ntc_table[ (adc_value >> {})  ];
  {} p2 = ntc_table[ (adc_value >> {})+1];

  /* Interpolate between both points. */
  {}
}}
""".format(self.adc_bits, self.temperature_resolution, ttype, adc_type,
           adc_mask, ttype, shift, ttype, shift, interp)
        return str

if __name__ == "__main__":
    description = \
"""
Generate a lookup table to convert ratiometric ADC values directly to
temperature. For use with NTC thermistor voltage divider, where ADC VREF is
applied across the voltage divider. The NTC thermistor may be located on either
the top side or bottom side of the divider.

The lookup table is constructed from list of manufacturer-specified temperature
and resistance values. These are provided in a space-delimited text file, with
each line consisting of one temperature and one resistance. Temperature is in
deg C and resistance in ohms. See the data in the example
tabular_data_example.txt. The data is fit to a 3 or 4 parameter Steinhart-Hart
model or a piecewise cubic. Then it is interpolated to create the lookup table.

The resulting C code is fast, using one integer multiply and some additions and
bit shifts.

Adapted from https://www.sebulli.com/ntc/index.php
"""
    ap = argparse.ArgumentParser(epilog=description)
    ap.add_argument('--adc_bits', help='Number of bits of ADC resolution.',
                    type=int, required=True, dest='adc_bits')
    ap.add_argument('--table_bits', help='Number of bits. Table len = '
                    '2^TABLE_BITS + 1.', type=int, required=True, 
                    dest='table_bits')
    ap.add_argument('--resolution', help='Temperature resolution (C). '
                    'Typically 0.01.', type=float, required=True,
                    dest='resolution', metavar='DEGREES')
    ap.add_argument('-f', help='Input file providing temperature and '
                    'resistance' 'in tabular format.', type=str, required=True,
                    metavar='FILE', dest='input')
    ap.add_argument('-r', help='Other resistor value (ohms).', type=float,
                    required=True, metavar='OHMS', dest='other_resistance')
    ap.add_argument('-o', '--output', help='Output file to write.',
                    dest='output', metavar='OUTPUT')
    ap.add_argument('--plot', help='Create plot.', dest='plot', 
                    action='store_true')
    ap.add_argument('--steinhart', help='Calculate the Steinhart-Hart '
                    'coefficients using 3 or 4 parameters.', type=int,
                    choices={3, 4}, metavar='SH', dest='steinhart')

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('-t', '--top', help='Thermistor on top-side of voltage '
                       'divider.', action='store_true', dest='top')
    group.add_argument('-b', '--bottom', help='Thermistor on bottom-side of '
                       'voltage divider.', action='store_true', dest='bottom')

    opts = ap.parse_args()

    if opts.steinhart:
        interpolation = 'steinhart'
    else:
        interpolation = 'piecewise-cubic'

    temperatures, resistances = ntc_lookup_table.read_input_file(opts.input)

    ntc = ntc_lookup_table(opts.adc_bits, opts.table_bits, opts.resolution,
                           temperatures, resistances, opts.other_resistance,
                           opts.top, interpolation, opts.steinhart)
    lookup_table = ntc.generate_table()
    c_code = ntc.generate_c_code()

    if opts.steinhart:
        params, cov = ntc.get_steinhart_hart_coefficients()
        print('Steinhart-Hart coefficients:')
        if len(params) == 3:
            print('  A = {:e}\n  B = {:e}\n  C = {:e}'.
                  format(params[0], params[1], params[2]))
        else:
            for i, a in enumerate(params):
                print('  a[{}] = {:e}'.format(i, a))
        print('  Standard deviation of the curve fit: {}'.format(np.std(cov)))
        test_resistance = 10e3
        print('  Temperature at {} ohms: {:.6f} deg C'.format(test_resistance,
              ntc.steinhart_hart(test_resistance, *params) - 273.15))

    if opts.output:
        with open(opts.output, "w") as f:
            f.write(c_code)
    else:
        print(c_code)

    if opts.plot:
        import matplotlib.pyplot as plt

        # Plot input data temperature vs resistance.
        fig, ax = plt.subplots(2)
        ax[0].plot(resistances, temperatures, 'b', marker='o',
                   label='Manufacturer data')
        ax[0].set_xlabel('Resistance (ohms)')
        ax[0].set_ylabel('Temperature (°C)')
        fig.suptitle('ADC to NTC temperature lookup table\nTable len: {}, '
                     'Temperature range: {} to {} °C'.format(len(lookup_table),
                     min(temperatures), max(temperatures)))
        ax[0].legend()
        ax[0].grid()

        # Plot the generated table. Indicate those temperatures that fall
        # outside the range of temperatures provided by the input data. These
        # will have reduced accuracy.
        table = np.array(lookup_table) * opts.resolution
        table_idx = np.array(range(len(table)))
        mask = np.array([True if t >= min(temperatures) and t <=
                        max(temperatures) else False for t in table])
        ax[1].plot(table_idx, table, 'b--', label='Reduced accuracy')
        ax[1].plot(table_idx[mask], table[mask], 'b-', label='Lookup table')
        ax[1].plot(table_idx[mask][0], table[mask][0], 'b', marker='o')
        ax[1].plot(table_idx[mask][-1], table[mask][-1], 'b', marker='o')
        ax[1].set_xlabel('The {} MSBs of the ADC value'.format(
            opts.table_bits))
        ax[1].set_ylabel('Temperature (°C)')
        ax[1].set_xlim(0, 2**opts.table_bits-1)
        ax[1].set_ylim(min(temperatures)-40, max(temperatures)+40)
        major_ticks = np.linspace(0, 2**opts.table_bits, 9)
        ax[1].set_xticks(major_ticks)
        ax[1].grid()
        h, l = ax[1].get_legend_handles_labels()
        ax[1].legend(h[::-1], l[::-1])
        fig.tight_layout()
        plt.show()

    exit(0)
